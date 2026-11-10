"""Optional real-browser checks, using disposable data and explicitly scripted replies.

Run: uv run --locked --group browser python scripts/browser_smoke.py
First install Chromium: uv run --locked --group browser playwright install chromium
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def reserve_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    return sock


def start_app(backend, data_dir, endpoint, project_dir):
    reservation = reserve_port()
    port = reservation.getsockname()[1]
    reservation.close()
    env = {
        **os.environ,
        "BFI_BACKEND": backend,
        "BFI_DATA_DIR": str(data_dir),
        "BFI_BASE_URL": endpoint,
        "BFI_API_KEY": "",
        "BFI_MODEL": "smoke-model",
        "BFI_CHARACTER_FILE": str(ROOT / "config/character.json"),
        "BFI_TIMEOUT_SECONDS": "2",
        "BFI_HISTORY_PAIRS": "12",
        "BFI_CONTEXT_CHARS": "24000",
        "BFI_PROFILES_FILE": str(ROOT / "config/profiles.json"),
        "BFI_PROJECT_ROOT": str(project_dir),
        "BFI_BRAVE_API_KEY": "",
    }
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "bfi.main:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError("Test app exited before it became ready.")
            try:
                if httpx.get(url + "/api/config", timeout=0.3, trust_env=False).status_code == 200:
                    return process, url
            except httpx.RequestError:
                pass
            time.sleep(0.1)
        raise RuntimeError("Test app did not become ready within 10 seconds.")
    except BaseException:
        process.terminate()
        process.wait(timeout=5)
        raise


def check_browser(mock_url, unavailable_url, output, executable):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=executable)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                external.append(request.url)
                if not request.url.startswith((mock_url, unavailable_url))
                else None
            ),
        )
        page.goto(mock_url)
        page.get_by_text("Mock backend", exact=True).wait_for()
        page.screenshot(path=str(output / "home.png"), full_page=True)
        page.get_by_role("button", name="Find a first step").click()
        assert "small first step" in page.locator("#message").input_value()
        page.locator("#message").fill("Hello foundation <b>literal text</b>")
        page.locator("#message").press("Enter")
        page.locator(".message.assistant").wait_for()
        assert page.locator(".message").count() == 2
        assert page.locator(".message.user b").count() == 0
        assert page.locator("#message").input_value() == ""
        page.locator(".provenance summary").click()
        assert page.locator(".provenance").inner_text().count("mock-script-v1") == 2
        with page.expect_download() as event:
            page.locator("#export-chat").click()
        event.value.save_as(str(output / "test-export.json"))
        exported = json.loads((output / "test-export.json").read_text())
        assert len(exported["messages"]) == 2
        cid = exported["id"]
        page.reload()
        page.locator(".message.assistant").wait_for()
        assert page.locator(".message").count() == 2
        page.locator("#open-status").click()
        assert page.locator("#status-dialog").is_visible()
        page.get_by_text("Scripted replies only.", exact=False).wait_for()
        page.locator("#close-status").click()
        page.locator("#new-chat").click()
        assert page.locator("#empty-state").is_visible()
        page.locator(".conversation-item").first.click()
        page.locator(".message.assistant").wait_for()
        page.screenshot(path=str(output / "chat.png"), full_page=True)
        for width, height in [(390, 844), (768, 1024)]:
            page.set_viewport_size({"width": width, "height": height})
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
            assert page.locator("#message").is_visible()
            page.screenshot(path=str(output / f"chat-{width}.png"), full_page=True)
        page.on("dialog", lambda dialog: dialog.accept())
        page.locator("#delete-chat").click()
        page.locator("#empty-state").wait_for(state="visible")
        assert page.request.get(f"{mock_url}/api/conversations/{cid}").status == 404

        page.set_viewport_size({"width": 1440, "height": 1000})
        for profile in ("academic", "engineering", "business"):
            page.locator("#profile-select").select_option(profile)
            assert page.locator("body").get_attribute("data-theme") == profile
            page.locator("#message").fill(f"Hello from {profile}")
            page.locator("#send").click()
            page.locator(".message.assistant").wait_for()
            assert page.locator(".message").count() == 2
            page.locator(".provenance summary").click()
            assert profile in page.locator(".provenance").inner_text()
        page.locator("#avatar-motion").uncheck()
        page.locator("#avatar-pose").select_option("business/thinking")
        page.wait_for_function(
            '() => document.querySelector("#sidebar-avatar").dataset.pose === "business/thinking"'
        )
        if page.locator("#corner-companion").is_hidden():
            page.locator("#toggle-corner").click()
        page.wait_for_selector("#corner-companion", state="visible")
        page.locator("#hide-corner").click()
        page.locator("#open-tools").click()
        page.locator("#run-tool").click()
        page.get_by_text('"files":', exact=False).wait_for()
        assert "README.md" in page.locator("#tool-result").inner_text()
        page.locator("#tool-name").select_option("read_project_file")
        page.locator("#tool-argument").fill("README.md")
        page.locator("#run-tool").click()
        page.get_by_text("local_project_text", exact=False).wait_for()
        assert "Browser test project" in page.locator("#tool-result").inner_text()
        page.locator("#close-tools").click()
        page.goto(mock_url + "/concepts")
        page.get_by_text("Current route: scripted mock", exact=False).wait_for()
        page.locator("#studio-motion").uncheck()
        for profile in ("academic", "engineering", "business"):
            page.locator(f"#choose-{profile}").click()
            assert page.locator("body").get_attribute("data-theme") == profile
            page.screenshot(path=str(output / f"studio-{profile}.png"), full_page=True)
        page.locator("#studio-pose").select_option("speaking")
        page.locator("#studio-corner").click()
        assert page.locator("#studio-stage").get_attribute("data-corner") == "on"
        for width, height in ((390, 844), (768, 1024)):
            page.set_viewport_size({"width": width, "height": height})
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
            page.screenshot(path=str(output / f"studio-{width}.png"), full_page=True)
        page.locator("#try-profile").click()
        page.get_by_text("Mock backend", exact=True).wait_for()
        assert page.locator("#profile-select").input_value() == "business"

        page.goto(unavailable_url)
        page.get_by_text("Endpoint not confirmed", exact=True).wait_for()
        page.locator("#message").fill("Preserve this draft on connection failure")
        page.locator("#send").click()
        page.locator("#error").wait_for(state="visible")
        assert "Cannot reach the local model server" in page.locator("#error").inner_text()
        assert page.locator("#message").input_value() == "Preserve this draft on connection failure"
        assert page.locator(".message").count() == 0
        page.screenshot(path=str(output / "connection-error.png"), full_page=True)
        assert not errors, errors
        assert not external, external

        # Browser storage is convenience, not the source of truth for conversations.
        isolated = browser.new_context()
        isolated.add_init_script("""Object.defineProperty(window, 'localStorage', {
            get() { throw new DOMException('Storage disabled', 'SecurityError'); }
        });""")
        no_storage = isolated.new_page()
        no_storage.goto(mock_url)
        no_storage.locator("#message").fill("Chat works with browser storage disabled")
        no_storage.locator("#send").click()
        no_storage.locator(".message.assistant").wait_for()
        isolated.close()
        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", help="Optional path to an already installed Chromium")
    parser.add_argument("--output", type=Path, default=ROOT / "runs/browser-smoke")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    processes = []
    # Reserving without listening guarantees this is not an inference server.
    unavailable = reserve_port()
    endpoint = f"http://127.0.0.1:{unavailable.getsockname()[1]}/v1"
    try:
        with tempfile.TemporaryDirectory(prefix="bfi-browser-") as temp:
            project = Path(temp) / "project"
            project.mkdir()
            (project / "README.md").write_text("# Browser test project", encoding="utf-8")
            mock, mock_url = start_app("mock", Path(temp) / "mock", endpoint, project)
            processes.append(mock)
            real, real_url = start_app("openai", Path(temp) / "unavailable", endpoint, project)
            processes.append(real)
            check_browser(mock_url, real_url, args.output.resolve(), args.chromium)
    finally:
        for process in processes:
            process.terminate()
            process.wait(timeout=5)
        unavailable.close()
    print("Browser checks passed. Screenshots and scripted test export:", args.output.resolve())


if __name__ == "__main__":
    main()
