"""Real Chromium/HTTP handler checks with a visibly simulated SSE server, not model inference."""

import asyncio
import json
import tempfile
import threading
import time
from pathlib import Path

import uvicorn
from browser_smoke import reserve_port, start_app
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def main():
    fixture = FastAPI()
    requests = []

    @fixture.get("/v1/models")
    def models():
        return {"data": [{"id": "smoke-model"}]}

    @fixture.post("/v1/chat/completions")
    async def complete(request: Request):
        body = await request.json()
        requests.append(body)
        if not body.get("stream"):
            return {
                "model": "simulated-http-fixture",
                "choices": [
                    {
                        "message": {
                            "content": "[Simulated server · no inference] A buffered reply.",
                        }
                    }
                ],
            }

        async def frames():
            for i, text in enumerate(["[Simulated server · no inference] ", "A live ", "reply."]):
                yield (
                    "data: "
                    + json.dumps(
                        {
                            "model": "simulated-http-fixture",
                            "choices": [
                                {"delta": {"content": text}},
                            ],
                        }
                    )
                    + "\n\n"
                )
                pause = (
                    3
                    if i == 0
                    and any(
                        word in body["messages"][-1]["content"] for word in ("cancel", "reload")
                    )
                    else 0.2
                )
                await asyncio.sleep(pause)
            yield 'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n'
            yield "data: [DONE]\n\n"

        return StreamingResponse(frames(), media_type="text/event-stream")

    reserved = reserve_port()
    port = reserved.getsockname()[1]
    reserved.close()
    server = uvicorn.Server(uvicorn.Config(fixture, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    process = None
    output = ROOT / "runs/handler-browser"
    output.mkdir(parents=True, exist_ok=True)
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        assert server.started
        with tempfile.TemporaryDirectory(prefix="bfi-handler-browser-") as temp:
            project = Path(temp) / "project"
            project.mkdir()
            (project / "README.md").write_text("# Disposable browser-check project")
            process, url = start_app(
                "openai", Path(temp) / "data", f"http://127.0.0.1:{port}/v1", project, timeout=10
            )
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(url + "/handler")
                expect(page.locator("#connections .card")).to_have_count(3)
                page.locator("#check-connections").click()
                expect(page.locator("#connections")).to_contain_text("Endpoint reachable")
                page.locator("#memory-content").fill("Owner prefers a bounded 4096 context.")
                page.locator("#memory-source").fill("Scripted owner statement")
                page.locator("#save-memory").click()
                expect(page.locator("#memories .card")).to_have_count(1)
                page.locator("#memories").get_by_role("button", name="Correct", exact=True).click()
                page.locator("#memory-content").fill("Owner prefers a bounded 8192 context.")
                page.locator("#memory-source").fill("Scripted owner correction")
                page.locator("#save-memory").click()
                expect(page.locator("#memories")).to_contain_text("8192")
                with page.expect_download() as download:
                    page.locator("#export-memory").click()
                download.value.save_as(str(output / "memory-export.json"))
                exported = json.loads((output / "memory-export.json").read_text())
                assert {r["status"] for r in exported["records"]} == {"current", "superseded"}
                page.screenshot(path=str(output / "handler-desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                page.screenshot(path=str(output / "handler-phone.png"), full_page=True)

                page.goto(url + "/library")
                page.locator("#research-query").fill("speculative")
                page.locator("#research-form button").click()
                expect(page.locator("#research-results .card").first).to_be_visible()
                page.locator("#research-results").get_by_role("button").first.click()
                expect(page.locator("#report-content")).to_contain_text("Optimization")
                page.get_by_text("Add a report or research note", exact=True).click()
                for field, value in {
                    "title": "Browser saved note",
                    "category": "verification",
                    "source": "Scripted browser check",
                    "date": "2026-11-11",
                    "content": "uniqueheliotrope — a saved research note",
                }.items():
                    page.locator("#new-report-" + field).fill(value)
                page.locator("#report-form button").click()
                expect(page.locator("#report-title")).to_have_text("Browser saved note")
                page.reload()
                page.locator("#research-query").fill("uniqueheliotrope")
                page.locator("#research-form button").click()
                expect(page.locator("#research-results .card")).to_have_count(1)
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                page.screenshot(path=str(output / "library-phone.png"), full_page=True)
                page.set_viewport_size({"width": 1440, "height": 1000})
                page.screenshot(path=str(output / "library-desktop.png"), full_page=True)

                page.goto(url)
                expect(page.locator("#message")).to_be_enabled()
                page.locator("#allow-avatar").uncheck()
                page.locator("#message").fill("Please reload this live reply")
                page.locator("#send").click()
                expect(page.locator(".pending")).to_contain_text("Simulated server")
                page.reload()
                expect(page.locator(".pending")).to_contain_text("Simulated server")
                expect(page.locator(".message.assistant")).to_contain_text("A live reply.")
                assert "8192" in json.dumps(requests[-1]["messages"])
                assert "4096" not in json.dumps(requests[-1]["messages"])
                page.locator("#allow-avatar").uncheck()
                page.locator("#message").fill("Please cancel this reply")
                page.locator("#send").click()
                expect(page.locator(".pending")).to_contain_text("Simulated server")
                page.locator("#cancel-generation").click()
                expect(page.locator("#error")).to_contain_text("cancelled")
                assert page.locator(".message.assistant").count() == 1
                assert page.locator("#message").input_value() == "Please cancel this reply"
                page.locator("#message").fill("Another live reply")
                page.locator("#send").click()
                expect(page.locator(".message.assistant")).to_have_count(2)
                expect(page.locator("#send")).to_be_disabled()
                page.screenshot(path=str(output / "live-chat.png"), full_page=True)
                page.locator("#stream-reply").uncheck()
                page.locator("#message").fill("A reply without streaming")
                page.locator("#send").click()
                expect(page.locator(".message.assistant")).to_have_count(3)
                expect(page.locator(".message.assistant").last).to_contain_text("A buffered reply.")
                assert requests[-1]["stream"] is False
                page.set_viewport_size({"width": 390, "height": 844})
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                page.screenshot(path=str(output / "chat-phone.png"), full_page=True)

                page.goto(url + "/handler")
                page.on("dialog", lambda d: d.accept())
                page.locator("#memories").get_by_role("button", name="Forget", exact=True).click()
                expect(page.locator("#memories .card")).to_have_count(0)
                assert not errors, errors
                browser.close()
    finally:
        if process:
            process.terminate()
            process.wait(timeout=5)
        server.should_exit = True
        thread.join(timeout=5)
    print(
        "Handler browser checks passed: memory correction/export/forget, library import/search, "
        "SSE preview, buffered replies, reload recovery, cancellation, and desktop/phone layouts."
    )
    print("This used a simulated HTTP model server, not real inference. Evidence:", output)


if __name__ == "__main__":
    main()
