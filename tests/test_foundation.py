import asyncio
import json
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from bfi.backends import BackendError, MockBackend, OpenAIBackend
from bfi.config import Settings
from bfi.main import create_app


@pytest.fixture
def settings(tmp_path):
    character = tmp_path / "character.json"
    character.write_text(
        json.dumps(
            {
                "name": "Test Companion",
                "description": "Test character",
                "system_prompt": "A fixed test prompt.",
            }
        ),
        encoding="utf-8",
    )
    return Settings(data_dir=tmp_path / "data", character_file=character)


def client_for(settings, backend=None):
    return TestClient(create_app(settings, backend), base_url="http://localhost")


def new(client):
    response = client.post("/api/conversations")
    assert response.status_code == 201
    return response.json()["id"]


def send(client, cid, content="Hello"):
    return client.post(f"/api/conversations/{cid}/messages", json={"content": content})


def test_mock_is_explicit_and_transcript_survives_app_restart(settings):
    with client_for(settings) as client:
        assert client.get("/api/status").json()["state"] == "mock"
        cid = new(client)
        response = send(client, cid)
        assert response.status_code == 200
        conversation = response.json()
        assert [m["role"] for m in conversation["messages"]] == ["user", "assistant"]
        reply = conversation["messages"][-1]
        assert "no model inference" in reply["content"]
        assert reply["provenance"]["reported_model"] == "mock-script-v1"
        assert reply["provenance"]["cloud_assistance"] == "none_by_app"
        assert reply["provenance"]["endpoint"] is None
    with client_for(settings) as restarted:
        saved = restarted.get(f"/api/conversations/{cid}").json()
        assert saved == conversation


def test_character_is_snapshotted_per_conversation(settings):
    with client_for(settings) as client:
        cid = new(client)
    data = json.loads(settings.character_file.read_text())
    data["name"], data["system_prompt"] = "Changed", "Changed prompt"
    settings.character_file.write_text(json.dumps(data))
    with client_for(settings) as client:
        assert (
            client.get(f"/api/conversations/{cid}").json()["character"]["name"] == "Test Companion"
        )
        assert client.post("/api/conversations").json()["character"]["name"] == "Changed"


def test_failed_inference_keeps_database_unchanged(settings):
    class FailingBackend(MockBackend):
        async def complete(self, messages):
            raise BackendError("Server unavailable", "connection")

    with client_for(settings, FailingBackend()) as client:
        cid = new(client)
        response = send(client, cid)
        assert response.status_code == 502
        assert response.json()["code"] == "connection"
        assert client.get(f"/api/conversations/{cid}").json()["messages"] == []


def test_backend_change_cannot_mix_mock_and_real_context(settings):
    with client_for(settings) as client:
        cid = new(client)
        send(client, cid)
    with client_for(replace(settings, backend="openai"), MockBackend()) as client:
        assert send(client, cid).status_code == 409
        assert len(client.get(f"/api/conversations/{cid}").json()["messages"]) == 2


@pytest.mark.parametrize("content", ["", "  \n", "x" * 8001])
def test_invalid_messages_are_not_saved(settings, content):
    with client_for(settings) as client:
        cid = new(client)
        assert send(client, cid, content).status_code == 422
        assert client.get(f"/api/conversations/{cid}").json()["messages"] == []


def test_missing_conversation_and_deletion(settings):
    with client_for(settings) as client:
        assert send(client, "missing").status_code == 404
        cid = new(client)
        send(client, cid)
        assert client.delete(f"/api/conversations/{cid}").status_code == 204
        assert client.get(f"/api/conversations/{cid}").status_code == 404
        assert client.get("/api/conversations").json() == []
        assert client.delete(f"/api/conversations/{cid}").status_code == 404


def test_real_adapter_sends_contract_and_records_provenance(settings):
    settings = replace(
        settings, backend="openai", model="requested-alias", api_key="private-test-key"
    )
    requests = []

    def server(request):
        assert request.headers["Authorization"] == "Bearer private-test-key"
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "requested-alias"}]})
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        body = json.loads(request.content)
        requests.append(body)
        return httpx.Response(
            200,
            json={
                "model": "reported-artifact",
                "choices": [
                    {"message": {"role": "assistant", "content": "Real API-shaped response"}}
                ],
                "usage": {"total_tokens": 15, "private_extra": "discard", "prompt_tokens": -1},
            },
        )

    adapter = OpenAIBackend(settings, httpx.MockTransport(server))
    with client_for(settings, adapter) as client:
        assert client.get("/api/status").json()["state"] == "reachable"
        assert "private-test-key" not in client.get("/api/config").text
        cid = new(client)
        response = send(client, cid, "First message")
        assert response.status_code == 200
        assert requests[0] == {
            "model": "requested-alias",
            "messages": [
                {"role": "system", "content": "A fixed test prompt."},
                {"role": "user", "content": "First message"},
            ],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 512,
        }
        provenance = response.json()["messages"][-1]["provenance"]
        assert provenance["requested_model"] == "requested-alias"
        assert provenance["reported_model"] == "reported-artifact"
        assert provenance["endpoint_locality"] == "unverified_loopback"
        assert provenance["usage"] == {"total_tokens": 15}
        assert "private-test-key" not in response.text


