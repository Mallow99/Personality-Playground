"""Application rules, tested without a window. Model servers are simulated, never real."""

import json
import sqlite3
import threading
from dataclasses import replace

import httpx
import pytest

from bfi.backends import BackendError, MockBackend, OpenAIBackend
from bfi.config import ConfigError, Settings
from bfi.errors import AppError
from bfi.service import ChatService
from bfi.store import SCHEMA_VERSION


class FailingBackend(MockBackend):
    def complete(self, messages):
        raise BackendError("Server unavailable", "connection")


def error_code(call, *args):
    with pytest.raises(AppError) as caught:
        call(*args)
    return caught.value.code


def test_mock_is_explicit_and_transcript_survives_app_restart(settings):
    service = ChatService(settings)
    assert service.status()["state"] == "mock"
    conversation = service.send(None, "Hello")
    assert [m["role"] for m in conversation["messages"]] == ["user", "assistant"]
    reply = conversation["messages"][-1]
    assert "no model inference" in reply["content"]
    assert reply["provenance"]["reported_model"] == "mock-script-v1"
    assert reply["provenance"]["cloud_assistance"] == "none_by_app"
    assert reply["provenance"]["endpoint"] is None
    restarted = ChatService(settings)
    assert restarted.conversation(conversation["id"]) == conversation
    assert [c["id"] for c in restarted.conversations()] == [conversation["id"]]


def test_character_is_snapshotted_per_conversation(settings):
    cid = ChatService(settings).send(None, "Hello")["id"]
    data = json.loads(settings.character_file.read_text())
    data["name"], data["system_prompt"] = "Changed", "Changed prompt"
    settings.character_file.write_text(json.dumps(data))
    service = ChatService(settings)
    assert service.conversation(cid)["character"]["name"] == "Test Companion"
    assert service.send(None, "Hello")["character"]["name"] == "Changed"


def test_failed_first_message_leaves_no_conversation_behind(settings):
    service = ChatService(settings, FailingBackend())
    assert error_code(service.send, None, "Hello") == "connection"
    assert service.conversations() == []


def test_failed_later_message_keeps_transcript_unchanged(settings):
    saved = ChatService(settings).send(None, "Hello")
    service = ChatService(settings, FailingBackend())
    assert error_code(service.send, saved["id"], "Again") == "connection"
    assert service.conversation(saved["id"]) == saved


def test_backend_change_cannot_mix_mock_and_real_context(settings):
    saved = ChatService(settings).send(None, "Hello")
    service = ChatService(replace(settings, backend="openai"), MockBackend())
    assert not service.can_continue(saved)
    assert error_code(service.send, saved["id"], "Hello") == "archived"
    assert len(service.conversation(saved["id"])["messages"]) == 2


@pytest.mark.parametrize("content", ["", "  \n", "x" * 8001])
def test_invalid_messages_are_not_saved(settings, content):
    service = ChatService(settings)
    assert error_code(service.send, None, content) == "invalid"
    assert service.conversations() == []


def test_missing_conversation_and_deletion(settings):
    service = ChatService(settings)
    assert error_code(service.send, "missing", "Hello") == "not_found"
    cid = service.send(None, "Hello")["id"]
    service.delete(cid)
    assert error_code(service.conversation, cid) == "not_found"
    assert service.conversations() == []
    assert error_code(service.delete, cid) == "not_found"
    with sqlite3.connect(service.store.path) as db:
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 0


def test_title_is_one_line_and_set_by_the_first_message(settings):
    service = ChatService(settings)
    conversation = service.send(None, "First line\n\n  second line " + "x" * 80)
    assert conversation["title"] == ("First line second line " + "x" * 80)[:60]
    assert service.send(conversation["id"], "Later")["title"] == conversation["title"]


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
        requests.append(json.loads(request.content))
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

    service = ChatService(settings, OpenAIBackend(settings, httpx.MockTransport(server)))
    assert service.status()["state"] == "reachable"
    assert "private-test-key" not in json.dumps(service.config())
    conversation = service.send(None, "First message")
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
    provenance = conversation["messages"][-1]["provenance"]
    assert provenance["requested_model"] == "requested-alias"
    assert provenance["reported_model"] == "reported-artifact"
    assert provenance["endpoint_locality"] == "unverified_loopback"
    assert provenance["usage"] == {"total_tokens": 15}
    assert "private-test-key" not in json.dumps(conversation)


