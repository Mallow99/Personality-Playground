import asyncio
import json
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from bfi.backends import BackendError, OpenAIBackend
from bfi.config import Settings
from bfi.main import create_app
from bfi.tools import ToolError, ToolRunner


@pytest.fixture
def settings(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("# The actual project\nRead this exact text.")
    (project / ".env").write_text("PRIVATE_KEY=do-not-read")
    (project / "data").mkdir()
    (project / "data" / "chat.txt").write_text("Private conversation")
    return Settings(data_dir=tmp_path / "data", project_root=project)


def client(settings, backend=None):
    return TestClient(create_app(settings, backend), base_url="http://localhost")


def test_three_profiles_have_separate_prompts_and_configurable_routes(settings, monkeypatch):
    monkeypatch.setenv("BFI_ENGINEERING_MODEL", "code-model")
    monkeypatch.setenv("BFI_ENGINEERING_API_KEY", "private-code-key")
    monkeypatch.setenv("BFI_ACADEMIC_ADAPTER_LABEL", "study-lora-r1")
    requests = []

    async def request(adapter, method, path, **kwargs):
        requests.append((adapter.settings.model, kwargs.get("json")))
        return {"model": adapter.settings.model, "choices": [{"message": {"content": "A reply"}}]}

    monkeypatch.setattr(OpenAIBackend, "request", request)
    with client(replace(settings, backend="openai")) as app:
        config = app.get("/api/config")
        profiles = config.json()["profiles"]
        assert [p["id"] for p in profiles] == ["academic", "engineering", "business"]
        assert len({p["character"]["system_prompt"] for p in profiles}) == 3
        assert "private-code-key" not in config.text
        ids = []
        for profile in profiles:
            conversation = app.post("/api/conversations", json={"profile_id": profile["id"]}).json()
            ids.append(conversation["id"])
            result = app.post(f"/api/conversations/{ids[-1]}/messages", json={"content": "Hello"})
            assert result.status_code == 200
            assert result.json()["messages"][-1]["provenance"]["profile_id"] == profile["id"]
        assert requests[0][0] == "local-model"
        assert requests[1][0] == "code-model"
        assert requests[1][1]["messages"][0]["content"] == profiles[1]["character"]["system_prompt"]
        assert len(set(ids)) == 3
        assert app.post("/api/conversations", json={"profile_id": "unknown"}).status_code == 404
        assert app.get("/api/status?profile_id=unknown").status_code == 404


def test_profile_route_change_does_not_reuse_an_old_transcript(settings, monkeypatch):
    with client(settings) as app:
        cid = app.post("/api/conversations", json={"profile_id": "engineering"}).json()["id"]
    monkeypatch.setenv("BFI_ENGINEERING_BACKEND", "openai")
    monkeypatch.setenv("BFI_ENGINEERING_MODEL", "a-different-model")
    with client(settings) as app:
        assert (
            app.post(f"/api/conversations/{cid}/messages", json={"content": "hello"}).status_code
            == 409
        )
        assert app.get(f"/api/conversations/{cid}").json()["messages"] == []


def test_actual_project_tool_results_and_disabled_capabilities(settings):
    with client(settings) as app:
        listed = app.post("/api/tools/inspect", json={"name": "list_project_files"})
        assert listed.status_code == 200
        assert listed.json()["result"]["files"] == ["README.md"]
        read = app.post(
            "/api/tools/inspect",
            json={"name": "read_project_file", "arguments": {"path": "README.md"}},
        )
        assert "Read this exact text." in read.json()["result"]["content"]
        assert (
            app.post(
                "/api/tools/inspect", json={"name": "web_search", "arguments": {"query": "test"}}
            ).status_code
            == 400
        )
    with client(replace(settings, project_root=None)) as app:
        assert (
            app.post("/api/tools/inspect", json={"name": "list_project_files"}).status_code == 400
        )
        assert app.get("/api/config").json()["tools"]["project_files"] is False


@pytest.mark.parametrize(
    "path",
    ["../outside.txt", ".env", "data/chat.txt", "/etc/passwd", "passwords.txt", "missing.md"],
)
def test_project_file_boundaries(settings, path):
    runner = ToolRunner(settings)
    with pytest.raises(ToolError):
        asyncio.run(runner.run("read_project_file", {"path": path}, {"read_project_file"}))


def test_project_links_are_not_followed(settings, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text("Outside the chosen project")
    try:
        (settings.project_root / "link.md").symlink_to(outside)
    except OSError:
        pytest.skip("This Windows account does not have symlink permission.")
    with pytest.raises(ToolError, match="links"):
        ToolRunner(settings).allowed_file("link.md")


def test_tools_are_explicit_and_mock_does_not_pretend_to_call_them(settings):
    with client(settings) as app:
        cid = app.post("/api/conversations").json()["id"]
        response = app.post(
            f"/api/conversations/{cid}/messages",
            json={"content": "Read my project", "project_tools": True},
        )
        assert response.status_code == 400
        assert "mock" in response.json()["detail"]
        assert app.get(f"/api/conversations/{cid}").json()["messages"] == []


def test_model_tool_round_trip_has_exact_results_and_persisted_trace(settings):
    settings = replace(settings, backend="openai")
    requests = []

    def server(request):
        payload = json.loads(request.content)
        requests.append(payload)
        if len(requests) == 1:
            assert {d["function"]["name"] for d in payload["tools"]} == {
                "list_project_files",
                "read_project_file",
            }
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call-1",
                                        "type": "function",
                                        "function": {
                                            "name": "read_project_file",
                                            "arguments": '{"path":"README.md"}',
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                    "usage": {"total_tokens": 10},
                },
            )
        tool_result = json.loads(payload["messages"][-1]["content"])
        assert tool_result["content"] == "# The actual project\nRead this exact text."
        assert payload["messages"][-1]["role"] == "tool"
        return httpx.Response(
            200,
            json={
                "model": "tool-model",
                "choices": [{"message": {"content": "I read the actual project."}}],
                "usage": {"total_tokens": 5},
            },
        )

    adapter = OpenAIBackend(settings, httpx.MockTransport(server))
    with client(settings, adapter) as app:
        cid = app.post("/api/conversations").json()["id"]
        response = app.post(
            f"/api/conversations/{cid}/messages",
            json={"content": "Read the README", "project_tools": True},
        )
        assert response.status_code == 200
        trace = response.json()["messages"][-1]["provenance"]
        assert trace["generation_calls"] == 2
        assert trace["usage"] == {"total_tokens": 15}
        assert trace["tool_steps"][0]["name"] == "read_project_file"
        assert trace["tool_steps"][0]["result"]["source_type"] == "local_project_text"


def test_model_cannot_request_a_tool_that_was_not_enabled(settings):
    def server(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {"id": "x", "function": {"name": "run_shell", "arguments": "{}"}}
                            ]
                        }
                    }
                ]
            },
        )

    adapter = OpenAIBackend(settings, httpx.MockTransport(server))
    runner = ToolRunner(settings)
    with pytest.raises(BackendError, match="invalid or excessive"):
        asyncio.run(adapter.complete_with_tools([], runner.definitions(project=True), runner))


