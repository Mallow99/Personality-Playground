import asyncio
import json
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from bfi.backends import BackendError, MockBackend, OpenAIBackend
from bfi.config import ROOT, Character, Settings
from bfi.store import Store
from bfi.tools import ToolError, ToolRunner


class MessageInput(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    project_tools: bool = False
    web_search: bool = False


class ConversationInput(BaseModel):
    profile_id: str = Field(default="companion", max_length=40)


class ToolInput(BaseModel):
    name: str = Field(max_length=60)
    arguments: dict = Field(default_factory=dict)


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
    profiles = {"companion": (character, settings)}
    for entry in json.loads(settings.profiles_file.read_text(encoding="utf-8")):
        profile = Character.model_validate(entry)
        if profile.profile_id not in {"academic", "engineering", "business"}:
            raise ValueError("Profile IDs must be academic, engineering, or business.")
        if profile.profile_id in profiles:
            raise ValueError("Duplicate profile ID.")
        profiles[profile.profile_id] = (profile, settings.for_profile(profile.profile_id))
    store = Store(settings.data_dir / "conversations.sqlite3")
    backends = {
        pid: backend or (MockBackend() if route.backend == "mock" else OpenAIBackend(route))
        for pid, (_, route) in profiles.items()
    }
    tools = ToolRunner(settings)
    app = FastAPI(title="Best Friend Initiative", version="0.1.0", docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])
    generation_lock = asyncio.Lock()

    @app.middleware("http")
    async def local_browser_boundary(request: Request, call_next):
        if request.method in {"POST", "DELETE", "PUT", "PATCH"}:
            origin = request.headers.get("origin")
            if origin and origin != str(request.base_url).rstrip("/"):
                return JSONResponse(
                    {"detail": "Use the app from its own local browser address."}, 403
                )
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

    def get_profile(profile_id):
        if profile_id not in profiles:
            raise HTTPException(404, "Character profile not found.")
        return profiles[profile_id]

    @app.get("/api/config")
    async def config():
        return {
            **settings.identity,
            "character": character.model_dump(),
            "cloud_delegation": "disabled",
            "history_pairs": settings.history_pairs,
            "context_chars": settings.context_chars,
            "profiles": [
                {
                    "id": pid,
                    "character": char.model_dump(),
                    **route.identity,
                    "adapter_label": route.adapter_label,
                    "adapter_verified": False,
                }
                for pid, (char, route) in profiles.items()
                if pid != "companion"
            ],
            "tools": tools.capabilities(),
        }

    @app.get("/api/status")
    async def status(profile_id: str = "companion"):
        _, route = get_profile(profile_id)
        return {
            **route.identity,
            **await backends[profile_id].status(),
            "cloud_delegation": "disabled",
            "adapter_label": route.adapter_label,
            "adapter_verified": False,
        }

    @app.get("/api/conversations")
    def conversations():
        return store.list()

    @app.post("/api/conversations", status_code=201)
    def new_conversation(payload: ConversationInput | None = None):
        char, route = get_profile(payload.profile_id if payload else "companion")
        return store.create(char.model_dump(), route.identity)

    @app.post("/api/tools/inspect")
    async def inspect_tool(payload: ToolInput):
        allowed = {d["function"]["name"] for d in tools.definitions(project=True, web=True)}
        try:
            return {
                "name": payload.name,
                "result": await tools.run(payload.name, payload.arguments, allowed),
            }
        except ToolError as exc:
            raise HTTPException(400, str(exc)) from exc

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
            profile_id = conversation["character"].get("profile_id", "companion")
            _, route = get_profile(profile_id)
            backend = backends[profile_id]
            if conversation["backend"] != route.identity:
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
            definitions = tools.definitions(project=message.project_tools, web=message.web_search)
            if (message.project_tools and not tools.capabilities()["project_files"]) or (
                message.web_search and not tools.capabilities()["web_search"]
            ):
                raise HTTPException(
                    400, "Requested tools are not configured. Open Tools for setup."
                )
            if definitions:
                if not hasattr(backend, "complete_with_tools"):
                    raise HTTPException(
                        400,
                        "The mock backend cannot choose tools. Use the Tools "
                        "inspector directly, or connect a tool-capable local model.",
                    )
                result = await backend.complete_with_tools(messages, definitions, tools)
            else:
                result = await backend.complete(messages)
            provenance = {
                **route.identity,
                "reported_model": result["reported_model"],
                "cloud_assistance": "none_by_app",
                "endpoint_locality": "mock" if route.backend == "mock" else "unverified_loopback",
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "usage": result["usage"],
                "context_messages_omitted": omitted,
                "profile_id": profile_id,
                "configured_adapter": route.adapter_label or None,
                "adapter_verified": False,
                "tool_steps": result.get("tool_steps", []),
                "generation_calls": result.get("generation_calls", 1),
            }
            return store.append_exchange(cid, content, result["content"], provenance)

    app.mount("/static", StaticFiles(directory=ROOT / "bfi/static"), name="static")

    @app.get("/")
    async def index():
        return FileResponse(ROOT / "bfi/static/index.html")

    @app.get("/concepts")
    async def concepts():
        return FileResponse(ROOT / "bfi/static/concepts.html")

    return app
