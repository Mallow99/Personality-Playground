"""Verify visible control outcomes, not just state attributes, in the shared demo."""

import tempfile
from pathlib import Path

from browser_smoke import start_app
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/edge-fix"
OUT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
    process, url = start_app("mock", folder, "http://127.0.0.1:1/v1", ROOT)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
            page = browser.new_page(viewport={"width": 1200, "height": 1100})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            pending = []
            page.route("**/focus/academic/reading.svg*", lambda route: pending.append(route))
            page.goto(url + "/static/e-preview/runtime-demo.html", wait_until="domcontentloaded")
            page.wait_for_function('()=>!document.querySelector("#pose").disabled')
            page.locator("#motion").uncheck()
            page.locator("#reply").click()
            assert pending
            pending[0].continue_()
            page.locator("#reveal").wait_for(state="visible")
            page.unroute("**/focus/academic/reading.svg*")
            page.locator("#show").click()
            assert not page.locator("#avatar").is_visible()
            assert "hidden" in page.locator("#example").inner_text()
            page.locator("#show").click()
            assert page.locator("#avatar").is_visible()
            page.locator("#reveal").click()
            assert (
                page.locator("#reading-left-hand").evaluate("e=>getComputedStyle(e).visibility")
                == "hidden"
            )
            assert not page.locator("#motion").is_checked()
            page.locator("#reveal").click()
            assert (
                page.locator("#reading-left-hand").evaluate("e=>getComputedStyle(e).visibility")
                == "visible"
            )
            page.locator("#motion").check()
            before = page.locator("#held-book").get_attribute("transform")
            page.wait_for_function(
                '(old)=>document.querySelector("#held-book").getAttribute("transform")!==old',
                arg=before,
            )
            page.locator("#motion").uncheck()
            assert page.locator("#held-book").get_attribute("transform") is None
            for role, default in [
                ("academic", "reading"),
                ("engineering", "coding"),
                ("business", "working"),
            ]:
                page.locator(f'[data-role="{role}"]').click()
                page.wait_for_function(
                    '(id)=>document.querySelector("#avatar").dataset.pose===id',
                    arg=f"{role}/{default}",
                )
                assert "Eyes toward" in page.locator("#pose-note").inner_text()
                page.locator("#think").click()
                assert page.locator("#avatar").get_attribute("data-pose") == f"{role}/thinking"
                assert page.locator(".avatar-status").inner_text().startswith("Thinking")
                assert not page.locator("#reveal").is_visible()
                page.locator("#reply").click()
                assert page.locator(".avatar-voice").is_visible()
                assert "8 seconds" in page.locator("#example").inner_text()
                page.locator("#idle").click()
                assert not page.locator(".avatar-voice").is_visible()
                for surface in ["light", "dark", "studio", "theme"]:
                    page.locator("#surface").select_option(surface)
                    assert page.locator(".desktop").get_attribute("data-surface") == surface
                page.locator("#pose").select_option(f"{role}/standing")
                page.wait_for_function(
                    '(id)=>document.querySelector("#avatar").dataset.pose===id',
                    arg=f"{role}/standing",
                )
                assert "Still artwork" in page.locator("#pose-note").inner_text()
                if role != "engineering":
                    page.locator("#animate-example").click()
                    page.locator("#reveal").wait_for(state="visible")
                    assert "Separate parts" in page.locator("#pose-note").inner_text()
            for role, pose in [
                ("academic", "academic/reading"),
                ("engineering", "engineering/H04"),
                ("business", "business/formal-report"),
            ]:
                page.locator(f'[data-role="{role}"]').click()
                page.locator("#pose").select_option(pose)
                for surface in ["light", "dark", "studio"]:
                    page.locator("#surface").select_option(surface)
                    page.locator(".desktop").screenshot(path=str(OUT / f"{role}-{surface}.png"))
                assert (
                    page.locator(".avatar-art > :first-child").evaluate(
                        "e=>getComputedStyle(e).filter"
                    )
                    == "none"
                )
            for width, height in [(1440, 1000), (768, 1024), (390, 844)]:
                page.set_viewport_size({"width": width, "height": height})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.locator("#show").click()
                assert not page.locator("#avatar").is_visible()
                page.locator("#show").click()
                assert page.locator("#avatar").is_visible()
                page.screenshot(path=str(OUT / f"controls-{width}.png"), full_page=True)
            page.goto(url + "/static/e-preview/art-review.html")
            page.wait_for_function('()=>document.querySelectorAll(".card").length===128')
            failures = page.evaluate("""async()=>{
                const rows=[...document.querySelectorAll('.packaged')];
                return (await Promise.all(rows.map(async img=>{
                    const probe=new Image();probe.src=img.src;
                    try{await probe.decode();return null;}catch{return img.src;}
                }))).filter(Boolean);
            }""")
            assert not failures, failures
            page.locator("#role").select_option("engineering")
            page.locator("#search").fill("flirty")
            assert page.locator(".card:visible").count() == 1
            assert "Both complete arms" in page.locator(".card:visible").inner_text()
            page.locator(".card:visible").screenshot(path=str(OUT / "flirty-repaired.png"))
            page.locator("#source").check()
            assert page.locator(".card:visible .original").is_visible()
            assert not page.locator(".card:visible .packaged").is_visible()
            page.locator("#source").uncheck()
            for background in ["dark", "light", "studio"]:
                page.locator("#background").select_option(background)
                assert page.locator("body").get_attribute("data-background") == background
            page.locator("#role").select_option("all")
            page.locator("#search").fill("")
            assert page.locator(".card:visible").count() == 128
            for width in [1440, 768, 390]:
                page.set_viewport_size({"width": width, "height": 1000})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.locator("#role").select_option("engineering")
            page.locator("#search").fill("flirty")
            page.screenshot(path=str(OUT / "review-phone.png"), full_page=True)
            reduced = browser.new_context(reduced_motion="reduce")
            reduced_page = reduced.new_page()
            reduced_page.goto(url + "/static/e-preview/runtime-demo.html")
            reduced_page.wait_for_selector("#reading-head")
            assert reduced_page.locator("#motion").is_disabled()
            assert "reduced-motion" in reduced_page.locator("#pose-note").inner_text()
            assert reduced_page.locator("#held-book").get_attribute("transform") is None
            reduced.close()
            assert not errors, errors
            browser.close()
            print(
                "PASS: real hide/show, delayed-art readiness, pose/role/thinking/reply/idle, "
                "movement, reveal, backgrounds, 128-pose review/source comparison and 3 layouts."
            )
    finally:
        process.terminate()
        process.wait(timeout=5)
