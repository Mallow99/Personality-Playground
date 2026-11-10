"""Check the illustrated proposal gallery in real Chromium with disposable storage."""

import json
import tempfile
from pathlib import Path

from browser_smoke import start_app
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/e-review-images"
OUT.mkdir(parents=True, exist_ok=True)
plan = json.loads((ROOT / "config/pose-review.json").read_text())
with tempfile.TemporaryDirectory(prefix="bfi-review-images-") as folder:
    process, url = start_app("mock", folder, "http://127.0.0.1:1/v1", ROOT)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url + "/static/e-preview/index.html#pose-approval")
            page.wait_for_selector(".review-row")
            assert page.locator(".review-row").count() == 54
            page.locator(".review-row img").evaluate_all("imgs=>imgs.forEach(i=>i.loading='eager')")
            page.wait_for_function(
                "()=>Array.from(document.querySelectorAll('.review-row img'))"
                ".every(i=>i.complete && i.naturalWidth===1536)"
            )
            for proposal in plan["proposals"]:
                row = page.locator(f'[data-review-id="{proposal["code"]}"]')
                assert proposal["reason"] in row.inner_text()
                img = row.locator("img")
                assert img.get_attribute("src") == proposal["image"]["sheet"]
                assert img.evaluate("i=>i.style.left") == (
                    f"-{proposal['image']['column'] * 100}%"
                    if proposal["image"]["column"]
                    else "0%"
                )
                assert img.evaluate("i=>i.style.top") == (
                    f"-{proposal['image']['row'] * 100}%" if proposal["image"]["row"] else "0%"
                )
            for width, height in [(1440, 1000), (768, 1024), (390, 844)]:
                page.set_viewport_size({"width": width, "height": height})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.get_by_role("button", name="Enlarge S01 illustration").click()
                assert page.locator("#review-image-dialog").is_visible()
                assert "S01" in page.locator("#review-image-title").inner_text()
                page.wait_for_function(
                    "()=>document.querySelector('#review-image-frame img').complete"
                )
                page.screenshot(path=str(OUT / f"expanded-{width}.png"))
                page.keyboard.press("Escape")
                assert not page.locator("#review-image-dialog").is_visible()
            page.get_by_label("Decision for S01", exact=True).select_option("skip")
            page.get_by_label("Notes for S01", exact=True).fill("Keep the clear pointing hand.")
            page.reload()
            page.wait_for_selector(".review-row")
            assert page.get_by_label("Decision for S01", exact=True).input_value() == "skip"
            assert "pointing hand" in page.get_by_label("Notes for S01", exact=True).input_value()
            page.locator("#review-filter").select_option("business")
            assert page.locator(".review-row").count() == 10
            page.get_by_role("button", name="Enlarge B10 illustration").click()
            assert "B10" in page.locator("#review-image-title").inner_text()
            assert page.locator("#review-image-frame img").evaluate("i=>i.style.left") == "-200%"
            assert page.locator("#review-image-frame img").evaluate("i=>i.style.top") == "-100%"
            page.locator("#review-image-close").click()
            with page.expect_download() as event:
                page.locator("#review-download").click()
            data = json.loads(Path(event.value.path()).read_text())["decisions"]
            assert len(data) == 54
            assert all(item["illustration"]["sha256"] for item in data)
            assert sum(item["decision"] == "skip" for item in data) == 1
            assert not errors, errors
            browser.close()
            print(
                "PASS: 54 image/reason pairs, cell positions, 3 layouts, modal/keyboard, "
                "saved choices and provenance export; no JS errors."
            )
    finally:
        process.terminate()
        process.wait(timeout=5)
