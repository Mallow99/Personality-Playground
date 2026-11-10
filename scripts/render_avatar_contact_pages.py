"""Render all runtime poses into twelve inspectable role contact pages."""

import io
import json
import math
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
static = root / "bfi/static"
out = root / "runs/visual-review"
out.mkdir(parents=True, exist_ok=True)
poses = json.loads((static / "avatar/catalog.json").read_text())["poses"]
for role in ["academic", "engineering", "business"]:
    rows = [p for p in poses if p["role"] == role]
    for page in range(math.ceil(len(rows) / 12)):
        canvas = Image.new("RGB", (1200, 900), "#b6acaf")
        draw = ImageDraw.Draw(canvas)
        for cell, p in enumerate(rows[page * 12 : (page + 1) * 12]):
            path = static / p.get("layered_src", p["src"]).removeprefix("/static/")
            if path.suffix == ".svg":
                image = Image.open(
                    io.BytesIO(cairosvg.svg2png(url=str(path), output_width=512, output_height=512))
                ).convert("RGBA")
            else:
                image = Image.open(path).convert("RGBA")
            image.thumbnail((290, 265))
            x = cell % 4 * 300
            y = cell // 4 * 300
            canvas.paste(image, (x + (300 - image.width) // 2, y), image)
            draw.text((x + 5, y + 270), p["id"], fill="#111111")
        canvas.save(out / f"{role}-{page + 1}.jpg")
print("Review pages:", len(list(out.glob("*.jpg"))))
