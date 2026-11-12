"""Memory/personality contracts. Model tests use simulated transports, not inference."""

import asyncio
import importlib
import json
import sqlite3
import time
from dataclasses import replace

import httpx
import httpx2
import pytest
from fastapi.testclient import TestClient

from bfi.backends import MockBackend
from bfi.config import Settings
from bfi.knowledge import Knowledge
from bfi.main import create_app
from bfi.memory_sleep import ProposalAction, SleepSettings, Suggestion, langmem_review


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path / "data")


def remember(kb, text, scope="shared", **kwargs):
    return kb.remember(text, scope, "fact", "Scripted owner evidence", **kwargs)


def test_existing_memory_database_migrates_without_losing_content(tmp_path):
    path = tmp_path / "old.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE memories (id TEXT PRIMARY KEY, root_id TEXT, content TEXT, "
            "scope TEXT, kind TEXT, source TEXT, status TEXT, created_at TEXT, updated_at TEXT)"
        )
        db.execute(
            "INSERT INTO memories VALUES ('old','old','Owner studies astronomy',"
            "'academic','fact','Owner','current','2026-11-11','2026-11-11')"
        )
        db.execute("CREATE VIRTUAL TABLE memory_search USING fts5(id UNINDEXED, content)")
        db.execute("INSERT INTO memory_search VALUES ('old','Owner studies astronomy')")
    kb = Knowledge(path)
    assert kb.memory("old")["importance"] == 3
    assert kb.memory("old")["keywords"] == []
    assert kb.search_memories("astronomy", "academic")[0]["id"] == "old"
    assert kb.search_memories("astronomy", "business") == []


def test_exact_cleanup_preserves_scope_kind_case_and_supports_undo(settings):
    async def scenario():
        app = create_app(settings)
        kb, sleep = app.state.knowledge, app.state.memory_sleep
        originals = [remember(kb, "I like the US."), remember(kb, "I  like the US.")]
        remember(kb, "I like the US.", "academic")
        remember(kb, "I like the us.")
        kb.remember("I like the US.", "shared", "preference", "Owner")
        run = sleep.start()
        await sleep.task
        assert sleep.run_state(run["id"])["state"] == "completed"
        assert "real tool-capable model" in sleep.run_state(run["id"])["summary"]
        assert len(kb.memories()) == 4
        change = sleep.proposals()[0]
        assert {m["id"] for m in change["before_records"]} == {m["id"] for m in originals}
        assert change["state"] == "applied"
        after_id = change["after_id"]
        assert sleep.apply(change["id"])["id"] == after_id  # idempotent application
        sleep.undo(change["id"])
        assert len(kb.memories()) == 5
        assert kb.memory(after_id) is None
        assert len(kb.search_memories("US", "business")) == 4
        sleep.start()
        await sleep.task
        again = next(p for p in sleep.proposals() if p["state"] == "applied")
        assert again["id"] != change["id"]
        sleep.undo(again["id"])
        # Undo removes the consolidation link: forgetting one restored record keeps the other.
        kb.forget(originals[0]["id"])
        assert kb.memory(originals[1]["id"]) is not None
        assert sleep.proposals() == []

    asyncio.run(scenario())


def test_forget_removes_merged_family_and_pending_audit_copies(settings):
    async def scenario():
        app = create_app(settings)
        kb, sleep = app.state.knowledge, app.state.memory_sleep
        originals = [remember(kb, "privatehelicopter"), remember(kb, "privatehelicopter")]
        unrelated = remember(kb, "Keep this other memory")
        sleep.start()
        await sleep.task
        proposal = sleep.proposals()[0]
        assert kb.forget(originals[0]["id"])
        assert kb.memory(proposal["after_id"]) is None
        assert all(kb.memory(m["id"]) is None for m in originals)
        assert kb.memory(unrelated["id"])
        assert sleep.proposals() == []
        assert "privatehelicopter" not in json.dumps(sleep.export())
        assert kb.search_memories("privatehelicopter", "academic") == []
        with pytest.raises(KeyError):
            sleep.undo(proposal["id"])

    asyncio.run(scenario())


