"""Inspect auto contrast, inward writing poses and retained authored transforms."""

import tempfile
from pathlib import Path

from browser_smoke import start_app
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/design-v5"
OUT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
    process, url = start_app("mock", folder, "http://127.0.0.1:1/v1", ROOT)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
            page = browser.new_page(viewport={"width": 1200, "height": 1100})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(url + "/static/e-preview/runtime-demo.html")
            page.wait_for_selector("#reading-head")
            for role, pose in [
                ("academic", "academic/reading"),
                ("engineering", "engineering/coding"),
                ("business", "business/working"),
            ]:
                page.locator(f'[data-role="{role}"]').click()
                page.locator("#pose").select_option(pose)
                for background in ["dark", "light"]:
                    page.locator("#surface").select_option(background)
                    page.wait_for_function(
                        '(value)=>document.querySelector("#avatar").dataset.contrast===value',
                        arg=background,
                    )
                    if role == "academic":
                        color = "#A17A51" if background == "dark" else "#58402B"
                        page.wait_for_selector(
                            f'#reading-head path[fill="{color}"]', state="attached"
                        )
                    else:
                        page.wait_for_function(
                            """dark=>{const i=document.querySelector('#avatar img');
                            return i?.complete&&i.naturalWidth>0&&
                            i.src.includes('/dark/')===dark;}""",
                            arg=background == "dark",
                        )
                    page.locator(".desktop").screenshot(path=str(OUT / f"{role}-{background}.png"))
            page.locator("#pose").select_option("business/formal-report")
            page.wait_for_function(
                '()=>document.querySelector("#avatar img")?.src.includes("formal-report")'
            )
            assert "paper faces him" in page.locator("#pose-note").inner_text()
            page.locator(".desktop").screenshot(path=str(OUT / "report-inward.png"))
            page.locator("#pose").select_option("business/seated")
            page.wait_for_selector("#business-consistent-head")
            transform = page.locator("#business-consistent-head").get_attribute("transform")
            page.locator("#motion").uncheck()
            assert page.locator("#business-consistent-head").get_attribute("transform") == transform
            page.locator("#motion").check()
            before = page.locator("#seated-moving-hand").get_attribute("transform")
            page.wait_for_function(
                '(old)=>document.querySelector("#seated-moving-hand").getAttribute("transform")!==old',
                arg=before,
            )
            assert page.locator("#business-consistent-head").get_attribute("transform") == transform
            catalog = page.request.get(url + "/api/avatar/catalog").json()
            failed = page.evaluate(
                """async poses=>{
              const failed=[];for(const pose of poses)for(const src of [pose.src,pose.dark_src]){
                const image=new Image();image.src=src;
                try{await image.decode();}catch{failed.push(src);}}
              return failed;
            }""",
                catalog["poses"],
            )
            assert not failed, failed
            page.goto(url)
            page.wait_for_selector("#avatar-contrast")
            page.locator("#profile-select").select_option("engineering")
            page.wait_for_function(
                '()=>document.querySelector("#corner-art").dataset.contrast==="dark"'
            )
            page.locator("#avatar-contrast").select_option("dark")
            page.wait_for_function(
                '()=>document.querySelector("#sidebar-avatar").dataset.contrast==="dark"'
            )
            assert page.request.get(url + "/api/avatar").json()["contrast"] == "dark"
            overlay = browser.new_page()
            overlay.goto(url + "/overlay")
            overlay.wait_for_function(
                '()=>document.querySelector("#overlay-avatar").dataset.contrast==="dark"'
            )
            overlay.locator("#contrast").select_option("light")
            page.wait_for_function('()=>document.querySelector("#avatar-contrast").value==="light"')
            for width, height in [(1440, 1000), (768, 1024), (390, 844)]:
                page.goto(url + "/static/e-preview/runtime-demo.html?pose=business/working")
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_selector("#avatar img")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(OUT / f"layout-{width}.png"), full_page=True)
            assert not errors, errors
            browser.close()
            print(
                "PASS: auto dark/light art, inward clipboard previews, retained head transforms, "
                "256 image decodes, owner/overlay contrast and 3 layouts."
            )
    finally:
        process.terminate()
        process.wait(timeout=5)
