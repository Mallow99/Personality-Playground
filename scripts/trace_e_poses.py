"""Direct trace of the generated E pose sheets, with rendered geometry comparisons.

UV_CACHE_DIR=/tmp/bfi-uv-cache uv run --with cairosvg --with numpy python scripts/trace_e_poses.py
Sources and crop rectangles are recorded. Palette normalization is explicit; no
anatomy is redrawn, no source image is embedded in the SVG.
"""

import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
from importlib.metadata import version
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "research/visual-studies/poses-v2"
OUT = ROOT / "bfi/static/e-preview/assets/poses"
PALETTES = {
    "academic": ["#58402B", "#87A452", "#EBD8AF"],
    "engineering": ["#20171E", "#D9254C", "#F6A0B4"],
    "business": ["#153B64", "#247DD4", "#B9E9FA"],
}
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def colors_for(role):
    return np.array(
        [tuple(bytes.fromhex(c[1:])) for c in PALETTES[role]] + [(255, 255, 255)], dtype=np.int32
    )


def classify(rgb, colors):
    delta = rgb.astype(np.int32)[:, :, None, :] - colors[None, None, :, :]
    return (delta * delta).sum(axis=3).argmin(axis=2)


def simplify(points, epsilon=0.75):
    if len(points) < 4:
        return points
    start, end = points[0], points[-1]
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = dx * dx + dy * dy

    def dist(p):
        if not length:
            return (p[0] - start[0]) ** 2 + (p[1] - start[1]) ** 2
        t = max(0, min(1, ((p[0] - start[0]) * dx + (p[1] - start[1]) * dy) / length))
        return (p[0] - start[0] - t * dx) ** 2 + (p[1] - start[1] - t * dy) ** 2

    index, maximum = max(enumerate(points[1:-1], 1), key=lambda pair: dist(pair[1]))
    value = dist(maximum)
    if value > epsilon * epsilon:
        return simplify(points[: index + 1], epsilon)[:-1] + simplify(points[index:], epsilon)
    return [start, end]


def smooth_paths(root):
    for node in root:
        if not node.tag.endswith("path"):
            continue
        data = []
        for sub in re.findall(r"M([^MZ]+)Z", node.get("d", "")):
            points = [tuple(map(int, p.split(","))) for p in sub.strip().split()]
            points = simplify(points + [points[0]])[:-1]
            if len(points) >= 3:
                data.append("M" + " ".join(f"{x},{y}" for x, y in points) + "Z")
        node.set("d", "".join(data))


def boundary_path(mask):
    # Trace the actual pixel boundaries, not an artist's replacement silhouette.
    padded = np.pad(mask, 1)
    edge_map = {}

    def add(start, end):
        edge_map.setdefault(start, []).append(end)

    ys, xs = np.where(mask & ~padded[:-2, 1:-1])
    for y, x in zip(ys.tolist(), xs.tolist(), strict=True):
        add((x, y), (x + 1, y))
    ys, xs = np.where(mask & ~padded[1:-1, 2:])
    for y, x in zip(ys.tolist(), xs.tolist(), strict=True):
        add((x + 1, y), (x + 1, y + 1))
    ys, xs = np.where(mask & ~padded[2:, 1:-1])
    for y, x in zip(ys.tolist(), xs.tolist(), strict=True):
        add((x + 1, y + 1), (x, y + 1))
    ys, xs = np.where(mask & ~padded[1:-1, :-2])
    for y, x in zip(ys.tolist(), xs.tolist(), strict=True):
        add((x, y + 1), (x, y))
    paths = []

    def direction(a, b):
        return 0 if b[0] > a[0] else 1 if b[1] > a[1] else 2 if b[0] < a[0] else 3

    while edge_map:
        start = next(iter(edge_map))
        current = start
        points = [start]
        previous = 0
        while True:
            candidates = edge_map[current]
            end = min(
                candidates,
                key=lambda v: {1: 0, 0: 1, 3: 2, 2: 3}[(direction(current, v) - previous) % 4],
            )
            candidates.remove(end)
            if not candidates:
                del edge_map[current]
            previous = direction(current, end)
            current = end
            if current == start:
                break
            points.append(current)
        clean = []
        for i, point in enumerate(points):
            before = points[i - 1]
            after = points[(i + 1) % len(points)]
            if (point[0] - before[0]) * (after[1] - point[1]) != (point[1] - before[1]) * (
                after[0] - point[0]
            ):
                clean.append(point)
        if clean:
            paths.append("M" + " ".join(f"{x},{y}" for x, y in clean) + "Z")
    return "".join(paths)


