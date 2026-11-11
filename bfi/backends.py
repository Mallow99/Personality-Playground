"""Replaceable inference adapters. Mock mode never silently substitutes for a failed server."""

import json
from typing import Protocol

import httpx

from bfi.config import Settings
from bfi.tools import ToolError


class BackendError(Exception):
    def __init__(self, message, code="backend_error", status=502):
        self.message, self.code, self.status = message, code, status
        super().__init__(message)


class Backend(Protocol):
    async def status(self) -> dict: ...
    async def complete(self, messages: list[dict]) -> dict: ...


class MockBackend:
    async def status(self):
        return {
            "state": "mock",
            "label": "Mock backend",
            "detail": "Scripted replies only. No model is loaded and no inference is running.",
        }

    async def complete(self, messages):
        return {
            "content": "[Mock reply · no model inference]\n\n"
            "Your message reached the application. This is a scripted response, "
            "so I can’t reason about it yet. This successful exchange will be saved "
            "in your conversation history.\n\n"
            "To talk to a model, start a compatible local server, set "
            "BFI_BACKEND=openai in .env, and start a new conversation.",
            "reported_model": "mock-script-v1",
            "usage": None,
        }


class OpenAIBackend:
    def __init__(self, settings: Settings, transport=None):
        self.settings, self.transport = settings, transport

    async def request(self, method, path, **kwargs):
        headers = (
            {"Authorization": f"Bearer {self.settings.api_key}"} if self.settings.api_key else {}
        )
        try:
            # Never forward loopback conversations through an environment HTTP proxy.
            async with httpx.AsyncClient(
                timeout=self.settings.timeout,
                headers=headers,
                trust_env=False,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = await client.request(
                    method, self.settings.base_url.rstrip("/") + path, **kwargs
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            raise BackendError(
                "The model server timed out. It may still be loading or generating. "
                "Check its terminal, or increase BFI_TIMEOUT_SECONDS.",
                "timeout",
                504,
            ) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            hint = {
                401: "Check BFI_API_KEY.",
                403: "Check BFI_API_KEY and server permissions.",
                404: "Check BFI_BASE_URL, the /v1 prefix, and BFI_MODEL.",
                400: "Check the model name, chat template, and context size.",
                429: "The model server is busy. Try again after its current request.",
                503: "The model may still be loading. Check the server terminal.",
            }.get(status, "Check the model server terminal and configuration.")
            # Do not echo a server response that could contain credentials or private text.
            raise BackendError(
                f"Model server returned HTTP {status}. {hint}", "server_http"
            ) from exc
        except httpx.RequestError as exc:
            raise BackendError(
                "Cannot reach the local model server. Start it, confirm its port, "
                "and check BFI_BASE_URL in .env. No mock reply was substituted.",
                "connection",
            ) from exc
        except ValueError as exc:
            raise BackendError(
                "The server returned invalid JSON. Check that this is an "
                "OpenAI-compatible API endpoint.",
                "invalid_response",
            ) from exc

    async def status(self):
        try:
            data = await self.request("GET", "/models", timeout=min(5, self.settings.timeout))
            models = data["data"]
            if not isinstance(models, list):
                raise TypeError
            ids = [m["id"] for m in models]
        except BackendError as exc:
            return {
                "state": "unavailable",
                "label": "Endpoint not confirmed",
                "detail": exc.message,
            }
        except (KeyError, TypeError):
            return {
                "state": "unavailable",
                "label": "Unexpected model list",
                "detail": "Expected a /models response with a data array of model IDs.",
            }
        listed = self.settings.model in ids
        return {
            "state": "reachable" if listed else "unconfirmed",
            "advertised_models": ids[:100],
            "label": "Endpoint reachable" if listed else "Model not listed",
            "detail": "The server advertises the configured model. Generation is not yet tested."
            if listed
            else "The server replied, but did not list BFI_MODEL. Some servers use "
            "aliases. You can try a message; check the server configuration if it fails.",
        }

    async def complete(self, messages):
        data = await self.request(
            "POST",
            "/chat/completions",
            json=self.body(messages),
        )
        return self.parse_reply(data)

    def body(self, messages, stream=False):
        body = {
            "model": self.settings.model,
            "messages": messages,
            "stream": stream,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
        }
        if self.settings.top_p is not None:
            body["top_p"] = self.settings.top_p
        return body

    async def complete_stream(self, messages, on_delta):
        """Read genuine SSE deltas. A failed/unfinished stream is never committed as a reply."""
        headers = (
            {"Authorization": f"Bearer {self.settings.api_key}"} if self.settings.api_key else {}
        )
        content, model, usage, finished = [], None, None, False
        size = 0
        try:
            async with (
                httpx.AsyncClient(
                    timeout=self.settings.timeout,
                    headers=headers,
                    trust_env=False,
                    follow_redirects=False,
                    transport=self.transport,
                ) as client,
                client.stream(
                    "POST",
                    self.settings.base_url.rstrip("/") + "/chat/completions",
                    json=self.body(messages, stream=True),
                ) as response,
            ):
                response.raise_for_status()
                if "text/event-stream" not in response.headers.get("content-type", ""):
                    raise BackendError(
                        "This endpoint did not return an SSE stream. Turn off live "
                        "reply display for this request.",
                        "stream_unsupported",
                    )
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        finished = True
                        break
                    data = json.loads(payload)
                    if data.get("error"):
                        raise ValueError("stream error")
                    if data.get("model") is not None:
                        if not isinstance(data["model"], str):
                            raise ValueError("invalid model")
                        model = data["model"]
                    if isinstance(data.get("usage"), dict):
                        usage = {
                            k: v
                            for k, v in data["usage"].items()
                            if k in {"prompt_tokens", "completion_tokens", "total_tokens"}
                            and type(v) is int
                            and v >= 0
                        }
                    choices = data.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    if delta.get("tool_calls"):
                        raise ValueError("unexpected tool call")
                    text = delta.get("content")
                    if text is not None:
                        if not isinstance(text, str):
                            raise ValueError("invalid delta")
                        size += len(text)
                        if size > 160000:
                            raise ValueError("response too large")
                        content.append(text)
                        on_delta(text)
                    if choices[0].get("finish_reason") is not None:
                        finished = True
        except httpx.TimeoutException as exc:
            raise BackendError(
                "The model stream timed out. Partial text was not saved as a completed reply.",
                "timeout",
                504,
            ) from exc
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise BackendError(
                "The model stream failed. Check the local server and its streaming "
                "support. No mock reply was substituted.",
                "stream_connection",
            ) from exc
        except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
            raise BackendError(
                "The server returned an invalid or excessive stream. No completed reply was saved.",
                "invalid_stream",
            ) from exc
        text = "".join(content)
        if not finished or not text.strip():
            raise BackendError(
                "The model stream ended without a completed text reply. Partial "
                "text was not committed.",
                "incomplete_stream",
            )
        return {"content": text, "reported_model": model, "usage": usage}

    @staticmethod
    def parse_reply(data):
        try:
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError
            reported = data.get("model")
            if reported is not None and not isinstance(reported, str):
                raise ValueError
            usage = data.get("usage")
            # Retain only numeric token counts, not arbitrary backend metadata.
            usage = (
                {
                    k: v
                    for k, v in usage.items()
                    if k in {"prompt_tokens", "completion_tokens", "total_tokens"}
                    and type(v) is int
                    and v >= 0
                }
                if isinstance(usage, dict)
                else None
            )
            return {"content": content, "reported_model": reported, "usage": usage}
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise BackendError(
                "The server returned no usable assistant text. Check its chat "
                "template and OpenAI chat-completions support.",
                "invalid_response",
            ) from exc

    async def complete_with_tools(self, messages, definitions, runner):
        """At most three tool calls, then one final text response. No arbitrary execution."""
        context, trace, usage = list(messages), [], {}
        allowed = {d["function"]["name"] for d in definitions}
        for generation in range(4):
            body = self.body(context)
            if len(trace) < 3:
                body.update(tools=definitions, tool_choice="auto")
            if len(json.dumps(body["messages"], ensure_ascii=False)) > self.settings.context_chars:
                raise BackendError(
                    "Tool results exceeded the configured context budget. "
                    "Narrow the request or raise BFI_CONTEXT_CHARS.",
                    "context_limit",
                )
            data = await self.request("POST", "/chat/completions", json=body)
            try:
                message = data["choices"][0]["message"]
                calls = message.get("tool_calls")
                if not calls:
                    reply = self.parse_reply(data)
                    for key, value in (reply["usage"] or {}).items():
                        usage[key] = usage.get(key, 0) + value
                    return {
                        **reply,
                        "usage": usage or None,
                        "tool_steps": trace,
                        "generation_calls": generation + 1,
                    }
                if not isinstance(calls, list) or len(calls) + len(trace) > 3:
                    raise ValueError
                # Save only the standard assistant fields, not arbitrary server extras.
                assistant = {
                    "role": "assistant",
                    "content": message.get("content"),
                    "tool_calls": [],
                }
                for call in calls:
                    function = call["function"]
                    if (
                        not isinstance(call["id"], str)
                        or len(call["id"]) > 200
                        or function["name"] not in allowed
                        or not isinstance(function["arguments"], str)
                        or len(function["arguments"]) > 4000
                    ):
                        raise ValueError
                    arguments = json.loads(function["arguments"])
                    assistant["tool_calls"].append(
                        {"id": call["id"], "type": "function", "function": function}
                    )
                    try:
                        result = await runner.run(function["name"], arguments, allowed)
                    except ToolError as exc:
                        result = {"error": str(exc)}
                    trace.append(
                        {
                            "call_id": call["id"],
                            "name": function["name"],
                            "arguments": arguments,
                            "result": result,
                        }
                    )
                context.append(assistant)
                for step in trace[-len(calls) :]:
                    context.append(
                        {
                            "role": "tool",
                            "tool_call_id": step["call_id"],
                            "content": runner.serialize(step["result"]),
                        }
                    )
                for key, value in (data.get("usage") or {}).items():
                    if (
                        key in {"prompt_tokens", "completion_tokens", "total_tokens"}
                        and type(value) is int
                        and value >= 0
                    ):
                        usage[key] = usage.get(key, 0) + value
            except (KeyError, IndexError, TypeError, ValueError, AttributeError) as exc:
                raise BackendError(
                    "The model returned invalid or excessive tool calls. "
                    "Only the tools enabled for this message may run; "
                    "a maximum of three calls is allowed.",
                    "invalid_tool_calls",
                ) from exc
        raise BackendError(
            "The model did not produce a final reply within the tool-call limit.", "tool_limit"
        )
