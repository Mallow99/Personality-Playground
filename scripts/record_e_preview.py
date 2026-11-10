"""Record actual Chromium playback using the installed system FFmpeg, without downloads."""

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
OUT = ROOT / "runs/e-preview-v2/recording"
ASSETS = ROOT / "bfi/static/e-preview/assets"
OUT.mkdir(parents=True, exist_ok=True)
# Select an existing development dependency in task-owned temporary storage.
registry = Path(playwright.__file__).parent / "driver/package/browsers.json"
revision = next(
    b["revision"] for b in json.loads(registry.read_text())["browsers"] if b["name"] == "ffmpeg"
)
local = Path("/tmp/bfi-browser-deps")
helper = local / f"ffmpeg-{revision}" / "ffmpeg-linux"
helper.parent.mkdir(parents=True, exist_ok=True)
if not helper.exists():
    helper.symlink_to(shutil.which("ffmpeg"))
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(local)


def publish_recording(source, name):
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-c:v",
            "libx264",
            "-crf",
            "22",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(ASSETS / name),
        ],
        check=True,
    )


with tempfile.TemporaryDirectory(prefix="bfi-e-record-") as folder:
    process, url = start_app("mock", folder, "http://127.0.0.1:1/v1", ROOT)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
            for kind in ["motif", "character", "rig"]:
                context = browser.new_context(
                    viewport={"width": 1120, "height": 900},
                    record_video_dir=str(OUT / kind),
                    record_video_size={"width": 1120, "height": 900},
                )
                page = context.new_page()
                page.goto(url + "/static/e-preview/index.html")
                page.wait_for_selector("#actor svg")
                if kind == "motif":
                    for role in ["academic", "engineering", "business"]:
                        page.locator(f'button[data-profile="{role}"]').click()
                        page.wait_for_timeout(2500)
                elif kind == "rig":
                    page.locator(".workbench").evaluate("el=>el.scrollIntoView({block:'start'})")
                    page.evaluate(
                        "() => {const el=document.querySelector('#piece-outlines');"
                        "el.checked=true;el.dispatchEvent(new Event('change'));}"
                    )
                    page.evaluate(
                        "() => {const el=document.querySelector('#piece-select');"
                        "el.value='left-hand';el.dispatchEvent(new Event('change'));}"
                    )
                    page.evaluate(
                        "() => {const el=document.querySelector('#piece-x');"
                        "el.value=25;el.dispatchEvent(new Event('input'));}"
                    )
                    page.wait_for_timeout(1000)
                    page.evaluate("() => document.querySelector('#piece-reset').click()")
                    page.locator("#stage-pose").select_option("seated")
                    page.wait_for_timeout(1600)
                    page.locator("#pose-transition").select_option("morph")
                    page.locator("#stage-pose").select_option("standing")
                    page.wait_for_timeout(1600)
                    page.locator("#pose-transition").select_option("turn")
                    page.locator("#stage-pose").select_option("seated")
                    page.locator("#speaking").click()
                    page.wait_for_timeout(1600)
                else:
                    page.locator(".workbench").evaluate("el=>el.scrollIntoView({block:'start'})")
                    page.locator("#sequence").click()
                    page.wait_for_timeout(14500)
                video = page.video
                context.close()
                publish_recording(video.path(), kind + "-reel.mp4")
            browser.close()
        print("Recorded actual browser motifs and character sequence, at native playback timing.")
    finally:
        process.terminate()
        process.wait(timeout=5)