def process(sheet, index, slug):
    role = sheet["role"]
    folder = OUT / role
    folder.mkdir(parents=True, exist_ok=True)
    path = SOURCES / sheet["file"]
    image = Image.open(path).convert("RGB")
    w, h = image.size
    cw, ch = w // 3, h // 2
    col, row = index % 3, index // 3
    bottom = round(sheet["art_bottom"][row] * ch / 512)
    bounds = (col * cw, row * ch, (col + 1) * cw, row * ch + bottom)
    # Keep cell coordinates and head/body proportions; never independently stretch limbs.
    source = Image.new("RGB", (cw, ch), "white")
    cell_to_canvas = [1, 0, 0, 0, 1, 0]
    frame = sheet.get("pose_frames", {}).get(slug)
    if frame:
        bounds = tuple(frame["bounds"])
        crop = image.crop(bounds)
        size = [round(value * frame["scale"]) for value in crop.size]
        offset = frame["offset"]
        source.paste(crop.resize(size, Image.Resampling.LANCZOS), tuple(offset))
        sx, sy = size[0] / crop.width, size[1] / crop.height
        cell_to_canvas = [
            sx,
            0,
            offset[0] + sx * (col * cw - bounds[0]),
            0,
            sy,
            offset[1] + sy * (row * ch - bounds[1]),
        ]
    else:
        source.paste(image.crop(bounds), (0, 0))
    source.save(folder / f"{slug}.source.png")
    rgb = np.array(source)
    colors = colors_for(role)
    classes = classify(rgb, colors)
    rgba = np.zeros((ch, cw, 4), dtype=np.uint8)
    rgba[:, :, :3] = colors[classes]
    rgba[:, :, 3] = np.where(classes < 3, 255, 0)
    reference = folder / f"{slug}.reference.png"
    Image.fromarray(rgba).save(reference)
    svg = folder / f"{slug}.svg"
    node = ET.Element(
        f"{{{NS}}}svg",
        {
            "width": str(cw),
            "height": str(ch),
            "viewBox": f"0 0 {cw} {ch}",
            "role": "img",
            "data-source-sheet": sheet["file"],
            "data-pose": slug,
        },
    )
    title = ET.SubElement(node, f"{{{NS}}}title")
    title.text = f"{role} — {slug}; direct generated-reference boundary trace"
    for color_index, color in enumerate(PALETTES[role]):
        ET.SubElement(
            node,
            f"{{{NS}}}path",
            {
                "d": boundary_path(classes == color_index),
                "fill": color,
                "fill-rule": "evenodd",
                "data-piece": f"color-region-{color_index}",
            },
        )
    boundary = folder / f"{slug}.boundary.svg"
    ET.ElementTree(node).write(boundary, encoding="unicode", xml_declaration=False)
    smooth_paths(node)
    node.set("data-cleanup-tolerance", "0.75 source pixels")
    ET.ElementTree(node).write(svg, encoding="unicode", xml_declaration=False)
    rendered = Image.open(
        io.BytesIO(cairosvg.svg2png(url=str(svg), output_width=cw, output_height=ch))
    ).convert("RGBA")
    render = np.array(rendered)
    mask_a = classes < 3
    mask_b = render[:, :, 3] >= 128
    overlap = mask_a & mask_b
    union = mask_a | mask_b
    geometry = float(overlap.sum() / max(1, union.sum()))
    boundary_render = np.array(
        Image.open(
            io.BytesIO(cairosvg.svg2png(url=str(boundary), output_width=cw, output_height=ch))
        ).convert("RGBA")
    )
    boundary_mask = boundary_render[:, :, 3] >= 128
    boundary_iou = float((mask_a & boundary_mask).sum() / max(1, (mask_a | boundary_mask).sum()))

    render_classes = classify(render[:, :, :3], colors)
    color = float((render_classes[overlap] == classes[overlap]).mean())
    # A same-coordinate side-by-side and difference view, not a subjective passing claim.
    comp = Image.new("RGB", (cw * 3, ch), "#f7f4ef")
    comp.paste(source, (0, 0))
    white = Image.new("RGBA", (cw, ch), "white")
    white.alpha_composite(rendered)
    comp.paste(white.convert("RGB"), (cw, 0))
    diff = np.full((ch, cw, 3), 255, dtype=np.uint8)
    diff[mask_a] = [220, 220, 220]
    diff[mask_a ^ mask_b] = [255, 0, 90]
    diff[overlap & (render_classes != classes)] = [0, 100, 255]
    comp.paste(Image.fromarray(diff), (cw * 2, 0))
    comparison_folder = ROOT / "runs/pose-comparisons"
    comparison_folder.mkdir(parents=True, exist_ok=True)
    comp.save(comparison_folder / f"{role}-{slug}.comparison.png")
    return {
        "id": slug,
        "label": slug.replace("-", " ").title(),
        "category": "playful"
        if slug in ["teasing", "flirty", "glamour", "silly", "sultry"]
        else "specialist"
        if slug
        in [
            "reading",
            "chalkboard",
            "writing-prose",
            "security-review",
            "coding",
            "debugging",
            "coordinating",
            "formal-report",
            "task-complete",
            "testing",
            "code-review",
        ]
        else "everyday",
        "sheet": sheet["file"],
        "sheet_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "crop": list(bounds),
        "cell_to_canvas": cell_to_canvas,
        "canvas": [cw, ch],
        "geometry_iou": round(geometry, 6),
        "boundary_geometry_iou": round(boundary_iou, 6),
        "cleanup_tolerance_px": 0.75,
        "palette_agreement": round(color, 6),
        "vector_sha256": hashlib.sha256(svg.read_bytes()).hexdigest(),
        "path_count": sum(c.tag.endswith("path") for c in node),
    }


