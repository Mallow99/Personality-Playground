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
from shapely.geometry import Polygon
from shapely.ops import unary_union

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
hand_shapes = []
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
        if name in {"left", "right"}:
            hand_shapes.append(polygon)
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
# Restore the page material hidden by the original hands. These authored page
# silhouettes define the real rear surface; moving the hand must reveal olive,
# not its own empty silhouette. The patch is painted UNDER the existing hands.
page_surface = unary_union(
    [
        Polygon([(184, 270), (255, 300), (257, 371), (189, 345)]),
        Polygon([(261, 300), (331, 270), (321, 347), (260, 371)]),
    ]
)
underlap = unary_union(hand_shapes).buffer(3).intersection(page_surface)
ET.SubElement(
    book,
    f"{{{NS}}}path",
    {
        "id": "restored-book-under-hands",
        "d": to_path(underlap),
        "fill": PALETTES["academic"][1],
        "fill-rule": "evenodd",
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
assert overlap >= 0.995, overlap
report = {
    "source": "poses/academic/reading.svg",
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "assembly_iou": overlap,
    "method": "whole contours plus authored rear-page geometry beneath hands",
    "occlusion": {
        "front": ["reading-left-hand", "reading-right-hand"],
        "rear": "book-pages",
        "restored": "restored-book-under-hands",
        "underlap_area": round(underlap.area, 3),
    },
    "source_form_counts": counts,
    "fixed": ["torso", "sleeves", "legs"],
    "animated": ["head", "book and attached hands", "small local grip adjustments"],
}
(ASSETS / "reading-limited.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"Limited reading example: {overlap:.6%} silhouette overlap at rest; body stays fixed.")

# A second contact case: the Business character's hand rests on the crossed thigh.
# Restore the rear trouser material before permitting any local hand motion.
source_business = ASSETS / "poses/business/seated.svg"
original_business = ET.parse(source_business).getroot()
layered = ET.Element(f"{{{NS}}}svg", {"viewBox": "90 70 340 410", "role": "img"})
ET.SubElement(
    layered, f"{{{NS}}}title"
).text = "Business seated: complete rear thigh beneath moving hand"
fixed = ET.SubElement(layered, f"{{{NS}}}g", {"id": "seated-fixed-body"})
rear = ET.SubElement(layered, f"{{{NS}}}g", {"id": "seated-rear-thigh"})
hand = ET.SubElement(layered, f"{{{NS}}}g", {"id": "seated-moving-hand"})
hand_geometry = None
for ci, color in enumerate(PALETTES["business"]):
    geom = next(geometry(p.get("d")) for p in original_business if p.get("fill") == color)
    polygons = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    for rank, polygon in enumerate(sorted(polygons, key=lambda p: -p.area)):
        target = hand if ci == 2 and rank == 3 else fixed
        if target is hand:
            hand_geometry = polygon
        ET.SubElement(
            target, f"{{{NS}}}path", {"d": to_path(polygon), "fill": color, "fill-rule": "evenodd"}
        )
assert hand_geometry is not None
thigh_surface = Polygon(
    [(205, 329), (240, 286), (291, 274), (320, 286), (297, 310), (260, 335), (207, 353)]
)
restored = hand_geometry.buffer(3).intersection(thigh_surface)
ET.SubElement(
    rear,
    f"{{{NS}}}path",
    {
        "id": "restored-thigh-under-hand",
        "d": to_path(restored),
        "fill": PALETTES["business"][0],
        "fill-rule": "evenodd",
    },
)
ET.ElementTree(layered).write(ASSETS / "business-seated-layered.svg", encoding="unicode")
(ASSETS / "business-seated-layered.json").write_text(
    json.dumps(
        {
            "source": "poses/business/seated.svg",
            "source_sha256": hashlib.sha256(source_business.read_bytes()).hexdigest(),
            "front": "seated-moving-hand",
            "rear": "seated-rear-thigh",
            "restored_area": round(restored.area, 3),
            "fixed": ["torso", "arms", "legs"],
            "motion": "small hand rotation only",
        },
        indent=2,
    )
    + "\n"
)

# Hidden-surface checks: remove the fronts and inspect the material they cover.
for tree, ids, points, color in [
    (svg, ["reading-left-hand", "reading-right-hand"], [(202, 325), (315, 325)], (135, 164, 82)),
    (layered, ["seated-moving-hand"], [(240, 298)], (21, 59, 100)),
]:
    check = ET.fromstring(ET.tostring(tree))
    check.set("viewBox", "0 0 512 512")
    for element in check.iter():
        if element.get("id") in ids:
            element.set("visibility", "hidden")
    pixels = np.array(
        Image.open(
            io.BytesIO(
                cairosvg.svg2png(bytestring=ET.tostring(check), output_width=512, output_height=512)
            )
        ).convert("RGBA")
    )
    for x, y in points:
        assert (
            pixels[y, x, 3] > 250 and max(abs(pixels[y, x, :3].astype(int) - np.array(color))) < 3
        ), (x, y, pixels[y, x])
print("Rear-material checks passed with front hands removed.")
