"""Split faithful pose art into stable semantic pieces without redrawing it."""

import argparse
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import GeometryCollection, Polygon
from shapely.validation import make_valid
from trace_e_poses import NS, PALETTES, boundary_path, classify, colors_for

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bfi/static/e-preview/assets/poses"
PARTS = [
    "head",
    "neck",
    "torso",
    "left-upper-arm",
    "left-forearm",
    "left-hand",
    "right-upper-arm",
    "right-forearm",
    "right-hand",
    "left-thigh",
    "left-shin",
    "left-foot",
    "right-thigh",
    "right-shin",
    "right-foot",
    "prop-main",
    "prop-secondary",
]
BONES = {"torso": ("neck", "hip", 38), "neck": ("neck", "neck", 11)}
for side in ["left", "right"]:
    for suffix, start, end, width in [
        ("upper-arm", "Shoulder", "Elbow", 18),
        ("forearm", "Elbow", "Wrist", 14),
        ("hand", "Wrist", "Hand", 13),
        ("thigh", "Hip", "Knee", 25),
        ("shin", "Knee", "Ankle", 19),
        ("foot", "Ankle", "Toe", 13),
    ]:
        BONES[f"{side}-{suffix}"] = (side + start, side + end, width)
ET.register_namespace("", NS)


def geometry(data):
    result = GeometryCollection()
    for match in re.finditer(r"M([^MZ]+)Z", data):
        points = [tuple(map(float, p.split(","))) for p in match[1].strip().split()]
        if len(points) >= 3:
            result = result.symmetric_difference(make_valid(Polygon(points)))
    return result


def to_path(geom):
    if geom.is_empty:
        return ""
    if geom.geom_type == "Polygon":
        return "".join(
            "M" + " ".join(f"{x:.3f},{y:.3f}" for x, y in list(ring.coords)[:-1]) + "Z"
            for ring in [geom.exterior, *geom.interiors]
        )
    return "".join(to_path(item) for item in geom.geoms) if hasattr(geom, "geoms") else ""


def guide_frame(guide, matrix):
    a, b, c, d, e, f = matrix

    def point(p):
        return [a * p[0] + b * p[1] + c, d * p[0] + e * p[1] + f]

    result = json.loads(json.dumps(guide))
    result["joints"] = {k: point(v) for k, v in guide["joints"].items()}
    box = guide["head"]
    result["head"] = [*point(box[:2]), *point(box[2:])]
    result["props"] = [
        {**p, "polygon": [point(v) for v in p["polygon"]]} for p in guide.get("props", [])
    ]
    result["ownershipRegions"] = [
        {**p, "polygon": [point(v) for v in p["polygon"]]}
        for p in guide.get("ownershipRegions", [])
    ]
    return result