def main(only_frames=False):
    manifest = {
        "version": 2,
        "tool_versions": {name: version(name) for name in ["numpy", "CairoSVG", "Pillow"]},
        "method": (
            "direct contours with 0.75px cleanup; exact boundaries retained; "
            "documented three-color normalization, no silhouette redraw"
        ),
        "reference": "generated E pose sheets; not approved production rig",
        "characters": {},
    }
    if only_frames:
        manifest = json.loads((OUT / "manifest.json").read_text())
    for sheet in json.loads((SOURCES / "sources.json").read_text())["sheets"]:
        role = sheet["role"]
        manifest["characters"].setdefault(role, [])
        for i, slug in enumerate(sheet["poses"]):
            if slug is None:
                continue
            if only_frames and slug not in sheet.get("pose_frames", {}):
                continue
            result = process(sheet, i, slug)
            if only_frames:
                manifest["characters"][role] = [
                    p for p in manifest["characters"][role] if p["id"] != slug
                ]
            manifest["characters"][role].append(result)
            print(role, slug, result["geometry_iou"], result["palette_agreement"], flush=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    assert all(
        p["geometry_iou"] >= 0.98 and p["palette_agreement"] >= 0.995
        for items in manifest["characters"].values()
        for p in items
    ), "A trace failed the geometry/palette gate; inspect comparisons."
    catalog = {
        role: [
            {k: p[k] for k in ["id", "label", "category", "geometry_iou", "palette_agreement"]}
            for p in items
        ]
        for role, items in manifest["characters"].items()
    }
    (ROOT / "bfi/static/e-preview/pose-catalog.js").write_text(
        "// Generated by scripts/trace_e_poses.py from source-sheet metadata.\n"
        "export const poseCatalog = " + json.dumps(catalog, indent=2) + ";\n"
    )
    print("PASS: pose traces passed rendered geometry/palette gates.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--only-frames", action="store_true")
    main(parser.parse_args().only_frames)
