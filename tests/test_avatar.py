import json

import httpx
import pytest
from fastapi.testclient import TestClient

from bfi.avatar import AvatarHub, AvatarTools
from bfi.backends import OpenAIBackend
from bfi.config import ROOT, Settings
from bfi.desktop import local_url
from bfi.main import create_app
from bfi.tools import ToolError, ToolRunner


def client(tmp_path, backend=None, mode="mock"):
    return TestClient(
        create_app(Settings(data_dir=tmp_path, backend=mode), backend), base_url="http://localhost"
    )


def test_catalog_has_all_128_local_art_assets():
    hub = AvatarHub()
    assert len(hub.poses) == 128
    assert sum(p["source"] == "generated-concept" for p in hub.poses.values()) == 54
    for p in hub.poses.values():
        assert p["src"].startswith("/static/")
        assert (ROOT / "bfi" / p["src"].lstrip("/")).is_file()
    assert all(p["id"].startswith("academic/") for p in hub.search("academic", "reading")["poses"])


@pytest.mark.parametrize(
    "changes",
    [
        {"pose_id": "https://evil.test/picture"},
        {"profile": []},
        {"profile": "unknown"},
        {"pose_id": []},
        {"caption": "x" * 401},
        {"visible": "yes"},
        {"dock": "center"},
        {"size": "huge"},
        {"javascript": "alert(1)"},
        {"profile": "academic", "pose_id": "business/standing"},
    ],
)
def test_avatar_rejects_unbounded_actions(tmp_path, changes):
    with client(tmp_path) as app:
        before = app.get("/api/avatar").json()
        assert app.post("/api/avatar", json=changes).status_code == 400
        assert app.get("/api/avatar").json() == before


def test_owner_actions_and_mock_lifecycle_are_not_mock_tool_calls(tmp_path):
    with client(tmp_path) as app:
        assert (
            app.post(
                "/api/avatar",
                json={
                    "profile": "business",
                    "pose_id": "business/B03",
                    "dock": "top-left",
                    "size": "small",
                },
            ).status_code
            == 200
        )
        cid = app.post("/api/conversations", json={"profile_id": "business"}).json()["id"]
        result = app.post(
            f"/api/conversations/{cid}/messages", json={"content": "Hello", "avatar_tools": True}
        )
        assert result.status_code == 200
        provenance = result.json()["messages"][-1]["provenance"]
        assert provenance["backend"] == "mock" and provenance["tool_steps"] == []
        state = app.get("/api/avatar").json()
        assert state["profile"] == "business" and state["speaking"]
        assert state["dock"] == "top-left"
        app.app.state.avatar.state["speech_until"] = 0
        assert not app.get("/api/avatar").json()["speaking"]
        switched = app.post("/api/avatar", json={"profile": "academic"}).json()
        assert switched["caption"] == "" and not switched["speaking"]
        assert app.get("/overlay").status_code == 200
        assert (
            app.post(
                "/api/avatar", json={"visible": False}, headers={"Origin": "https://elsewhere.test"}
            ).status_code
            == 403
        )


def test_model_avatar_calls_are_scoped_and_persisted(tmp_path):
    calls = []

    def server(request):
        payload = json.loads(request.content)
        calls.append(payload)
        if len(calls) == 1:
            assert {d["function"]["name"] for d in payload["tools"]} == {
                "avatar_catalog",
                "avatar_set",
            }
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "catalog",
                                        "function": {
                                            "name": "avatar_catalog",
                                            "arguments": '{"query":"reading","limit":3}',
                                        },
                                    },
                                    {
                                        "id": "cue",
                                        "function": {
                                            "name": "avatar_set",
                                            "arguments": (
                                                '{"pose_id":"academic/reading",'
                                                '"caption":"Let us read this."}'
                                            ),
                                        },
                                    },
                                ],
                            }
                        }
                    ]
                },
            )
        assert payload["messages"][-1]["role"] == "tool"
        assert json.loads(payload["messages"][-1]["content"])["pose_id"] == "academic/reading"
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "Here is the explanation."}}]}
        )

    settings = Settings(data_dir=tmp_path, backend="openai")
    with TestClient(
        create_app(settings, OpenAIBackend(settings, httpx.MockTransport(server))),
        base_url="http://localhost",
    ) as app:
        cid = app.post("/api/conversations", json={"profile_id": "academic"}).json()["id"]
        reply = app.post(
            f"/api/conversations/{cid}/messages",
            json={"content": "Explain this", "avatar_tools": True},
        )
        assert reply.status_code == 200, reply.text
        steps = reply.json()["messages"][-1]["provenance"]["tool_steps"]
        assert [s["name"] for s in steps] == ["avatar_catalog", "avatar_set"]
        state = app.get("/api/avatar").json()
        assert state["pose_id"] == "academic/reading" and state["speaking"]
        assert state["caption"] == "Here is the explanation."


