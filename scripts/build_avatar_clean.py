"""Keep original traces, package runtime copies without detached baseline scraps."""

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "bfi/static"
OUT = STATIC / "avatar/clean"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
manifest = json.loads((STATIC / "e-preview/assets/poses/manifest.json").read_text())
records = []
for role, poses in manifest["characters"].items():
    for pose in poses:
        slug = pose["id"]
        source = STATIC / f"e-preview/assets/poses/{role}/{slug}.svg"
        root = ET.parse(source).getroot()
        removed = []
        for element in root.iter():
            if not element.get("d"):
                continue
            rings = []
            for ring in re.findall(r"M([^MZ]+)Z", element.get("d")):
                points = [tuple(map(float, p.split(","))) for p in ring.strip().split()]
                xs, ys = zip(*points, strict=True)
                area = (
                    abs(
                        sum(
                            x * points[(i + 1) % len(points)][1]
                            - points[(i + 1) % len(points)][0] * y
                            for i, (x, y) in enumerate(points)
                        )
                    )
                    / 2
                )
                tiny_baseline = min(ys) >= 420 and max(ys) - min(ys) <= 14 and area <= 120
                neighbor = role == "engineering" and slug == "tired" and min(xs) >= 470
                if tiny_baseline or neighbor:
                    removed.append(
                        {
                            "bounds": [min(xs), min(ys), max(xs), max(ys)],
                            "reason": "neighbor fragment"
                            if neighbor
                            else "detached baseline scrap",
                        }
                    )
                else:
                    rings.append("M" + ring + "Z")
            element.set("d", "".join(rings))
        destination = OUT / role / f"{slug}.svg"
        destination.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(root).write(destination, encoding="unicode")
        records.append(
            {
                "id": f"{role}/{slug}",
                "src": f"/static/avatar/clean/{role}/{slug}.svg",
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "removed": removed,
            }
        )
(OUT / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")
print(
    f"Packaged {len(records)} runtime traces; "
    f"removed {sum(len(p['removed']) for p in records)} small baseline/neighbor contours. "
    "Originals unchanged."
)
