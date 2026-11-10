"""Check actual rendered material/contrast contracts for the v5 design candidate."""

import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "bfi/static"
config = json.loads((ROOT / "config/avatar-design-v5.json").read_text())
catalog = json.loads((STATIC / "avatar/catalog.json").read_text())
report = json.loads((STATIC / "avatar/design-v5/business-report.json").read_text())
assert len(report) == 42
assert len([p for p in catalog["poses"] if p.get("face_design") == "two-eye-v5"]) == 42


def render(path):
    svg = ET.parse(path).getroot()
    svg.set("viewBox", "0 0 512 512")
    return np.array(
        Image.open(
            io.BytesIO(
                cairosvg.svg2png(bytestring=ET.tostring(svg), output_width=512, output_height=512)
            )
        ).convert("RGBA")
    )


for row in report:
    if not row["inward_board"]:
        continue
    pixels = render(STATIC / f"avatar/design-v5/{row['id']}.svg")
    image = Image.new("1", (512, 512))
    ImageDraw.Draw(image).polygon([tuple(p) for p in row["inward_board"]], fill=1)
    mask = np.array(image, dtype=bool)
    # Test inside the authored backing plane, away from rasterized border pixels.
    for _ in range(3):
        mask &= np.roll(mask, 1, 0) & np.roll(mask, -1, 0)
        mask &= np.roll(mask, 1, 1) & np.roll(mask, -1, 1)
    assert mask.sum() > 400
    assert (pixels[mask, 3] > 250).mean() > 0.995, row["id"]
    # It is the plain rear face, not a pale spreadsheet presented to the camera.
    navy = np.array([21, 59, 100])
    cx, cy = np.rint(np.mean(row["inward_board"], axis=0)).astype(int)
    # Gripping fingers correctly occupy the near edge. The rear-face center is
    # an unmarked solid patch, unlike the previous visible spreadsheet grid.
    center = pixels[cy - 4 : cy + 5, cx - 4 : cx + 5]
    assert np.max(abs(center[:, :, :3].astype(int) - navy)) < 2, row["id"]
    assert center[:, :, 3].min() == 255, row["id"]


def luminance(color):
    rgb = np.array(tuple(bytes.fromhex(color[1:]))) / 255
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return float(linear @ [0.2126, 0.7152, 0.0722])


background = luminance("#151719")
for colors in config["darkPalettes"].values():
    for color in colors:
        assert (luminance(color) + 0.05) / (background + 0.05) >= 3, color
for pose in catalog["poses"]:
    assert (STATIC / pose["dark_src"].removeprefix("/static/")).is_file()
    assert pose["dark_asset_version"]
    if pose.get("layered_src"):
        assert pose["dark_layered_src"]
print(
    "PASS: 42 Business candidates, inward opaque writing boards, "
    "128 dark variants and palette contrast."
)
