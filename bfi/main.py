import asyncio
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from bfi.backends import BackendError, MockBackend, OpenAIBackend
from bfi.config import ROOT, Character, Settings
from bfi.store import Store


class MessageInput(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


def context_for(conversation, content, settings):
    """Send recent complete pairs; the full transcript remains in SQLite."""
    prompt = conversation["character"]["system_prompt"]
    budget = settings.context_chars - len(prompt) - len(content)
    selected = []
    history = conversation["messages"]
    for end in range(len(history), max(0, len(history) - settings.history_pairs * 2), -2):
        pair = history[end - 2 : end]
        cost = sum(len(m["content"]) for m in pair)
        if cost > budget:
            break
        selected = [{"role": m["role"], "content": m["content"]} for m in pair] + selected
        budget -= cost
    return (
        [{"role": "system", "content": prompt}] + selected + [{"role": "user", "content": content}],
        len(history) - len(selected),
    )


def create_app(settings=None, backend=None):
    if settings is None:
        load_dotenv(ROOT / ".env")
        settings = Settings.from_env()
    character = Character.model_validate_json(settings.character_file.read_text(encoding="utf-8"))
    store = Store(settings.data_dir / "conversations.sqlite3")
    backend = backend or (MockBackend() if settings.backend == "mock" else OpenAIBackend(settings))
    app = FastAPI(title="Best Friend Initiative", version="0.1.0", docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])
    generation_lock = asyncio.Lock()

    @app.middleware("http")
    async def local_request_boundary(request: Request, call_next):
        if request.method in {"POST", "DELETE", "PUT", "PATCH"}:
            origin = request.headers.get("origin")
            if origin and origin != str(request.base_url).rstrip("/"):
                return JSONResponse({"detail": "Use the local application address."}, 403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(BackendError)
    async def backend_error(request, exc):
        return JSONResponse({"detail": exc.message, "code": exc.code}, status_code=exc.status)

    def get_conversation(cid):
        conversation = store.get(cid)
        if conversation is None:
            raise HTTPException(404, "Conversation not found.")
        return conversation

    @app.get("/api/config")
    async def config():
        return {
            **settings.identity,
            "character": character.model_dump(),
            "cloud_delegation": "disabled",
            "history_pairs": settings.history_pairs,
            "context_chars": settings.context_chars,
        }

    @app.get("/api/status")
    async def status():
        return {**settings.identity, **await backend.status(), "cloud_delegation": "disabled"}

    @app.get("/api/conversations")
    def conversations():
        return store.list()

    @app.post("/api/conversations", status_code=201)
    def new_conversation():
        return store.create(character.model_dump(), settings.identity)

    @app.get("/api/conversations/{cid}")
    def conversation(cid: str):
        return get_conversation(cid)

    @app.delete("/api/conversations/{cid}", status_code=204)
    async def delete_conversation(cid: str):
        async with generation_lock:
            if not store.delete(cid):
                raise HTTPException(404, "Conversation not found.")

    @app.post("/api/conversations/{cid}/messages")
    async def send(cid: str, message: MessageInput):
        content = message.content.strip()
        if not content:
            raise HTTPException(422, "Write a message before sending.")
        # One generation at a time suits a single GPU and keeps transcript order deterministic.
        if generation_lock.locked():
            raise HTTPException(409, "A reply is already being generated. Wait and try again.")
        async with generation_lock:
            conversation = get_conversation(cid)
            if conversation["backend"] != settings.identity:
                raise HTTPException(
                    409,
                    "This conversation uses a different backend or model. "
                    "Start a new conversation to keep its history separate.",
                )
            messages, omitted = context_for(conversation, content, settings)
            if sum(len(m["content"]) for m in messages) > settings.context_chars:
                raise HTTPException(
                    422,
                    "The character prompt and message exceed BFI_CONTEXT_CHARS. "
                    "Shorten the message or raise that setting.",
                )
            started = time.perf_counter()
            result = await backend.complete(messages)
            provenance = {
                **settings.identity,
                "reported_model": result["reported_model"],
                "cloud_assistance": "none_by_app",
                "endpoint_locality": "mock"
                if settings.backend == "mock"
                else "unverified_loopback",
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "usage": result["usage"],
                "context_messages_omitted": omitted,
            }
            return store.append_exchange(cid, content, result["content"], provenance)

    return app