def test_conflict_is_flagged_in_recall_and_needs_explicit_resolution(settings):
    app = create_app(settings)
    kb, sleep = app.state.knowledge, app.state.memory_sleep
    before = [
        remember(kb, "My home is Paris", "academic"),
        remember(kb, "My home is Berlin", "academic"),
    ]
    pid = sleep.propose(
        "unit-review",
        Suggestion(
            action="conflict",
            source_ids=[m["id"] for m in before],
            reason="Two current home cities; no move date.",
        ),
        before,
    )
    assert len(kb.memories()) == 2
    assert "review_warning" in kb.search_memories("home", "academic")[0]
    assert "review_warning" in kb.memory_context("home", "academic", 4000)[0]
    assert kb.search_memories("home", "business") == []
    with pytest.raises(ValueError, match="Resolve a conflict"):
        sleep.apply(pid)
    result = sleep.apply(
        pid,
        ProposalAction(
            content="My current home is Berlin.", source="Owner clarified the move today"
        ),
    )
    assert result["source"] == "Owner clarified the move today"
    assert len(kb.memories()) == 1
    assert "review_warning" not in kb.search_memories("home", "academic")[0]
    sleep.undo(pid)
    assert len(kb.memories()) == 2


@pytest.mark.parametrize("invalid", ["unknown", "cross_scope", "repeated", "false_enrichment"])
def test_model_proposals_cannot_escape_snapshot_or_rewrite_under_enrichment(settings, invalid):
    app = create_app(settings)
    kb, sleep = app.state.knowledge, app.state.memory_sleep
    first = remember(kb, "An owner fact", "academic")
    second = remember(kb, "A private fact", "business")
    values = {
        "unknown": dict(action="correct", source_ids=["invented"], content="Invented"),
        "cross_scope": dict(
            action="merge", source_ids=[first["id"], second["id"]], content="Mixed"
        ),
        "repeated": dict(action="merge", source_ids=[first["id"], first["id"]], content="Same"),
        "false_enrichment": dict(action="enrich", source_ids=[first["id"]], content="New fact"),
    }
    with pytest.raises(ValueError):
        sleep.propose(
            "unit-review",
            Suggestion(reason="Invalid simulated proposal", **values[invalid]),
            [first, second],
        )
    assert len(kb.memories()) == 2
    assert sleep.proposals() == []


def test_stale_model_proposal_and_undo_cannot_overwrite_owner_corrections(settings):
    app = create_app(settings)
    kb, sleep = app.state.knowledge, app.state.memory_sleep
    record = remember(kb, "First version")
    pid = sleep.propose(
        "unit-review",
        Suggestion(
            action="correct",
            source_ids=[record["id"]],
            content="Clearer version",
            reason="Simulated wording proposal",
        ),
        [record],
    )
    corrected = kb.remember(
        "Owner corrected version", "shared", "fact", "Explicit correction", replaces=record["id"]
    )
    with pytest.raises(ValueError, match="changed or was forgotten"):
        sleep.apply(pid)
    second = sleep.propose(
        "unit-review",
        Suggestion(
            action="enrich",
            source_ids=[corrected["id"]],
            content=corrected["content"],
            keywords=["alternate"],
            reason="Alternate search term",
        ),
        [corrected],
    )
    enriched = sleep.apply(second)
    assert kb.search_memories("alternate", "academic")[0]["id"] == enriched["id"]
    kb.remember("An even newer correction", "shared", "fact", "Owner", replaces=enriched["id"])
    with pytest.raises(ValueError, match="newer work"):
        sleep.undo(second)


def test_recall_keywords_importance_and_duplicate_suppression(settings):
    app = create_app(settings)
    kb = app.state.knowledge
    high = remember(kb, "Use short explanations", importance=5, keywords=["concise", "brief"])
    for i in range(6):
        remember(kb, f"Routine event {i}", importance=1)
    remember(kb, "Use short explanations", importance=5)
    assert kb.search_memories("brief", "business")[0]["id"] == high["id"]
    context = kb.memory_context("unrelated topic", "business", 4000)
    assert sum(m["content"] == high["content"] for m in context) == 1
    assert any(m["content"] == high["content"] for m in context)
    assert sum(len(json.dumps(m, ensure_ascii=False)) for m in context) <= 4000