def test_recent_pair_context_and_full_storage(settings):
    class CapturingBackend(MockBackend):
        def __init__(self):
            self.last = None

        async def complete(self, messages):
            self.last = messages
            return {"content": "Reply", "reported_model": "test", "usage": None}

    backend = CapturingBackend()
    with client_for(replace(settings, history_pairs=1), backend) as client:
        cid = new(client)
        send(client, cid, "one")
        send(client, cid, "two")
        conversation = send(client, cid, "three").json()
        assert [m["content"] for m in backend.last] == [
            "A fixed test prompt.",
            "two",
            "Reply",
            "three",
        ]
        assert len(conversation["messages"]) == 6
        assert conversation["messages"][-1]["provenance"]["context_messages_omitted"] == 2


def test_character_budget_omits_whole_pairs(settings):
    class LargeReply(MockBackend):
        async def complete(self, messages):
            return {"content": "r" * 950, "reported_model": "test", "usage": None}

    with client_for(replace(settings, context_chars=1000), LargeReply()) as client:
        cid = new(client)
        assert send(client, cid, "a" * 100).status_code == 200
        result = send(client, cid, "b" * 100).json()
        assert result["messages"][-1]["provenance"]["context_messages_omitted"] == 2
        assert send(client, cid, "x" * 1000).status_code == 422


@pytest.mark.parametrize(
    "failure,code,status",
    [
        ("connection", "connection", 502),
        ("timeout", "timeout", 504),
        ("http401", "server_http", 502),
        ("json", "invalid_response", 502),
        ("empty", "invalid_response", 502),
        ("redirect", "server_http", 502),
    ],
)
def test_real_backend_failures_are_clear_and_never_become_mock(settings, failure, code, status):
    def server(request):
        if failure == "connection":
            raise httpx.ConnectError("raw internal details", request=request)
        if failure == "timeout":
            raise httpx.ReadTimeout("raw internal details", request=request)
        if failure == "http401":
            return httpx.Response(401, text="secret raw server error")
        if failure == "json":
            return httpx.Response(200, text="not JSON")
        if failure == "redirect":
            return httpx.Response(307, headers={"Location": "https://example.com"})
        return httpx.Response(200, json={"choices": [{"message": {"content": ""}}]})

    settings = replace(settings, backend="openai")
    backend = OpenAIBackend(settings, httpx.MockTransport(server))
    with client_for(settings, backend) as client:
        cid = new(client)
        response = send(client, cid)
        assert response.status_code == status
        assert response.json()["code"] == code
        assert "raw" not in response.text
        assert client.get(f"/api/conversations/{cid}").json()["messages"] == []


@pytest.mark.parametrize(
    "payload,state",
    [
        ({"data": [{"id": "other-model"}]}, "unconfirmed"),
        ({"error": "unexpected"}, "unavailable"),
        ({"data": None}, "unavailable"),
    ],
)
def test_status_does_not_overclaim_model_readiness(settings, payload, state):
    settings = replace(settings, backend="openai")
    backend = OpenAIBackend(
        settings, httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
    )
    with client_for(settings, backend) as client:
        assert client.get("/api/status").json()["state"] == state


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/v1",
        "http://127.0.0.1:wrong/v1",
        "file:///tmp/data",
        "http://secret@localhost/v1",
        "http://localhost/v1?api_key=secret",
    ],
)
def test_endpoint_configuration_rejects_nonlocal_or_credential_urls(settings, url):
    with pytest.raises(ValueError, match="BFI_BASE_URL"):
        replace(settings, base_url=url)


def test_local_browser_boundary(settings):
    with client_for(settings) as client:
        assert (
            client.post(
                "/api/conversations", headers={"Origin": "https://other.example"}
            ).status_code
            == 403
        )
        assert client.get("/api/config", headers={"Host": "other.example"}).status_code == 400
        assert (
            client.post("/api/conversations", headers={"Origin": "http://localhost"}).status_code
            == 201
        )


def test_overlapping_generation_is_rejected_without_interleaving(settings):
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()

        class SlowBackend(MockBackend):
            async def complete(self, messages):
                entered.set()
                await release.wait()
                return await super().complete(messages)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_app(settings, SlowBackend())),
            base_url="http://localhost",
        ) as client:
            cid = (await client.post("/api/conversations")).json()["id"]
            path = f"/api/conversations/{cid}/messages"
            first = asyncio.create_task(client.post(path, json={"content": "first"}))
            await asyncio.wait_for(entered.wait(), 2)
            try:
                second = await client.post(path, json={"content": "second"})
                assert second.status_code == 409
            finally:
                release.set()
            assert (await first).status_code == 200
            messages = (await client.get(f"/api/conversations/{cid}")).json()["messages"]
            assert len(messages) == 2
            assert messages[0]["content"] == "first"

    asyncio.run(scenario())