def labels_for(guide, shape, classes, role):
    height, width = shape
    y, x = np.mgrid[:height, :width].astype(float)
    x += 0.5
    y += 0.5
    costs = np.full((len(PARTS), height, width), 1e8, dtype=np.float32)
    joints = guide["joints"]
    hidden = set(guide.get("hiddenParts", []))
    manual = {p["id"] for p in guide.get("ownershipRegions", [])}
    for name, (start, end, radius) in BONES.items():
        if name in hidden or name in manual:
            continue
        ax, ay = joints[start]
        bx, by = joints[end]
        dx, dy = bx - ax, by - ay
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / max(dx * dx + dy * dy, 1), 0, 1)
        costs[PARTS.index(name)] = ((x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2) / (
            radius * radius
        )
    labels = costs.argmin(axis=0).astype(np.uint8)
    x0, y0, x1, y1 = guide["head"]
    head = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
    labels[head] = PARTS.index("head")
    hand_near = np.zeros(shape, dtype=bool)
    for side in ["left", "right"]:
        part = f"{side}-hand"
        near = costs[PARTS.index(part)] < 0.65
        near &= classes == 0 if role != "business" else (classes == 0) | (classes == 2)
        labels[near] = PARTS.index(part)
        hand_near |= near
    for prop in guide.get("props", []):
        image = Image.new("1", (width, height))
        ImageDraw.Draw(image).polygon([tuple(p) for p in prop["polygon"]], fill=1)
        labels[np.array(image, dtype=bool) & ~head & ~hand_near] = PARTS.index(prop["id"])
    for region in guide.get("ownershipRegions", []):
        image = Image.new("1", (width, height))
        ImageDraw.Draw(image).polygon([tuple(p) for p in region["polygon"]], fill=1)
        mask = np.array(image, dtype=bool)
        if "colors" in region:
            mask &= np.isin(classes, region["colors"])
        labels[mask] = PARTS.index(region["id"])
    return labels


def build(role, pose, entry, guide):
    folder = OUT / role
    source = ET.parse(folder / f"{pose}.svg").getroot()
    reference = np.array(Image.open(folder / f"{pose}.reference.png").convert("RGBA"))
    base = np.array(
        Image.open(io.BytesIO(cairosvg.svg2png(url=str(folder / f"{pose}.svg")))).convert("RGBA")
    )
    classes = classify(reference[:, :, :3], colors_for(role))
    mapped = guide_frame(guide, entry.get("cell_to_canvas", [1, 0, 0, 0, 1, 0]))
    labels = labels_for(mapped, reference.shape[:2], classes, role)
    shapes = [GeometryCollection() for _ in range(3)]
    for path in source:
        fill = path.get("fill")
        if fill in PALETTES[role]:
            i = PALETTES[role].index(fill)
            shapes[i] = shapes[i].union(geometry(path.get("d", "")))
    whole = guide.get("mappingMethod") == "whole-shape"
    grouped = [[GeometryCollection() for _ in range(3)] for _ in PARTS]
    components = []
    if whole:
        for color, art in enumerate(shapes):
            polygons = [art] if art.geom_type == "Polygon" else list(art.geoms)
            for rank, polygon in enumerate(sorted(polygons, key=lambda p: -p.area)):
                shape_id = f"c{color}-{rank}"
                center = polygon.representative_point()
                fallback = PARTS[int(labels[min(511, int(center.y)), min(511, int(center.x))])]
                owner = guide.get("componentAssignments", {}).get(shape_id, fallback)
                grouped[PARTS.index(owner)][color] = grouped[PARTS.index(owner)][color].union(
                    polygon
                )
                components.append(
                    {
                        "id": shape_id,
                        "part": owner,
                        "color": color,
                        "area": round(polygon.area, 3),
                        "path": to_path(polygon),
                    }
                )
    data = {
        "version": 1,
        "role": role,
        "pose": pose,
        "canvas": entry["canvas"],
        "palette": PALETTES[role],
        "guideStatus": guide.get("mappingStatus", "draft"),
        "guide": mapped,
        "sourceGuide": guide,
        "cellToCanvas": entry.get("cell_to_canvas", [1, 0, 0, 0, 1, 0]),
        "source_sha256": entry["vector_sha256"],
        "parts": [],
        "mappingMethod": "whole-shape" if whole else "joint-regions",
        "sourceComponents": components,
    }
    svg = ET.Element(
        f"{{{NS}}}svg",
        {
            "viewBox": "0 0 512 512",
            "width": "512",
            "height": "512",
            "role": "img",
            "data-pose": pose,
            "data-rig": "semantic-v1",
        },
    )
    ET.SubElement(svg, f"{{{NS}}}title").text = f"{role} {pose}, semantic body pieces"
    debug = np.full((512, 512, 3), 255, dtype=np.uint8)
    allowed_colors = {p["id"]: p.get("colors", [0, 1, 2]) for p in mapped["ownershipRegions"]}
    for i, name in enumerate(PARTS):
        region = (
            geometry(boundary_path(labels == i)).simplify(0.2, preserve_topology=True).buffer(0.16)
        )
        paths = (
            [to_path(art) for art in grouped[i]]
            if whole
            else [
                to_path(art.intersection(region))
                if color in allowed_colors.get(name, [0, 1, 2])
                else ""
                for color, art in enumerate(shapes)
            ]
        )
        if name == "head":
            pivot = [
                (mapped["head"][0] + mapped["head"][2]) / 2,
                (mapped["head"][1] + mapped["head"][3]) / 2,
            ]
        elif name in BONES:
            pivot = mapped["joints"][BONES[name][0]]
        else:
            pivot = [256, 256]
        part = {"id": name, "pivot": pivot, "paths": paths, "visible": any(paths)}
        if whole:
            part["label"] = (
                name.replace("-thigh", " leg (continuous form)")
                .replace("-upper-arm", " sleeve")
                .replace("-", " ")
            )
        data["parts"].append(part)
        group = ET.SubElement(svg, f"{{{NS}}}g", {"data-part": name})
        for color, path in zip(PALETTES[role], paths, strict=True):
            if path:
                ET.SubElement(
                    group, f"{{{NS}}}path", {"d": path, "fill": color, "fill-rule": "evenodd"}
                )
        debug[(labels == i) & (reference[:, :, 3] > 127)] = [
            (47 + i * 79) % 220,
            (83 + i * 107) % 220,
            (131 + i * 53) % 220,
        ]
    svg_path = folder / f"{pose}.rig.svg"
    ET.ElementTree(svg).write(svg_path, encoding="unicode")
    rendered = np.array(Image.open(io.BytesIO(cairosvg.svg2png(url=str(svg_path)))).convert("RGBA"))
    a = base[:, :, 3] > 127
    b = rendered[:, :, 3] > 127
    overlap = float((a & b).sum() / max(1, (a | b).sum()))
    data["assembly_geometry_iou"] = round(overlap, 6)
    data["rig_sha256"] = hashlib.sha256(svg_path.read_bytes()).hexdigest()
    (folder / f"{pose}.rig.json").write_text(json.dumps(data, separators=(",", ":")))
    check = ROOT / "runs/e-rig-review" / role
    check.mkdir(parents=True, exist_ok=True)
    if whole:
        review = ET.fromstring(ET.tostring(svg))
        for i, group in enumerate(review.findall(f"{{{NS}}}g")):
            color = (
                f"#{(47 + i * 79) % 220:02x}{(83 + i * 107) % 220:02x}{(131 + i * 53) % 220:02x}"
            )
            for path in group:
                path.set("fill", color)
        debug = np.array(
            Image.open(
                io.BytesIO(
                    cairosvg.svg2png(bytestring=ET.tostring(review), background_color="#ffffff")
                )
            ).convert("RGB")
        )
    Image.fromarray(debug).save(check / f"{pose}.parts.png")
    assert overlap >= 0.99, (role, pose, overlap)
    return {
        "pose": pose,
        "assembly_geometry_iou": round(overlap, 6),
        "visibleParts": [p["id"] for p in data["parts"] if p["visible"]],
        "guideStatus": data["guideStatus"],
        "mappingMethod": data["mappingMethod"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "poses", nargs="*", help="Optional role/pose selections; default rebuilds all"
    )
    selected = set(parser.parse_args().poses)
    manifest = json.loads((OUT / "manifest.json").read_text())
    known = {
        f"{role}/{p['id']}" for role, entries in manifest["characters"].items() for p in entries
    }
    if selected - known:
        parser.error("Unknown pose selection: " + ", ".join(sorted(selected - known)))
    report = (
        json.loads((OUT / "rig-report.json").read_text())
        if selected
        else {"version": 1, "parts": PARTS, "characters": {}}
    )
    for role, entries in manifest["characters"].items():
        path = ROOT / f"config/rigs/{role}.json"
        if not path.exists():
            print("WAITING FOR GUIDE", role, flush=True)
            continue
        guides = json.loads(path.read_text())["poses"]
        if not selected:
            report["characters"][role] = []
        for entry in entries:
            if selected and f"{role}/{entry['id']}" not in selected:
                continue
            result = build(role, entry["id"], entry, guides[entry["id"]])
            rows = report["characters"][role]
            if selected:
                rows[next(i for i, row in enumerate(rows) if row["pose"] == entry["id"])] = result
            else:
                rows.append(result)
            print(role, entry["id"], result["assembly_geometry_iou"], flush=True)
    (OUT / "rig-report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