def test_langmem_integration_uses_real_library_against_simulated_openai_transport(monkeypatch):
    import openai

    # LangChain defines client subclasses at import time; patch factories after that.
    importlib.import_module("langchain_openai")

    requests = []
    record = {"id": "owner-record", "content": "I prefer concise explanations", "scope": "shared"}

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        assert request.url.host == "127.0.0.1"
        name = body["tools"][0]["function"]["name"]
        assert name == "ReviewBatch"
        assert "owner-record" in json.dumps(body["messages"])
        return httpx2.Response(
            200,
            json={
                "id": "simulated-review",
                "model": "fixture-model",
                "object": "chat.completion",
                "created": 0,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "review-call",
                                    "type": "function",
                                    "function": {
                                        "name": name,
                                        "arguments": json.dumps(
                                            {
                                                "proposals": [
                                                    {
                                                        "action": "enrich",
                                                        "source_ids": ["owner-record"],
                                                        "content": record["content"],
                                                        "keywords": ["brief"],
                                                        "reason": "Alternate wording for recall",
                                                    }
                                                ]
                                            }
                                        ),
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            },
        )

    transport = httpx2.MockTransport(respond)
    monkeypatch.setattr(
        openai, "DefaultHttpxClient", lambda **kw: httpx2.Client(transport=transport, **kw)
    )
    monkeypatch.setattr(
        openai,
        "DefaultAsyncHttpxClient",
        lambda **kw: httpx2.AsyncClient(transport=transport, **kw),
    )
    result = asyncio.run(
        langmem_review([record], Settings(backend="openai", model="fixture-model"))
    )
    assert len(requests) == 1
    assert result[0].action == "enrich"
    assert result[0].keywords == ["brief"]


def test_scope_specific_review_is_bounded_and_rotates_unreviewed_records(settings):
    async def scenario():
        app = create_app(replace(settings, backend="openai"), MockBackend())
        kb, sleep = app.state.knowledge, app.state.memory_sleep
        seen = []

        async def reviewer(records, route):
            seen.append((records, route))
            return []

        sleep.reviewer = reviewer
        sleep.configure(SleepSettings(max_records=2))
        for i in range(4):
            remember(kb, f"Private topic {i}", "engineering")
        sleep.start()
        await sleep.task
        sleep.start()
        await sleep.task
        assert len(seen) == 2
        assert len({m["id"] for batch, _ in seen for m in batch}) == 4
        assert all(m["scope"] == "engineering" for batch, _ in seen for m in batch)
        assert all(route.max_tokens == 2048 for _, route in seen)

    asyncio.run(scenario())


def test_chat_preempts_sleep_and_releases_the_same_generation_resource(settings):
    async def scenario():
        app = create_app(replace(settings, backend="openai"), MockBackend())
        kb, sleep = app.state.knowledge, app.state.memory_sleep
        remember(kb, "Review this saved fact")
        started, stopped = asyncio.Event(), asyncio.Event()

        async def review(records, route):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        sleep.reviewer = review
        run = sleep.start()
        await asyncio.wait_for(started.wait(), 2)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        ) as c:
            conversation = (
                await c.post("/api/conversations", json={"profile_id": "academic"})
            ).json()
            assert stopped.is_set()
            response = await c.post(
                f"/api/conversations/{conversation['id']}/messages",
                json={"content": "Chat takes priority"},
            )
            assert response.status_code == 200
            assert len(response.json()["messages"]) == 2
        assert sleep.run_state(run["id"])["state"] == "interrupted"
        assert not sleep.lock.locked()
        await app.state.jobs.shutdown()

    asyncio.run(scenario())


def test_forgetting_during_model_review_cannot_restore_the_forgotten_text(settings):
    async def scenario():
        app = create_app(replace(settings, backend="openai"), MockBackend())
        kb, sleep = app.state.knowledge, app.state.memory_sleep
        record = remember(kb, "Forgotten secretviolet")

        async def review(records, route):
            kb.forget(record["id"])
            return [
                Suggestion(
                    action="enrich",
                    source_ids=[record["id"]],
                    content=record["content"],
                    keywords=["violet"],
                    reason="Simulated late result",
                )
            ]

        sleep.reviewer = review
        run = sleep.start()
        await sleep.task
        assert sleep.run_state(run["id"])["state"] == "failed"
        assert kb.memories(history=True) == []
        assert "secretviolet" not in json.dumps(sleep.export())

    asyncio.run(scenario())


def test_idle_scheduler_obeys_idle_interval_disable_and_pending_chat(settings):
    async def scenario():
        app = create_app(settings)
        kb, sleep = app.state.knowledge, app.state.memory_sleep
        remember(kb, "Some saved fact")
        await sleep.tick()
        assert sleep.runs() == []
        sleep.last_activity = time.monotonic() - 1000
        sleep.has_pending = lambda: True
        await sleep.tick()
        assert sleep.runs() == []
        sleep.has_pending = lambda: False
        await sleep.tick()
        await sleep.task
        assert len(sleep.runs()) == 1
        await sleep.tick()
        assert len(sleep.runs()) == 1
        sleep.configure(SleepSettings(enabled=False))
        sleep.last_activity = sleep.last_attempt = -10000
        await sleep.tick()
        assert len(sleep.runs()) == 1

    asyncio.run(scenario())


