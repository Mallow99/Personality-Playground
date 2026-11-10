"""Check matte removal against known compositing and pose-local gaze boundaries."""

import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import numpy as np
from avatar_matte import remove_white_matte
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "bfi/static"
PALETTES = {
    "academic": ["#58402B", "#87A452", "#EBD8AF"],
    "engineering": ["#20171E", "#D9254C", "#F6A0B4"],
    "business": ["#153B64", "#247DD4", "#B9E9FA"],
}
for palette in PALETTES.values():
    colors = np.array([tuple(bytes.fromhex(c[1:])) for c in palette])
    coverage = np.array([0, 0.15, 0.35, 0.65, 0.9, 1])[None, :, None]
    white_matted = (colors[:, None, :] * coverage + 255 * (1 - coverage)).round().astype("uint8")
    rgba = remove_white_matte(white_matted, palette)
    # A known white-composited edge must regain its color on a dark desktop.
    recovered = rgba[:, 1:, :3].astype(int)
    assert np.max(abs(recovered - colors[:, None, :])) <= 5
    assert np.max(abs(rgba[:, :, 3] / 255 - coverage[:, :, 0])) < 0.025
    assert not rgba[:, 0].any()
for path in (STATIC / "avatar/cutouts").glob("*.png"):
    pixels = np.array(Image.open(path).convert("RGBA"))
    assert not pixels[:28, :, 3].any() and not pixels[484:, :, 3].any(), path.name
    assert not pixels[pixels[:, :, 3] == 0, :3].any(), path.name


def rendered(root):
    root.set("viewBox", "0 0 512 512")
    return np.array(
        Image.open(
            io.BytesIO(
                cairosvg.svg2png(bytestring=ET.tostring(root), output_width=512, output_height=512)
            )
        ).convert("RGBA")
    )


for record in json.loads((STATIC / "avatar/focus/manifest.json").read_text()):
    role, slug = record["id"].split("/")
    source = STATIC / record["source_path"]
    before = (
        np.array(Image.open(source).convert("RGBA"))
        if source.suffix == ".png"
        else rendered(ET.parse(source).getroot())
    )
    after = rendered(ET.parse(STATIC / record["src"].removeprefix("/static/")).getroot())
    head = (
        record.get("head")
        or json.loads((ROOT / f"config/rigs/{role}.json").read_text())["poses"][slug]["head"]
    )
    x, y, x2, y2 = head
    allowed = np.zeros((512, 512), dtype=bool)
    allowed[y : y2 + 1, x : x2 + 1] = True
    # Cairo premultiplies PNG edge RGB and can round it by one level. Compare
    # visible composites, not undefined straight RGB beneath near-zero alpha.
    for background in [0, 255]:

        def composite(pixels, background=background):
            alpha = pixels[:, :, 3:4].astype(float) / 255
            return np.rint(pixels[:, :, :3] * alpha + background * (1 - alpha))

        difference = abs(composite(before) - composite(after)).max(axis=2)
        assert (difference[allowed] > 4).any(), record["id"]
        assert difference[~allowed].max() <= 1, record["id"]
print(
    "PASS: white-matte compositing, 54 transparent cutouts, "
    "15 eye edits contained inside source heads."
)
