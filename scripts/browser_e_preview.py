"""Exercise the E proof in a real Chromium against the local BFI app.

uv run --locked --group browser python scripts/browser_e_preview.py
"""

import json
import tempfile
from pathlib import Path

from browser_smoke import start_app
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/e-preview-v3"
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
            page.goto(url + "/static/e-preview/mapping-lab.html")
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
                assert page.locator("#pose option").count() == len(items)
                for item in items:
                    page.locator("#pose").select_option(item["id"])
                    page.wait_for_function(
                        '(id)=>document.querySelector("#actor svg").dataset.pose===id',
                        arg=item["id"],
                    )
                    page.wait_for_function(
                        '() => Array.from(document.querySelectorAll("#comparison-box img"))'
                        ".every(i=>i.complete && i.naturalWidth>0)"
                    )
                page.locator("#pose").select_option("seated")
                page.wait_for_function(
                    '() => document.querySelector("#actor svg").dataset.pose==="seated"'
                )
                page.locator("#pose-filter").select_option("all")
                assert page.locator("#pose-grid figure:visible").count() == len(items)
                page.locator("#pose-filter").select_option("everyday")
                assert page.locator("#pose-grid figure:visible").count() == sum(
                    p["category"] == "everyday" for p in items
                )
                page.locator("#comparison-mode").select_option("vector")
                page.locator("#actor").screenshot(path=str(OUT / f"{role}-seated.png"))
                page.locator("#fidelity").screenshot(path=str(OUT / f"{role}-comparison.png"))
            assert "adult studies" not in page.locator("body").inner_text().lower()
            assert page.locator(".review-row").count() == 54
            page.get_by_label("Decision for S01", exact=True).select_option("keep")
            page.get_by_label("Notes for S01", exact=True).fill("clear extended hand")
            page.reload()
            page.wait_for_selector("#actor svg")
            assert page.get_by_label("Decision for S01", exact=True).input_value() == "keep"
            with page.expect_download() as export:
                page.locator("#review-download").click()
            decisions = json.loads(Path(export.value.path()).read_text())["decisions"]
            assert len(decisions) == 54
            assert sum(d["decision"] == "keep" for d in decisions) == 1
            assert sum(d["decision"] == "unreviewed" for d in decisions) == 53
            page.locator("#motion").uncheck()
            page.locator("#speaking").click()
            assert page.locator("#actor .speech-marks").is_visible()
            assert "Talking" in page.locator("#talk-status").inner_text()
            page.locator("#talk-mode").select_option("gestures")
            assert not page.locator("#actor .speech-marks").is_visible()
            page.locator("#talk-mode").select_option("both")
            page.locator("#speaking").click()
            assert page.locator('#actor svg[data-whole-shapes="true"]').count() == 1
            assert page.locator('#actor [data-shape="c0-3"]').count() == 1
            page.locator("#piece-drag").check()
            page.locator("#form-drag").check()
            page.locator('#actor [data-shape="c0-3"]').scroll_into_view_if_needed()
            point = page.locator('#actor [data-shape="c0-3"]').evaluate("""p=>{
                const b=p.getBBox();
                for(let x=1;x<10;x++)for(let y=1;y<10;y++){
                    const q=new DOMPoint(b.x+b.width*x/10,b.y+b.height*y/10);
                    if(p.isPointInFill(q)){const r=q.matrixTransform(p.getScreenCTM());
                        return {x:r.x,y:r.y};}
                }
            }""")
            assert point
            page.mouse.move(point["x"], point["y"])
            page.mouse.down()
            page.mouse.move(point["x"] + 14, point["y"] + 6, steps=4)
            page.mouse.up()
            assert "translate(" in page.locator('#actor [data-shape="c0-3"]').get_attribute(
                "transform"
            )
            assert "translate(0 0)" in page.locator('#actor [data-part="left-hand"]').get_attribute(
                "transform"
            )
            page.locator("#piece-reset").click()
            page.locator("#form-drag").uncheck()
            page.locator("#piece-drag").uncheck()
            page.locator("#motion").check()
            page.locator("#mapping-pair").click()
            page.wait_for_function(
                '() => document.querySelector("#actor").dataset.transitioning==="false" && '
                'document.querySelector("#actor").dataset.pose==="seated"'
            )
            page.locator("#actor").screenshot(path=str(OUT / "whole-shapes-seated.png"))
            page.locator("#pose-transition").select_option("morph")
            page.locator("#mapping-pair").click()
            page.wait_for_function(
                '() => document.querySelector("#actor").dataset.transitioning==="false" && '
                'document.querySelector("#actor").dataset.pose==="standing"'
            )
            page.locator("#pose-transition").select_option("still")
            page.locator("#mapping-pair").click()
            page.wait_for_function('() => document.querySelector("#actor").dataset.pose==="seated"')
            page.locator("#pose-transition").select_option("turn")
            page.locator("#motion").uncheck()
            page.locator('[data-profile="business"]').click()
            page.wait_for_function(
                '() => document.querySelector("#actor").dataset.profile==="business"'
            )
            page.locator("#pose").select_option("seated")
            page.wait_for_function('() => document.querySelector("#actor").dataset.pose==="seated"')
            assert page.locator("#actor [data-part]").count() == 17
            page.locator("#piece-select").select_option("left-hand")
            page.locator("#piece-x").evaluate(
                "el=>{el.value='12';el.dispatchEvent(new Event('input'));}"
            )
            assert "translate(12 0)" in page.locator(
                '#actor [data-part="left-hand"]'
            ).get_attribute("transform")
            assert "translate(0 0)" in page.locator(
                '#actor [data-part="right-hand"]'
            ).get_attribute("transform")
            page.locator("#piece-reset").click()
            page.locator("#piece-outlines").check()
            page.locator("#actor").screenshot(path=str(OUT / "mapped-pieces.png"))
            page.locator("#piece-outlines").uncheck()
            page.locator("#piece-drag").check()
            page.locator("#actor").scroll_into_view_if_needed()
            point = page.locator('#actor [data-part="left-hand"]').evaluate("""g=>{
                for(const p of g.querySelectorAll('path')){
                  if(!p.getAttribute('d'))continue;const b=p.getBBox();
                  for(let x=1;x<10;x++)for(let y=1;y<10;y++){
                    const point=new DOMPoint(b.x+b.width*x/10,b.y+b.height*y/10);
                    if(p.isPointInFill(point)){
                      const q=point.matrixTransform(p.getScreenCTM());return {x:q.x,y:q.y};
                    }
                  }
                }
                return null;
            }""")
            assert point
            page.mouse.move(point["x"], point["y"])
            page.mouse.down()
            page.mouse.move(point["x"] + 18, point["y"] + 8, steps=5)
            page.mouse.up()
            assert page.locator("#piece-select").input_value() == "left-hand"
            assert "translate(0 0)" not in page.locator(
                '#actor [data-part="left-hand"]'
            ).get_attribute("transform")
            page.locator("#piece-drag").uncheck()
            page.locator("#piece-reset").click()
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
                '() => ["academic","engineering","business"].forEach(id=>'
                "document.querySelector(`[data-profile=${id}]`).click())"
            )
            page.wait_for_function(
                '() => document.querySelector("#actor").dataset.profile==="business"'
            )
            page.keyboard.press("Escape")
            page.locator("#pose").select_option("standing-2")
            page.wait_for_function(
                '() => document.querySelector("#actor").dataset.transitioning==="true"'
            )
            page.locator("#actor").screenshot(path=str(OUT / "morph-midpoint.png"))
            page.wait_for_function(
                '() => document.querySelector("#actor").dataset.transitioning==="false"'
            )
            assert page.locator('#actor [data-part="left-hand"]').count() == 1
            page.locator("#piece-select").select_option("left-hand")
            page.locator("#piece-x").evaluate(
                "el=>{el.value='16';el.dispatchEvent(new Event('input'));}"
            )
            page.locator("#stage-pose").select_option("greeting")
            page.wait_for_function(
                '() => document.querySelector("#actor").dataset.pose==="greeting" && '
                'document.querySelector("#actor").dataset.transitioning==="false"'
            )
            assert page.locator("#pose").input_value() == "greeting"
            assert "translate(16 0)" in page.locator(
                '#actor [data-part="left-hand"]'
            ).get_attribute("transform")
            assert "translate(0 0)" in page.locator(
                '#actor [data-part="right-hand"]'
            ).get_attribute("transform")
            assert (
                page.locator('#actor [data-part="head"] .piece-motion').evaluate(
                    "el=>getComputedStyle(el).animationName"
                )
                == "piece-breathe"
            )
            page.locator("#piece-reset").click()
            page.locator("#sequence").click()
            page.wait_for_function(
                '() => document.querySelector("#actor").classList.contains("speaking")'
            )
            page.wait_for_function(
                '() => document.querySelector("#actor").dataset.visible==="false"', timeout=18000
            )
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
                "PASS: all 74 poses, source/SVG comparisons, filters, 3 layouts, "
                "piece selection/dragging, persistent hand offsets, pose morphing, "
                "motif playback/cancel, rapid switching, speaking/visibility sequence, "
                "reduced motion and cursor sample; no JS errors."
            )
    finally:
        process.terminate()
        process.wait(timeout=5)
