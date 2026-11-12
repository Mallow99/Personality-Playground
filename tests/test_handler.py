"""Handler contracts use scripted backends/transports; these are not inference benchmarks."""

import asyncio
import json
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from bfi.backends import BackendError, MockBackend, OpenAIBackend
from bfi.config import Settings
from bfi.knowledge import KnowledgeTools
from bfi.main import create_app
from bfi.tools import ToolError, ToolRunner


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path / "data")


def client(settings, backend=None):
    return TestClient(create_app(settings, backend), base_url="http://localhost")


def conversation(app, profile="academic"):
    return app.post("/api/conversations", json={"profile_id": profile}).json()["id"]


def memory(app, text, scope="shared"):
    response = app.post(
        "/api/memory",
        json={
            "content": text,
            "scope": scope,
            "source": "Owner statement in test",
            "kind": "decision",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_runtime_presets_activate_local_routes_and_keep_keys_server_side(settings, monkeypatch):
    monkeypatch.setenv("BFI_RUNTIME", "lmstudio")
    monkeypatch.delenv("BFI_BACKEND", raising=False)
    monkeypatch.delenv("BFI_BASE_URL", raising=False)
    route = Settings.from_env()
    assert route.backend == "openai"
    assert route.base_url == "http://127.0.0.1:1234/v1"
    monkeypatch.setenv("BFI_ENGINEERING_RUNTIME", "ollama")
    custom = settings.for_profile("engineering")
    assert custom.backend == "openai"
    assert custom.base_url == "http://127.0.0.1:11434/v1"
    with client(replace(settings, api_key="never-return-this")) as app:
        response = app.get("/api/handler")
        assert "never-return-this" not in response.text
        assert response.json()["queue"]["concurrent_generations"] == 1
        assert all(not p["inference_verified"] for p in response.json()["runtime_presets"])


@pytest.mark.parametrize(
    "changes",
    [
        {"temperature": -1},
        {"temperature": float("nan")},
        {"top_p": 0},
        {"top_p": 1.1},
        {"runtime": "unknown"},
        {"queue_limit": 0},
    ],
)
def test_invalid_tuning_is_rejected(settings, changes):
    with pytest.raises(ValueError):
        replace(settings, **changes)


def test_memory_correction_forgetting_and_restart_are_real_persistence(settings):
    with client(settings) as app:
        original = memory(app, "v5 is accepted")
        corrected = app.patch(
            f"/api/memory/{original['id']}",
            json={
                "content": "v5 is rejected",
                "scope": "shared",
                "kind": "decision",
                "source": "Later owner correction",
            },
        ).json()
        assert corrected["id"] != original["id"]
        assert len(app.get("/api/memory").json()) == 1
        exported = app.get("/api/memory/export").json()["records"]
        assert {r["status"] for r in exported} == {"current", "superseded"}
        assert (
            app.patch(
                f"/api/memory/{original['id']}",
                json={
                    "content": "conflicting edit",
                    "source": "stale form",
                },
            ).status_code
            == 409
        )
    with client(settings) as restarted:
        assert restarted.get("/api/memory").json()[0]["content"] == "v5 is rejected"
        assert restarted.delete(f"/api/memory/{corrected['id']}").status_code == 204
        assert restarted.get("/api/memory/export").json()["records"] == []


def test_model_context_obeys_character_scope_and_owner_toggle(settings):
    class Capture(MockBackend):
        async def complete(self, messages):
            self.seen = json.dumps(messages)
            return await super().complete(messages)

    backend = Capture()
    with client(settings, backend) as app:
        memory(app, "shared-unique-preference")
        private = memory(app, "engineering-private-unique", "engineering")
        academic = conversation(app, "academic")
        engineering = conversation(app, "engineering")
        response = app.post(f"/api/conversations/{academic}/messages", json={"content": "Hello"})
        assert "shared-unique-preference" in backend.seen
        assert "engineering-private-unique" not in backend.seen
        assert response.json()["messages"][-1]["provenance"]["memory_records"]
        app.post(f"/api/conversations/{engineering}/messages", json={"content": "Hello"})
        assert "engineering-private-unique" in backend.seen
        fresh = conversation(app, "academic")
        app.post(
            f"/api/conversations/{fresh}/messages", json={"content": "Hi", "use_memory": False}
        )
        assert "shared-unique-preference" not in backend.seen
        assert (
            app.patch(
                f"/api/memory/{private['id']}",
                json={
                    "content": "leak",
                    "scope": "shared",
                    "source": "wrong scope",
                },
            ).status_code
            == 400
        )


def test_model_memory_search_cannot_choose_another_scope(settings):
    app = create_app(settings)
    knowledge = app.state.knowledge
    knowledge.remember("private unicorn", "engineering", "fact", "owner")
    runner = KnowledgeTools(ToolRunner(settings), knowledge, "academic")
    result = asyncio.run(runner.run("memory_search", {"query": "unicorn"}, {"memory_search"}))
    assert result["records"] == []
    with pytest.raises(ToolError):
        asyncio.run(
            runner.run(
                "memory_search", {"query": "unicorn", "scope": "engineering"}, {"memory_search"}
            )
        )


def test_library_is_searchable_and_import_survives_restart(settings):
    with client(settings) as app:
        bundled_ids = {d["id"] for d in app.get("/api/research").json()["documents"]}
        assert {
            "full-stack-2026-11-11",
            "memory-2026-11-11",
            "source-catalog-2026-11-11",
        } <= bundled_ids
        result = app.get("/api/research", params={"q": "speculative quantization"}).json()
        assert result["results"]
        assert all(hit["source"] for hit in result["results"])
        for q in ['" OR * -', "') DROP TABLE documents; --", "💚"]:
            assert app.get("/api/research", params={"q": q}).status_code == 200
        doc = app.post(
            "/api/research",
            json={
                "title": "Weekend note",
                "category": "inference",
                "source": "Owner research note",
                "reviewed_at": "2026-11-11",
                "content": "uniqueheliotrope inference evidence",
            },
        ).json()
        assert (
            app.get("/api/research", params={"q": "uniqueheliotrope"}).json()["results"][0]["id"]
            == doc["id"]
        )
        exported_ids = {d["id"] for d in app.get("/api/research/export").json()["documents"]}
        assert exported_ids == bundled_ids | {doc["id"]}
    with client(settings) as restarted:
        saved = restarted.get(f"/api/research/{doc['id']}").json()
        assert saved["content"] == "uniqueheliotrope inference evidence"
        assert saved["sha256"] == doc["sha256"]


def test_research_tool_roundtrip_uses_library_and_retains_sources(settings):
    route = replace(settings, backend="openai")
    calls = []

    def server(request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1:
            assert "research_search" in {t["function"]["name"] for t in body["tools"]}
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "tool_calls": [
                                    {
                                        "id": "r1",
                                        "function": {
                                            "name": "research_search",
                                            "arguments": '{"query":"quantization"}',
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                },
            )
        result = json.loads(body["messages"][-1]["content"])
        assert result["results"][0]["source"]
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "Source-based reply"}}]}
        )

    with client(route, OpenAIBackend(route, httpx.MockTransport(server))) as app:
        cid = conversation(app)
        result = app.post(
            f"/api/conversations/{cid}/messages",
            json={
                "content": "Look up our quantization research",
                "research_tools": True,
            },
        )
        assert result.status_code == 200
        assert (
            result.json()["messages"][-1]["provenance"]["tool_steps"][0]["name"]
            == "research_search"
        )


