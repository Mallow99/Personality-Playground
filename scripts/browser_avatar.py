"""Exercise real handler/avatar wiring in Chromium; mock replies remain labeled mock."""

import json
import tempfile
from pathlib import Path

from browser_smoke import start_app
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/runtime-avatar"
OUT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="bfi-avatar-") as folder:
    process, url = start_app("mock", folder, "http://127.0.0.1:1/v1", ROOT)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(url)
            page.wait_for_selector("#sidebar-avatar img", state="attached")
            page.wait_for_function('()=>document.querySelector("#avatar-pose").options.length===42')
            overlay = context.new_page()
            overlay.on("pageerror", lambda e: errors.append(str(e)))
            overlay.goto(url + "/overlay")
            overlay.wait_for_selector(".avatar-art img")
            for role, pose in [
                ("academic", "academic/S01"),
                ("engineering", "engineering/H10"),
                ("business", "business/B03"),
            ]:
                page.locator("#profile-select").select_option(role)
                page.wait_for_function(
                    '(role)=>document.querySelector("#sidebar-avatar").dataset.profile===role',
                    arg=role,
                )
                page.locator("#avatar-pose").select_option(pose)
                page.wait_for_function(
                    '(pose)=>document.querySelector("#sidebar-avatar").dataset.pose===pose',
                    arg=pose,
                )
                overlay.wait_for_function(
                    '(pose)=>document.querySelector(".avatar-view").dataset.pose===pose', arg=pose
                )
                assert page.locator("body").get_attribute("data-theme") == role
                page.locator("#message").fill("Please help me plan this.")
                page.locator("#send").click()
                page.wait_for_selector(".message.assistant")
                overlay.wait_for_function(
                    '()=>document.querySelector(".avatar-view").dataset.activity==="speaking"'
                )
                assert "Mock reply" in overlay.locator(".avatar-caption").inner_text()
                page.wait_for_timeout(250)
                page.screenshot(path=str(OUT / f"{role}-handler.png"))
            page.locator("#profile-select").select_option("academic")
            page.wait_for_function(
                '()=>document.querySelector("#sidebar-avatar").dataset.profile==="academic"'
            )
            page.locator("#avatar-pose").select_option("academic/reading")
            page.wait_for_selector("#sidebar-avatar svg #reading-head", state="attached")
            overlay.wait_for_selector("#reading-head")
            overlay.bring_to_front()
            before = overlay.locator("#held-book").get_attribute("transform")
            overlay.wait_for_timeout(450)
            assert overlay.locator("#held-book").get_attribute("transform") != before
            page.locator("#avatar-motion").uncheck()
            overlay.wait_for_function(
                '()=>document.querySelector(".avatar-view").dataset.motion==="off"'
            )
            page.locator("#avatar-dock").select_option("bottom-left")
            page.wait_for_function(
                '()=>document.querySelector("#corner-companion").dataset.dock==="bottom-left"'
            )
            page.locator("#hide-corner").click()
            overlay.wait_for_function('()=>document.querySelector("#overlay-avatar").hidden')
            overlay.locator("#hide-avatar").click()
            page.wait_for_function('()=>!document.querySelector("#corner-companion").hidden')
            for width, height in [(1440, 1000), (768, 1024), (390, 844)]:
                page.set_viewport_size({"width": width, "height": height})
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                page.screenshot(path=str(OUT / f"layout-{width}.png"))
            state = page.request.get(url + "/api/avatar").json()
            assert state["pose_id"] == "academic/reading"
            page.request.post(
                url + "/api/avatar",
                data=json.dumps({"caption": "<img src=x onerror=alert(1)>"}),
                headers={"Content-Type": "application/json"},
            )
            overlay.wait_for_function(
                '()=>document.querySelector(".avatar-caption").textContent.includes("<img")'
            )
            assert overlay.locator(".avatar-caption img").count() == 0
            page.goto(url + "/static/e-preview/runtime-demo.html")
            page.wait_for_selector("#avatar #reading-head")
            page.locator('[data-role="business"]').click()
            page.locator("#pose").select_option("business/B03")
            page.locator("#reply").click()
            assert page.locator("#avatar").get_attribute("data-activity") == "speaking"
            assert page.request.get(url + "/api/avatar").json()["profile"] == "academic"
            for width, height in [(1440, 1000), (768, 1024), (390, 844)]:
                page.set_viewport_size({"width": width, "height": height})
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            page.screenshot(path=str(OUT / "static-demo-phone.png"))
            assert not errors, errors
            browser.close()
            print(
                "PASS: 3 character themes, concept cutouts, mock reply cues, two-window sync, "
                "reading motion, owner controls, 3 layouts and caption text isolation."
            )
    finally:
        process.terminate()
        process.wait(timeout=5)