def test_recent_pair_context_and_full_storage(settings):
    class CapturingBackend(MockBackend):
        last = None

        def complete(self, messages):
            self.last = messages
            return {"content": "Reply", "reported_model": "test", "usage": None}

    backend = CapturingBackend()
    service = ChatService(replace(settings, history_pairs=1), backend)
    cid = service.send(None, "one")["id"]
    service.send(cid, "two")
    conversation = service.send(cid, "three")
    assert [m["content"] for m in backend.last] == ["A fixed test prompt.", "two", "Reply", "three"]
    assert len(conversation["messages"]) == 6
    assert conversation["messages"][-1]["provenance"]["context_messages_omitted"] == 2


def test_character_budget_omits_whole_pairs(settings):
    class LargeReply(MockBackend):
        def complete(self, messages):
            return {"content": "r" * 950, "reported_model": "test", "usage": None}

    service = ChatService(replace(settings, context_chars=1000), LargeReply())
    cid = service.send(None, "a" * 100)["id"]
    result = service.send(cid, "b" * 100)
    assert result["messages"][-1]["provenance"]["context_messages_omitted"] == 2
    assert error_code(service.send, cid, "x" * 1000) == "invalid"


@pytest.mark.parametrize(
    "failure,code",
    [
        ("connection", "connection"),
        ("timeout", "timeout"),
        ("http401", "server_http"),
        ("json", "invalid_response"),
        ("empty", "invalid_response"),
        ("redirect", "server_http"),
    ],
)
def test_real_backend_failures_are_clear_and_never_become_mock(settings, failure, code):
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
    service = ChatService(settings, OpenAIBackend(settings, httpx.MockTransport(server)))
    with pytest.raises(BackendError) as caught:
        service.send(None, "Hello")
    assert caught.value.code == code
    assert "raw" not in caught.value.message
    assert service.conversations() == []


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
    assert ChatService(settings, backend).status()["state"] == state


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
    with pytest.raises(ConfigError, match="BFI_BASE_URL"):
        replace(settings, base_url=url)


def test_configuration_mistakes_are_explained(settings, monkeypatch):
    monkeypatch.setenv("BFI_TIMEOUT_SECONDS", "two minutes")
    with pytest.raises(ConfigError, match="BFI_TIMEOUT_SECONDS must be a number"):
        Settings.from_env()
    settings.character_file.write_text('{"name": "Only a name"}')
    with pytest.raises(ConfigError, match="system_prompt"):
        ChatService(settings)
    settings.character_file.write_text("not json")
    with pytest.raises(ConfigError, match="not valid"):
        ChatService(settings)
    settings.character_file.unlink()
    with pytest.raises(ConfigError, match="Cannot read"):
        ChatService(settings)


def test_data_from_a_newer_app_version_is_refused_untouched(settings):
    ChatService(settings).send(None, "Hello")
    path = settings.data_dir / "conversations.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
    assert error_code(ChatService, settings) == "newer_data"
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION + 1
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 2


def test_overlapping_generation_is_rejected_without_interleaving(settings):
    entered, release = threading.Event(), threading.Event()

    class SlowBackend(MockBackend):
        def complete(self, messages):
            entered.set()
            assert release.wait(5)
            return super().complete(messages)

    service = ChatService(settings, SlowBackend())
    results = []
    first = threading.Thread(target=lambda: results.append(service.send(None, "first")))
    first.start()
    try:
        assert entered.wait(5)
        assert error_code(service.send, None, "second") == "busy"
        assert error_code(service.delete, "anything") == "busy"
    finally:
        release.set()
        first.join(5)
    assert [m["content"] for m in results[0]["messages"]][0] == "first"
    assert len(service.conversations()) == 1
    assert service.send(results[0]["id"], "third")["messages"][2]["content"] == "third"