def test_queue_serializes_jobs_supports_idempotency_and_cancels_waiting(settings):
    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()

        class Slow(MockBackend):
            calls = 0

            async def complete(self, messages):
                self.calls += 1
                started.set()
                await release.wait()
                return await super().complete(messages)

        backend = Slow()
        app = create_app(replace(settings, queue_limit=2), backend)
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://localhost"
            ) as c:
                cid = (await c.post("/api/conversations")).json()["id"]
                path = f"/api/conversations/{cid}/jobs"
                first = (await c.post(path, json={"content": "first", "request_id": "same"})).json()
                await asyncio.wait_for(started.wait(), 2)
                again = (await c.post(path, json={"content": "first", "request_id": "same"})).json()
                assert first["id"] == again["id"]
                assert (
                    await c.post(path, json={"content": "different", "request_id": "same"})
                ).status_code == 409
                second = (await c.post(path, json={"content": "second"})).json()
                assert second["state"] == "queued"
                assert (await c.post(path, json={"content": "third"})).status_code == 429
                cancelled = await c.post(f"/api/jobs/{second['id']}/cancel")
                assert cancelled.json()["state"] == "cancelled"
                release.set()
                await asyncio.gather(*list(app.state.jobs.tasks.values()))
                assert (await c.get(f"/api/jobs/{first['id']}")).json()["state"] == "succeeded"
                assert backend.calls == 1
                assert len((await c.get(f"/api/conversations/{cid}")).json()["messages"]) == 2
        finally:
            await app.state.jobs.shutdown()

    asyncio.run(scenario())


