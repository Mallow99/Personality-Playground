"""Author small work-directed eyes while preserving source bodies and silhouettes."""

import base64
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from build_e_rigs import NS, PALETTES, geometry, to_path
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "bfi/static"
OUT = STATIC / "avatar/focus"


def build_focus():
    config = json.loads((ROOT / "config/avatar-focus.json").read_text())
    records = []
    for pose in config["poses"]:
        role, slug = pose["id"].split("/")
        source = (
            STATIC / f"avatar/cutouts/{pose['cutout']}.png"
            if pose.get("cutout")
            else STATIC / "e-preview/assets/reading-limited.svg"
            if pose.get("layered")
            else STATIC / f"avatar/clean/{role}/{slug}.svg"
        )
        if pose.get("cutout"):
            root = ET.Element(f"{{{NS}}}svg", {"viewBox": "0 0 512 512", "role": "img"})
            ET.SubElement(
                root,
                f"{{{NS}}}image",
                {
                    "width": "512",
                    "height": "512",
                    "href": "data:image/png;base64,"
                    + base64.b64encode(source.read_bytes()).decode(),
                },
            )
        else:
            root = ET.parse(source).getroot()
        parent = (
            next(e for e in root.iter() if e.get("id") == "reading-head")
            if pose.get("layered")
            else root
        )
        defs = ET.SubElement(root, f"{{{NS}}}defs")
        edits = ET.SubElement(parent, f"{{{NS}}}g", {"id": "work-directed-eyes"})
        for index, eye in enumerate(pose["eyes"]):
            if "aperture" in eye:
                aperture = Polygon(eye["aperture"])
            else:
                # Fill just the existing light aperture's exterior, including its old
                # pupil holes, before adding a new iris. No generic face replacement.
                color = PALETTES[role][eye["color"]]
                shapes = [
                    geometry(e.get("d"))
                    for e in parent.iter()
                    if e.get("fill") == color and e.get("d")
                ]
                candidates = []
                x, y, x2, y2 = eye["bounds"]
                for shape in shapes:
                    for polygon in [shape] if shape.geom_type == "Polygon" else shape.geoms:
                        px, py = polygon.representative_point().coords[0]
                        if x <= px <= x2 and y <= py <= y2 and polygon.area > 20:
                            candidates.append(polygon)
                assert candidates, pose["id"]
                aperture = Polygon(max(candidates, key=lambda p: p.area).exterior)
            clip_id = f"work-eye-{index}"
            clip = ET.SubElement(defs, f"{{{NS}}}clipPath", {"id": clip_id})
            ET.SubElement(clip, f"{{{NS}}}path", {"d": to_path(aperture)})
            ET.SubElement(
                edits, f"{{{NS}}}path", {"d": to_path(aperture), "fill": PALETTES[role][2]}
            )
            ET.SubElement(
                edits,
                f"{{{NS}}}path",
                {
                    "d": to_path(Polygon(eye["pupil"])),
                    "fill": PALETTES[role][0],
                    "clip-path": f"url(#{clip_id})",
                },
            )
        path = OUT / role / f"{slug}.svg"
        path.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(root).write(path, encoding="unicode")
        records.append(
            {
                "id": pose["id"],
                "target": pose["target"],
                "source_path": str(source.relative_to(STATIC)),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "src": f"/static/avatar/focus/{role}/{slug}.svg",
                "original_src": (
                    f"/static/avatar/cutouts/{pose['cutout']}.png"
                    if pose.get("cutout")
                    else f"/static/e-preview/assets/poses/{role}/{slug}.svg"
                ),
                "layered": pose.get("layered", False),
                "head": pose.get("head"),
                "asset_version": hashlib.sha256(path.read_bytes()).hexdigest()[:12],
            }
        )
    (OUT / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")
    print(f"Built {len(records)} pose-local work-directed eye variants; originals retained.")
    return records


if __name__ == "__main__":
    build_focus()
