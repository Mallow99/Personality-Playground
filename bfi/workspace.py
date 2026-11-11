"""Owner-facing setup, generation jobs, saved memory, and research library APIs."""

from datetime import date
from typing import Literal
from uuid import uuid4

from fastapi import HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from bfi.config import ROOT
from bfi.jobs import QueueFull
from bfi.runtimes import catalog

Scope = Literal["shared", "companion", "academic", "engineering", "business"]


class MessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=8000)
    project_tools: bool = False
    web_search: bool = False
    avatar_tools: bool = False
    use_memory: bool = True
    research_tools: bool = False
    stream_reply: bool = False


class JobInput(MessageInput):
    stream_reply: bool = True
    request_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,80}$")


class MemoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    content: str = Field(min_length=1, max_length=2000)
    scope: Scope = "shared"
    kind: Literal["fact", "preference", "decision", "experience"] = "fact"
    source: str = Field(min_length=1, max_length=1000)


class ResearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=80)
    source: str = Field(min_length=1, max_length=1500)
    content: str = Field(min_length=1, max_length=200000)
    reviewed_at: date


def install_workspace(app, settings, profiles, backends, knowledge, jobs, get_conversation):
    @app.get("/api/handler")
    async def handler():
        return {
            "runtime_presets": catalog(),
            "profiles": [
                {
                    "id": pid,
                    "name": char.name,
                    **route.identity,
                    "runtime": route.runtime,
                    "temperature": route.temperature,
                    "top_p": route.top_p,
                    "max_tokens": route.max_tokens,
                    "context_chars": route.context_chars,
                    "memory_chars": route.memory_chars,
                    "adapter_verified": False,
                }
                for pid, (char, route) in profiles.items()
            ],
            "queue": {
                "concurrent_generations": 1,
                "pending_limit": settings.queue_limit,
                "restart_policy": "interrupt_without_replay",
            },
            "memory": {
                "provider": "sqlite-owner-curated-v1",
                "automatic_writes": False,
                "character_scopes_enforced": True,
            },
            "research": {"provider": "sqlite-fts5-v1", "documents": len(knowledge.documents())},
            "services": {
                "voice": "not_connected",
                "media_generation": "not_connected",
                "training": "separate_experiment",
                "model_lifecycle": "external_runtime",
            },
            "verification": (
                "Configuration is not proof of inference, adapter loading or PC performance."
            ),
        }

    @app.get("/api/jobs")
    async def list_jobs(conversation_id: str | None = None):
        return jobs.list(conversation_id)

    @app.post("/api/conversations/{cid}/jobs", status_code=202)
    async def submit(cid: str, payload: JobInput):
        conversation = get_conversation(cid)
        profile = conversation["character"].get("profile_id", "companion")
        if profile not in profiles or conversation["backend"] != profiles[profile][1].identity:
            raise HTTPException(409, "This conversation's model changed. Start a new conversation.")
        if not payload.content.strip():
            raise HTTPException(422, "Write a message before sending.")
        try:
            return jobs.submit(cid, payload.model_dump(exclude={"request_id"}), payload.request_id)
        except QueueFull as exc:
            raise HTTPException(429, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/api/jobs/{jid}")
    async def job(jid: str):
        result = jobs.get(jid)
        if not result:
            raise HTTPException(404, "Generation job not found.")
        return result

    @app.post("/api/jobs/{jid}/cancel")
    async def cancel(jid: str):
        result = await jobs.cancel(jid)
        if not result:
            raise HTTPException(404, "Generation job not found.")
        return result

    @app.get("/api/memory")
    def memories(scope: Scope | None = None, history: bool = False):
        return knowledge.memories(scope, history)

    @app.post("/api/memory", status_code=201)
    def remember(payload: MemoryInput):
        return knowledge.remember(**payload.model_dump())

    @app.patch("/api/memory/{mid}")
    def correct(mid: str, payload: MemoryInput):
        try:
            return knowledge.remember(**payload.model_dump(), replaces=mid)
        except KeyError as exc:
            raise HTTPException(409, exc.args[0]) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.delete("/api/memory/{mid}", status_code=204)
    def forget(mid: str):
        if not knowledge.forget(mid):
            raise HTTPException(404, "Saved memory not found.")

    @app.get("/api/memory/export")
    def export_memories():
        return {
            "format": "bfi-owner-memory-v1",
            "records": knowledge.memories(history=True, limit=None),
            "forget_scope": "Saved memory and its corrections only. Past conversation text, "
            "tool traces and earlier exports/backups are separate records.",
        }

    @app.get("/api/research")
    def research(q: str = Query(default="", max_length=300), limit: int = Query(8, ge=1, le=20)):
        return {
            "documents": knowledge.documents(),
            "results": knowledge.search_documents(q, limit) if q.strip() else [],
            "query": q,
            "evidence": "Saved research, not verified PC measurements.",
        }

    @app.post("/api/research", status_code=201)
    def add_report(payload: ResearchInput):
        return knowledge.put_document(
            "saved-" + str(uuid4()),
            payload.title,
            payload.category,
            payload.source,
            payload.content,
            payload.reviewed_at.isoformat(),
        )

    @app.get("/api/research/export")
    def export_research():
        return {
            "format": "bfi-research-v1",
            "documents": [knowledge.document(doc["id"]) for doc in knowledge.documents()],
        }

    @app.get("/api/research/{did}")
    def report(did: str):
        document = knowledge.document(did)
        if not document:
            raise HTTPException(404, "Saved report not found.")
        return document

    @app.get("/handler")
    @app.get("/library")
    def workspace():
        return FileResponse(ROOT / "bfi/static/workspace.html")
