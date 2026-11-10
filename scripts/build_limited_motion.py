"""Group intact contours from one reading pose for a limited movement example."""

import hashlib
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import numpy as np
from build_e_rigs import NS, PALETTES, geometry, to_path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "bfi/static/e-preview/assets"
source = ASSETS / "poses/academic/reading.svg"
root = ET.parse(source).getroot()
svg = ET.Element(f"{{{NS}}}svg", {"viewBox": "90 90 330 370", "role": "img"})
ET.SubElement(
    svg, f"{{{NS}}}title"
).text = "Academic reading, with limited head, book and hand movement"
body = ET.SubElement(svg, f"{{{NS}}}g", {"id": "fixed-body", "data-motion": "fixed"})
head = ET.SubElement(svg, f"{{{NS}}}g", {"id": "reading-head"})
held = ET.SubElement(svg, f"{{{NS}}}g", {"id": "held-book"})
book = ET.SubElement(held, f"{{{NS}}}g", {"id": "book-pages"})
right = ET.SubElement(held, f"{{{NS}}}g", {"id": "reading-right-hand"})
left = ET.SubElement(held, f"{{{NS}}}g", {"id": "reading-left-hand"})
counts = dict(body=0, head=0, book=0, right=0, left=0)
for ci, color in enumerate(PALETTES["academic"]):
    art = next(geometry(p.get("d")) for p in root if p.get("fill") == color)
    polygons = [art] if art.geom_type == "Polygon" else list(art.geoms)
    for rank, polygon in enumerate(sorted(polygons, key=lambda p: -p.area)):
        c = polygon.representative_point()
        name, group = "body", body
        if ci == 0 and rank == 4:
            name, group = "right", right
        elif ci == 0 and rank == 5:
            name, group = "left", left
        elif 170 <= c.x <= 325 and 105 <= c.y <= 231:
            name, group = "head", head
        elif (ci == 1 and rank == 0) or (185 <= c.x <= 330 and 280 <= c.y <= 370):
            name, group = "book", book
        counts[name] += 1
        ET.SubElement(
            group,
            f"{{{NS}}}path",
            {
                "d": to_path(polygon),
                "fill": color,
                "fill-rule": "evenodd",
                "data-source-form": f"c{ci}-{rank}",
            },
        )
path = ASSETS / "reading-limited.svg"
ET.ElementTree(svg).write(path, encoding="unicode")
# Compare at the source canvas before viewport cropping, with all transforms at rest.
svg.set("viewBox", "0 0 512 512")
a = (
    np.array(
        Image.open(
            io.BytesIO(cairosvg.svg2png(url=str(source), output_width=512, output_height=512))
        ).convert("RGBA")
    )[:, :, 3]
    > 127
)
b = (
    np.array(
        Image.open(
            io.BytesIO(
                cairosvg.svg2png(bytestring=ET.tostring(svg), output_width=512, output_height=512)
            )
        ).convert("RGBA")
    )[:, :, 3]
    > 127
)
overlap = float((a & b).sum() / (a | b).sum())
assert overlap >= 0.9999, overlap
report = {
    "source": "poses/academic/reading.svg",
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "assembly_iou": overlap,
    "method": "whole connected source contours; no anatomical region slicing",
    "source_form_counts": counts,
    "fixed": ["torso", "sleeves", "legs"],
    "animated": ["head", "book and attached hands", "small local grip adjustments"],
}
(ASSETS / "reading-limited.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"Limited reading example: {overlap:.6%} silhouette overlap at rest; body stays fixed.")
