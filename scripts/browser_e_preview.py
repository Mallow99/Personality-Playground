"""Exercise the E proof in a real Chromium against the local BFI app.

uv run --locked --group browser python scripts/browser_e_preview.py
"""

import json
import tempfile
from pathlib import Path

from browser_smoke import start_app
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/e-preview-v2"
OUT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="bfi-e-browser-") as folder:
    process, url = start_app("mock", folder, "http://127.0.0.1:1/v1", ROOT)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
            context = browser.new_context(viewport={"width": 1440, "height": 1100})
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url + "/static/e-preview/index.html")
            page.wait_for_selector("#actor svg")
            page.locator("#motion").uncheck()
            manifest = json.loads(
                (ROOT / "bfi/static/e-preview/assets/poses/manifest.json").read_text()
            )
            for role, items in manifest["characters"].items():
                page.locator(f'button[data-profile="{role}"]').click()
                page.wait_for_function(
                    '(id)=>document.querySelector("#actor").dataset.profile===id', arg=role
                )
                assert page.locator("#pose option").count() == 18
                for item in items:
                    page.locator("#pose").select_option(item["id"])
                    page.wait_for_function(
                        '(id)=>document.querySelector("#actor svg").dataset.pose===id',
                        arg=item["id"],
                    )
                    page.wait_for_function(
                        'Array.from(document.querySelectorAll("#comparison-box img"))'
                        ".every(i=>i.complete && i.naturalWidth>0)"
                    )
                page.locator("#pose").select_option("seated")
                page.wait_for_function(
                    'document.querySelector("#actor svg").dataset.pose==="seated"'
                )
                page.locator("#pose-filter").select_option("playful")
                assert page.locator("#pose-grid figure:visible").count() == 4
                page.locator("#pose-filter").select_option("practical")
                assert page.locator("#pose-grid figure:visible").count() == 14
                page.locator("#comparison-mode").select_option("vector")
                page.locator("#actor").screenshot(path=str(OUT / f"{role}-seated.png"))
                page.locator("#fidelity").screenshot(path=str(OUT / f"{role}-comparison.png"))
            for width, height in [(1440, 1100), (768, 1024), (390, 844)]:
                page.set_viewport_size({"width": width, "height": height})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
                page.evaluate("scrollTo(0,0)")
                page.screenshot(path=str(OUT / f"layout-{width}.png"))
            page.locator("#motion").check()
            for role in manifest["characters"]:
                page.locator(f'button[data-profile="{role}"]').click()
                page.wait_for_timeout(650)
                page.screenshot(path=str(OUT / f"{role}-transition.png"))
                page.keyboard.press("Escape")
                assert page.locator("#transition-layer").is_hidden()
            page.evaluate(
                'document.querySelector("[data-profile=academic]").click();document.querySelector("[data-profile=engineering]").click();document.querySelector("[data-profile=business]").click();'
            )
            page.wait_for_function('document.querySelector("#actor").dataset.profile==="business"')
            page.keyboard.press("Escape")
            page.locator("#sequence").click()
            page.wait_for_timeout(3300)
            assert page.locator("#actor").evaluate('(el)=>el.classList.contains("speaking")')
            page.wait_for_timeout(9000)
            assert page.locator("#actor").get_attribute("data-visible") == "false"
            page.locator("#visibility").click()
            assert page.locator("#actor").get_attribute("data-visible") == "true"
            page.emulate_media(reduced_motion="reduce")
            page.locator("#transition").click()
            assert page.locator("#transition-layer").is_hidden()
            page.locator("#cursor-demo").click()
            assert page.locator("#agent-cursor").is_visible()
            assert not errors, errors
            context.close()
            browser.close()
            print(
                "PASS: all 54 poses, source/SVG comparisons, filters, 3 layouts, "
                "motif playback/cancel, rapid switching, speaking/visibility sequence, "
                "reduced motion and cursor sample; no JS errors."
            )
    finally:
        process.terminate()
        process.wait(timeout=5)