def test_personalities_persist_preview_save_restore_and_pin_existing_chats(settings):
    with TestClient(create_app(settings), base_url="http://localhost") as c:
        initial = c.get("/api/personalities").json()
        assert {p["profile"] for p in initial} == {"academic", "engineering", "business"}
        assert all(not p["trained_weights"] for p in initial)
        academic = next(p for p in initial if p["profile"] == "academic")
        old_chat = c.post("/api/conversations", json={"profile_id": "academic"}).json()
        changed = {**academic["settings"], "tone": "A unique thoughtful starlight voice"}
        preview = c.post("/api/personalities/academic/preview", json=changed)
        assert "starlight" in preview.json()["compiled_prompt"]
        assert c.get("/api/personalities").json()[0]["revision"] == 1
        saved = c.put(
            "/api/personalities/academic", json={"settings": changed, "expected_revision": 1}
        )
        assert saved.status_code == 200
        assert saved.json()["revision"] == 2
        new_chat = c.post("/api/conversations", json={"profile_id": "academic"}).json()
        assert "starlight" in new_chat["character"]["system_prompt"]
        assert "starlight" not in old_chat["character"]["system_prompt"]
        assert (
            c.get(f"/api/conversations/{old_chat['id']}").json()["character"]
            == old_chat["character"]
        )
        engineering = c.post("/api/conversations", json={"profile_id": "engineering"}).json()
        assert "starlight" not in engineering["character"]["system_prompt"]
        reply = c.post(f"/api/conversations/{new_chat['id']}/messages", json={"content": "Hi"})
        assert reply.json()["messages"][-1]["provenance"]["personality_revision"] == 2
        assert (
            c.put(
                "/api/personalities/academic", json={"settings": changed, "expected_revision": 1}
            ).status_code
            == 409
        )
        restored = c.post(
            "/api/personalities/academic/restore", json={"revision": 1, "expected_revision": 2}
        )
        assert restored.json()["revision"] == 3
        assert "starlight" not in restored.json()["compiled_prompt"]
        exported = c.get("/api/personalities/export").json()
        assert len(exported["profiles"][0]["versions"]) == 3
    with TestClient(create_app(settings), base_url="http://localhost") as c:
        assert c.get("/api/personalities").json()[0]["revision"] == 3


def test_owner_apis_validate_settings_keep_sleep_configuration_and_reject_stale_edits(settings):
    with TestClient(create_app(settings), base_url="http://localhost") as c:
        assert c.get("/personalities").status_code == 200
        assert c.put("/api/memory/sleep/settings", json={"idle_minutes": 0}).status_code == 422
        assert c.put("/api/memory/sleep/settings", json={"enabled": False}).status_code == 200
        assert (
            c.post(
                "/api/memory", json={"content": "Bad priority", "source": "Test", "importance": 6}
            ).status_code
            == 422
        )
        p = c.get("/api/personalities").json()[0]
        assert (
            c.put(
                "/api/personalities/unknown",
                json={"settings": p["settings"], "expected_revision": 1},
            ).status_code
            == 404
        )
        assert (
            c.post(
                "/api/personalities/academic/preview", json={**p["settings"], "traits": ["x"] * 9}
            ).status_code
            == 422
        )
        assert (
            c.put(
                "/api/personalities/academic",
                headers={"Origin": "http://elsewhere.test"},
                json={"settings": p["settings"], "expected_revision": 1},
            ).status_code
            == 403
        )
    with TestClient(create_app(settings), base_url="http://localhost") as c:
        assert c.get("/api/memory/sleep").json()["settings"]["enabled"] is False


def test_personality_prompt_revision_survives_later_base_profile_changes(settings, tmp_path):
    first = create_app(settings).state.personalities.get("academic")
    profiles = json.loads(settings.profiles_file.read_text())
    profiles[0]["system_prompt"] += "\nA newly edited base instruction."
    revised_file = tmp_path / "profiles.json"
    revised_file.write_text(json.dumps(profiles))
    app = create_app(replace(settings, profiles_file=revised_file))
    current = app.state.personalities.get("academic")
    assert current["compiled_prompt"] == first["compiled_prompt"]
    from bfi.personality import PersonalitySettings

    saved = app.state.personalities.save(
        "academic", PersonalitySettings.model_validate(current["settings"]), expected_revision=1
    )
    assert "newly edited base instruction" in saved["compiled_prompt"]
    assert app.state.personalities.get("academic", 1)["compiled_prompt"] == first["compiled_prompt"]


def test_unfinished_sleep_is_interrupted_on_restart_without_replay(settings):
    app = create_app(settings)
    with app.state.knowledge.connect() as db:
        db.execute(
            "INSERT INTO sleep_runs VALUES "
            "('unfinished','running','2026-11-12','2026-11-12','In progress',1)"
        )
    restarted = create_app(settings)
    run = restarted.state.memory_sleep.run_state("unfinished")
    assert run["state"] == "interrupted"
    assert "not replayed" in run["summary"]
    assert restarted.state.memory_sleep.task is None