def test_avatar_consent_does_not_add_tools_when_disabled(tmp_path):
    def server(request):
        assert "tools" not in json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "A normal reply."}}]})

    settings = Settings(data_dir=tmp_path, backend="openai")
    with client(
        tmp_path, OpenAIBackend(settings, httpx.MockTransport(server)), mode="openai"
    ) as app:
        cid = app.post("/api/conversations", json={"profile_id": "academic"}).json()["id"]
        assert (
            app.post(f"/api/conversations/{cid}/messages", json={"content": "Hello"}).status_code
            == 200
        )


@pytest.mark.parametrize("field,value", [("profile", "business"), ("motion", False)])
def test_handler_cannot_change_profile_or_owner_motion(field, value):
    import asyncio

    hub = AvatarHub()
    runner = AvatarTools(ToolRunner(Settings()), hub, "academic")
    with pytest.raises(ToolError):
        asyncio.run(runner.run("avatar_set", {field: value}, {"avatar_set"}))
    with pytest.raises(ToolError):
        asyncio.run(runner.run("avatar_set", {"pose_id": "business/standing"}, {"avatar_set"}))


def test_backend_failure_clears_speaking_and_thinking(tmp_path):
    settings = Settings(data_dir=tmp_path, backend="openai")
    adapter = OpenAIBackend(settings, httpx.MockTransport(lambda req: httpx.Response(503)))
    with client(tmp_path, adapter, mode="openai") as app:
        cid = app.post("/api/conversations", json={"profile_id": "engineering"}).json()["id"]
        assert (
            app.post(f"/api/conversations/{cid}/messages", json={"content": "Hello"}).status_code
            == 502
        )
        state = app.get("/api/avatar").json()
        assert state["activity"] == "error" and not state["speaking"]
        assert app.get(f"/api/conversations/{cid}").json()["messages"] == []


def test_desktop_url_is_loopback_only():
    import argparse

    assert local_url("http://127.0.0.1:8000/") == "http://127.0.0.1:8000"
    for value in [
        "https://example.com",
        "http://localhost/path",
        "http://user:secret@localhost",
        "file:///etc/passwd",
        "http://localhost?x=1",
    ]:
        with pytest.raises(argparse.ArgumentTypeError):
            local_url(value)


def test_thinking_state_remains_visible_and_owner_can_hide_during_generation(tmp_path):
    import asyncio

    from bfi.backends import MockBackend

    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()

        class Slow(MockBackend):
            async def complete(self, messages):
                entered.set()
                await release.wait()
                return await super().complete(messages)

        app = create_app(Settings(data_dir=tmp_path), Slow())
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        ) as browser:
            cid = (
                await browser.post("/api/conversations", json={"profile_id": "academic"})
            ).json()["id"]
            pending = asyncio.create_task(
                browser.post(f"/api/conversations/{cid}/messages", json={"content": "Explain this"})
            )
            await asyncio.wait_for(entered.wait(), 2)
            try:
                state = (await browser.get("/api/avatar")).json()
                assert state["activity"] == "thinking" and state["conversation_id"] == cid
                assert (
                    await browser.post("/api/avatar", json={"visible": False})
                ).status_code == 200
                assert (
                    await browser.post("/api/avatar", json={"profile": "business"})
                ).status_code == 409
            finally:
                release.set()
            assert (await pending).status_code == 200
            assert not (await browser.get("/api/avatar")).json()["visible"]

    asyncio.run(scenario())