def test_cancel_running_job_releases_handler_and_never_saves_partial_pair(settings):
    async def scenario():
        started = asyncio.Event()

        class Slow(MockBackend):
            calls = 0

            async def complete(self, messages):
                self.calls += 1
                if self.calls == 1:
                    started.set()
                    await asyncio.Event().wait()
                return await super().complete(messages)

        app = create_app(settings, Slow())
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://localhost"
            ) as c:
                cid = (await c.post("/api/conversations", json={"profile_id": "academic"})).json()[
                    "id"
                ]
                path = f"/api/conversations/{cid}/jobs"
                job = (await c.post(path, json={"content": "cancel me"})).json()
                await asyncio.wait_for(started.wait(), 2)
                assert (await c.post(f"/api/jobs/{job['id']}/cancel")).json()[
                    "state"
                ] == "cancelled"
                assert (await c.get(f"/api/conversations/{cid}")).json()["messages"] == []
                assert not app.state.avatar.snapshot()["speaking"]
                next_job = (await c.post(path, json={"content": "next reply"})).json()
                await asyncio.gather(*list(app.state.jobs.tasks.values()))
                assert (await c.get(f"/api/jobs/{next_job['id']}")).json()["state"] == "succeeded"
                assert (await c.delete(f"/api/conversations/{cid}")).status_code == 204
                assert (await c.get(f"/api/jobs/{next_job['id']}")).status_code == 404
        finally:
            await app.state.jobs.shutdown()

    asyncio.run(scenario())


def test_shutdown_and_restart_mark_unfinished_jobs_without_replaying(settings):
    async def scenario():
        started = asyncio.Event()

        class Slow(MockBackend):
            async def complete(self, messages):
                started.set()
                await asyncio.Event().wait()

        app = create_app(settings, Slow())
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        ) as c:
            cid = (await c.post("/api/conversations")).json()["id"]
            job = (
                await c.post(f"/api/conversations/{cid}/jobs", json={"content": "unfinished"})
            ).json()
            await asyncio.wait_for(started.wait(), 2)
            await app.state.jobs.shutdown()
        restarted = create_app(settings)
        assert restarted.state.jobs.get(job["id"])["state"] == "interrupted"
        assert restarted.state.jobs.tasks == {}
        await restarted.state.jobs.shutdown()

    asyncio.run(scenario())


def test_streaming_reads_real_sse_chunks_and_commits_only_final_reply(settings):
    route = replace(settings, backend="openai", temperature=0.2, top_p=0.9)
    frames = [
        {"model": "test-stream", "choices": [{"delta": {"content": "Hello"}}]},
        {"choices": [{"delta": {"content": " there"}, "finish_reason": "stop"}]},
        {"choices": [], "usage": {"total_tokens": 12, "private_extra": "discard"}},
    ]

    def server(request):
        body = json.loads(request.content)
        assert body["stream"] is True
        assert body["temperature"] == 0.2 and body["top_p"] == 0.9
        text = "".join("data: " + json.dumps(f) + "\n\n" for f in frames) + "data: [DONE]\n\n"
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=text)

    chunks = []
    reply = asyncio.run(
        OpenAIBackend(route, httpx.MockTransport(server)).complete_stream(
            [{"role": "user", "content": "hello"}],
            chunks.append,
        )
    )
    assert chunks == ["Hello", " there"]
    assert reply == {
        "content": "Hello there",
        "reported_model": "test-stream",
        "usage": {"total_tokens": 12},
    }


@pytest.mark.parametrize(
    "text,content_type,code",
    [
        (
            'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n',
            "text/event-stream",
            "incomplete_stream",
        ),
        ("data: not-json\n\n", "text/event-stream", "invalid_stream"),
        ('data: {"error":"private server detail"}\n\n', "text/event-stream", "invalid_stream"),
        ('{"choices":[]}', "application/json", "stream_unsupported"),
    ],
)
def test_incomplete_or_invalid_streams_are_not_successful(settings, text, content_type, code):
    adapter = OpenAIBackend(
        settings,
        httpx.MockTransport(
            lambda r: httpx.Response(
                200,
                headers={"content-type": content_type},
                content=text,
            )
        ),
    )
    with pytest.raises(BackendError) as error:
        asyncio.run(adapter.complete_stream([], lambda t: None))
    assert error.value.code == code
    assert "private server detail" not in error.value.message
