"""Verify and record the one-pose reading example in real Chromium."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import playwright
from browser_smoke import start_app
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/limited-motion"
OUT.mkdir(parents=True, exist_ok=True)
registry = Path(playwright.__file__).parent / "driver/package/browsers.json"
revision = next(
    b["revision"] for b in json.loads(registry.read_text())["browsers"] if b["name"] == "ffmpeg"
)
helper = Path("/tmp/bfi-browser-deps") / f"ffmpeg-{revision}/ffmpeg-linux"
helper.parent.mkdir(parents=True, exist_ok=True)
if not helper.exists():
    helper.symlink_to(shutil.which("ffmpeg"))
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(helper.parent.parent)
with tempfile.TemporaryDirectory(prefix="bfi-limited-motion-") as folder:
    process, url = start_app("mock", folder, "http://127.0.0.1:1/v1", ROOT)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
            page = browser.new_page(viewport={"width": 1120, "height": 900})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url + "/static/e-preview/limited-motion.html")
            page.wait_for_selector("#limited-actor svg")
            page.locator("#play").click()
            assert page.locator("#fixed-body").get_attribute("transform") is None
            hands = page.locator("#reading-left-hand path").count()
            assert hands == 1, hands
            for value in [0, 250, 500, 750, 1000]:
                page.locator("#scrub").evaluate(
                    '(el,value)=>{el.value=value;el.dispatchEvent(new Event("input"));}', value
                )
                assert page.locator("#fixed-body").get_attribute("transform") is None
            page.locator("#scrub").evaluate(
                'el=>{el.value=500;el.dispatchEvent(new Event("input"));}'
            )
            assert "rotate(0 " not in page.locator("#reading-head").get_attribute("transform")
            for width, height in [(1120, 900), (768, 1024), (390, 844)]:
                page.set_viewport_size({"width": width, "height": height})
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                page.locator(".art-panel").screenshot(path=str(OUT / f"animated-frame-{width}.png"))
                page.locator("#original").click()
                assert page.locator("#original-actor").is_visible()
                assert page.locator("#limited-actor").is_hidden()
                assert page.locator("#play").is_disabled()
                page.locator(".art-panel").screenshot(path=str(OUT / f"original-{width}.png"))
                page.locator("#original").click()
            assert page.locator("#restored-book-under-hands").count() == 1
            page.locator("#reveal").click()
            assert (
                page.locator("#reading-left-hand").evaluate("el=>getComputedStyle(el).visibility")
                == "hidden"
            )
            page.locator(".art-panel").screenshot(path=str(OUT / "rear-layer.png"))
            page.locator("#reveal").click()
            page.locator("#zoom").click()
            assert page.locator("#limited-actor svg").get_attribute("viewBox") == "155 105 205 275"
            page.emulate_media(reduced_motion="reduce")
            page.wait_for_function('() => document.querySelector("#play").disabled')
            assert page.locator("#play").is_disabled()
            assert page.locator("#scrub").input_value() == "0"
            assert not errors, errors
            page.close()
            context = browser.new_context(
                viewport={"width": 1120, "height": 900},
                record_video_dir=str(OUT / "video"),
                record_video_size={"width": 1120, "height": 900},
            )
            page = context.new_page()
            page.goto(url + "/static/e-preview/limited-motion.html")
            page.wait_for_selector("#limited-actor svg")
            page.locator(".example").evaluate('el=>el.scrollIntoView({block:"start"})')
            page.wait_for_timeout(8100)
            page.locator("#original").click()
            page.wait_for_timeout(1500)
            page.locator("#original").click()
            page.locator("#zoom").click()
            page.wait_for_timeout(4200)
            video = page.video
            context.close()
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(video.path()),
                    "-c:v",
                    "libx264",
                    "-crf",
                    "22",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(ROOT / "bfi/static/e-preview/assets/reading-limited.mp4"),
                ],
                check=True,
            )
            browser.close()
            print(
                "PASS: fixed body, whole hands, timeline, source comparison, close-up, "
                "3 layouts and reduced motion; recorded real browser playback."
            )
    finally:
        process.terminate()
        process.wait(timeout=5)
