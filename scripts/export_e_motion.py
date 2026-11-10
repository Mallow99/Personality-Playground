"""Export a vector motion sketch, not a browser recording.

Run with: UV_CACHE_DIR=/tmp/bfi-uv-cache uv run --with cairosvg python scripts/export_e_motion.py
"""

import io
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1] / "bfi/static/e-preview/assets"
FONT_FILE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
FONT = ImageFont.truetype(str(FONT_FILE), 13) if FONT_FILE.exists() else ImageFont.load_default()
frames = []
for index in range(96):
    seconds = index / 8
    pose = (
        "standing"
        if seconds < 1.8
        else "chalkboard"
        if seconds < 6.5
        else "thinking"
        if seconds < 8.5
        else "seated"
    )
    svg = (ROOT / "poses/academic" / f"{pose}.svg").read_text()
    speaking = 3 <= seconds < 6.5
    image = Image.open(
        io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=360, output_height=360))
    ).convert("RGBA")
    opacity = min(1, seconds / 0.5, max(0, (12 - seconds) / 0.5))
    image.putalpha(
        image.getchannel("A").point(lambda alpha, opacity=opacity: round(alpha * opacity))
    )
    frame = Image.new("RGB", (420, 640), "#f6f0e5")
    frame.paste(image, (30, 125), image)
    draw = ImageDraw.Draw(frame)
    draw.text((20, 16), "ACADEMIC / E — VECTOR MOTION SKETCH", fill="#58402B", font=FONT)
    label = "Speaking gesture · no audio" if speaking else pose.capitalize()
    draw.text((20, 588), label, fill="#58402B", font=FONT)
    draw.text((20, 613), "Exported SVG frames; not a screen recording.", fill="#58402B", font=FONT)
    frames.append(frame)
frames[0].save(
    ROOT / "academic-motion.gif",
    save_all=True,
    append_images=frames[1:],
    duration=125,
    loop=0,
    optimize=True,
)
print("Exported 12-second Academic SVG motion sketch.")