def test_tool_call_count_is_bounded(settings):
    calls = []

    def server(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": str(len(calls)),
                                    "function": {"name": "list_project_files", "arguments": "{}"},
                                }
                            ]
                        }
                    }
                ]
            },
        )

    runner = ToolRunner(settings)
    with pytest.raises(BackendError):
        asyncio.run(
            OpenAIBackend(settings, httpx.MockTransport(server)).complete_with_tools(
                [], runner.definitions(project=True), runner
            )
        )
    assert len(calls) == 4


def test_search_uses_provider_and_returns_sources_without_exposing_key(settings):
    def server(request):
        assert request.headers["X-Subscription-Token"] == "private-search-key"
        assert request.url.params["q"] == "local AI"
        return httpx.Response(
            200,
            json={
                "web": {
                    "results": [
                        {
                            "title": "A source",
                            "url": "https://example.com",
                            "description": "An actual snippet",
                        }
                    ]
                }
            },
        )

    runner = ToolRunner(
        replace(settings, search_api_key="private-search-key"), httpx.MockTransport(server)
    )
    result = asyncio.run(runner.run("web_search", {"query": "local AI"}, {"web_search"}))
    assert result["results"][0]["url"] == "https://example.com"
    assert result["source_type"] == "search_snippets"
    assert "private-search-key" not in json.dumps(result)


def test_search_failure_is_not_a_fabricated_result(settings):
    runner = ToolRunner(
        replace(settings, search_api_key="test"), httpx.MockTransport(lambda r: httpx.Response(429))
    )
    with pytest.raises(ToolError, match="No results were invented"):
        asyncio.run(runner.run("web_search", {"query": "test"}, {"web_search"}))
