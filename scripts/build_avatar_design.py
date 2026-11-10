"""Consistent Business heads, solid paper planes and role-colored dark artwork."""

import base64
import copy
import hashlib
import io
import json
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

import cairosvg
import numpy as np
from build_e_rigs import NS, PALETTES, geometry, guide_frame, to_path
from PIL import Image
from shapely.geometry import Polygon, box
from trace_e_poses import boundary_path, smooth_paths

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "bfi/static"
OUT = STATIC / "avatar/design-v5"
ET.register_namespace("", NS)


def components(mask):
    seen = np.zeros(mask.shape, dtype=bool)
    height, width = mask.shape
    rows = []
    for sy, sx in zip(*np.where(mask), strict=True):
        if seen[sy, sx]:
            continue
        queue = deque([(sy, sx)])
        seen[sy, sx] = True
        ys, xs = [], []
        while queue:
            y, x = queue.popleft()
            ys.append(y)
            xs.append(x)
            for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        rows.append((np.array(ys), np.array(xs)))
    return rows


def palette_classes(pixels, role):
    colors = np.array([tuple(bytes.fromhex(c[1:])) for c in PALETTES[role]], dtype=int)
    return ((pixels[:, :, None, :3].astype(int) - colors) ** 2).sum(axis=3).argmin(axis=2)


def raster(svg):
    full = copy.deepcopy(svg)
    full.set("viewBox", "0 0 512 512")
    return np.array(
        Image.open(
            io.BytesIO(
                cairosvg.svg2png(bytestring=ET.tostring(full), output_width=512, output_height=512)
            )
        ).convert("RGBA")
    )


def png_element(pixels):
    data = io.BytesIO()
    Image.fromarray(pixels).save(data, format="PNG")
    return ET.Element(
        f"{{{NS}}}image",
        {
            "width": "512",
            "height": "512",
            "href": "data:image/png;base64," + base64.b64encode(data.getvalue()).decode(),
        },
    )


def head_models(config):
    image = Image.open(ROOT / config["reference"]).convert("RGBA")
    result = {}
    for name, bounds in config["headModels"].items():
        pixels = np.array(image.crop(bounds))
        classes = palette_classes(pixels, "business")
        svg = ET.Element(f"{{{NS}}}svg", {"viewBox": f"0 0 {pixels.shape[1]} {pixels.shape[0]}"})
        for index, color in enumerate(PALETTES["business"]):
            ET.SubElement(
                svg,
                f"{{{NS}}}path",
                {
                    "d": boundary_path((classes == index) & (pixels[:, :, 3] > 220)),
                    "fill": color,
                    "fill-rule": "evenodd",
                },
            )
        smooth_paths(svg)
        result[name] = (svg, pixels.shape[1], pixels.shape[0])
        ET.ElementTree(svg).write(OUT / f"head-{name}.svg", encoding="unicode")
    return result


def detected_head(pixels):
    classes = palette_classes(pixels, "business")
    candidates = []
    for ys, xs in components((classes == 0) & (pixels[:, :, 3] > 100)):
        bounds = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        x, y, x2, y2 = bounds
        if len(xs) > 300 and 35 < x2 - x < 180 and 30 < y2 - y < 165 and y < 220:
            candidates.append(bounds)
    assert candidates, "No unambiguous Business head candidate"
    return min(candidates, key=lambda b: b[1])


def remove_head_svg(svg, bounds):
    region = box(*bounds).buffer(3)
    removed = []
    for path in svg.iter():
        if path.get("fill") not in PALETTES["business"] or not path.get("d"):
            continue
        index = PALETTES["business"].index(path.get("fill"))
        shape = geometry(path.get("d"))
        polygons = [shape] if shape.geom_type == "Polygon" else list(shape.geoms)
        kept = []
        for polygon in polygons:
            bx, by, bx2, by2 = polygon.bounds
            inside = region.intersection(polygon).area / max(polygon.area, 0.001) > 0.8
            # Whole hand/sleeve forms stay in the foreground, including at the face.
            face = inside and (
                index == 1
                or (index == 0 and (polygon.area > 200 or polygon.area < 10))
                or (index == 2 and (polygon.area < 250 or by2 - by < 22))
            )
            if face:
                removed.append([index, list(polygon.bounds), round(polygon.area, 2)])
            else:
                kept.append(polygon)
        path.set("d", "".join(to_path(p) for p in kept))
    return removed


def remove_head_png(pixels, bounds):
    result = pixels.copy()
    classes = palette_classes(pixels, "business")
    x, y, x2, y2 = bounds
    removed = []
    for index in range(3):
        for ys, xs in components((classes == index) & (pixels[:, :, 3] > 20)):
            inside = ((xs >= x - 3) & (xs <= x2 + 3) & (ys >= y - 3) & (ys <= y2 + 3)).mean() > 0.8
            face = inside and (
                index == 1
                or (index == 0 and (len(xs) > 200 or len(xs) < 10))
                or (index == 2 and (len(xs) < 250 or ys.max() - ys.min() < 22))
            )
            if face:
                result[ys, xs] = 0
                removed.append(
                    [
                        index,
                        [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)],
                        len(xs),
                    ]
                )
    return result, removed


def authored_writing(slug, config):
    spec = config["business"]["authoredWriting"][slug]
    raw = Image.open(ROOT / config["business"]["writingReference"]).convert("RGBA")
    crop = raw.crop(spec["crop"])
    bounds = crop.getchannel("A").point(lambda a: 255 if a > 220 else 0).getbbox()
    crop = crop.crop(bounds)
    size = (round(crop.width * spec["height"] / crop.height), spec["height"])
    crop = crop.resize(size, Image.Resampling.LANCZOS)
    left, top = (512 - size[0]) // 2, spec["top"]
    canvas = Image.new("RGBA", (512, 512))
    canvas.alpha_composite(crop, (left, top))
    pixels = np.array(canvas)
    classes = palette_classes(pixels, "business")
    colors = np.array([tuple(bytes.fromhex(c[1:])) for c in PALETTES["business"]], dtype=np.uint8)
    normalized = np.dstack(
        [colors[classes], np.where(pixels[:, :, 3] > 220, 255, 0).astype(np.uint8)]
    )
    normalized[normalized[:, :, 3] == 0, :3] = 0
    folder = OUT / "authored"
    folder.mkdir(exist_ok=True)
    source = folder / f"{slug}.reference.png"
    Image.fromarray(normalized).save(source)
    svg = ET.Element(f"{{{NS}}}svg", {"viewBox": "0 0 512 512", "role": "img"})
    for index, color in enumerate(PALETTES["business"]):
        ET.SubElement(
            svg,
            f"{{{NS}}}path",
            {
                "d": boundary_path((classes == index) & (pixels[:, :, 3] > 220)),
                "fill": color,
                "fill-rule": "evenodd",
            },
        )
    smooth_paths(svg)
    scale = spec["height"] / (bounds[3] - bounds[1])
    board = [
        [
            (x - spec["crop"][0] - bounds[0]) * scale + left,
            (y - spec["crop"][1] - bounds[1]) * scale + top,
        ]
        for x, y in spec["board"]
    ]
    svg.insert(
        0,
        ET.Element(
            f"{{{NS}}}path",
            {
                "id": "inward-clipboard-back",
                "d": to_path(Polygon(board)),
                "fill": PALETTES["business"][0],
            },
        ),
    )
    return svg, normalized, source, board


def business_design(entries, config):
    OUT.mkdir(parents=True, exist_ok=True)
    models = head_models(config)
    guides = json.loads((ROOT / "config/rigs/business.json").read_text())["poses"]
    source_manifest = {
        p["id"]: p
        for p in json.loads((STATIC / "e-preview/assets/poses/manifest.json").read_text())[
            "characters"
        ]["business"]
    }
    report = []
    for entry in entries:
        if entry["role"] != "business":
            continue
        slug = entry["id"].split("/")[1]
        authored = slug in config["business"]["authoredWriting"]
        face_only = config["business"]["faceOnly"].get(slug)
        board = None
        if authored:
            svg, pixels, source, board = authored_writing(slug, config)
            bounds = detected_head(pixels)
            removed = []
            mode = "authored-inward-writing"
            entry["design_source"] = "/static/" + str(source.relative_to(STATIC))
            entry["clipboard_orientation"] = "paper_faces_character"
        elif entry["source"] == "generated-concept":
            source = STATIC / f"avatar/cutouts/{slug}.png"
            pixels = np.array(Image.open(source).convert("RGBA"))
            bounds = detected_head(pixels)
            body, removed = (pixels, []) if face_only else remove_head_png(pixels, bounds)
            svg = ET.Element(f"{{{NS}}}svg", {"viewBox": "0 0 512 512", "role": "img"})
            svg.append(png_element(body))
        else:
            source = (
                STATIC / "e-preview/assets/business-seated-layered.svg"
                if entry["motion"] == "seated-hand"
                else STATIC / f"avatar/clean/business/{slug}.svg"
            )
            svg = ET.parse(source).getroot()
            pixels = raster(svg)
            matrix = source_manifest[slug].get("cell_to_canvas", [1, 0, 0, 0, 1, 0])
            bounds = guide_frame(guides[slug], matrix)["head"]
            removed = [] if face_only else remove_head_svg(svg, bounds)
        paper = config["business"]["paper"].get(slug, [])
        paper_group = ET.Element(f"{{{NS}}}g", {"id": "opaque-paper-surfaces"})
        for polygon in paper:
            color = PALETTES["business"][1 if slug in config["business"]["solidBack"] else 2]
            ET.SubElement(
                paper_group, f"{{{NS}}}path", {"d": to_path(Polygon(polygon)), "fill": color}
            )
        svg.insert(0, paper_group)
        if face_only:
            mode = "two-eye-local-with-foreground-hand"
            group = ET.SubElement(
                svg, f"{{{NS}}}g", {"id": "business-consistent-head", "data-face-model": mode}
            )
            ET.SubElement(
                group,
                f"{{{NS}}}path",
                {"d": to_path(Polygon(face_only["cover"])), "fill": PALETTES["business"][0]},
            )
            for key, index in [("eyes", 2), ("pupils", 1)]:
                for polygon in face_only[key]:
                    ET.SubElement(
                        group,
                        f"{{{NS}}}path",
                        {"d": to_path(Polygon(polygon)), "fill": PALETTES["business"][index]},
                    )
        elif not authored:
            mode = (
                "down"
                if slug in config["business"]["work"]
                else "front"
                if slug in ["standing", "greeting", "laughing", "B04", "S03", "S09", "S12"]
                else "quarter"
            )
            head, width, height = models[mode]
            head = copy.deepcopy(head)
            if slug in config["business"]["closedEyes"]:
                for path in head:
                    shape = geometry(path.get("d"))
                    polygons = [shape] if shape.geom_type == "Polygon" else list(shape.geoms)
                    kept = []
                    for polygon in polygons:
                        if (
                            path.get("fill") in PALETTES["business"][1:]
                            and polygon.centroid.y > height * 0.48
                        ):
                            if path.get("fill") == PALETTES["business"][2]:
                                bx, by, bx2, by2 = polygon.bounds
                                cy = (by + by2) / 2
                                kept.append(
                                    Polygon([(bx, cy), (bx2, cy - 2), (bx2, cy + 2), (bx, cy + 4)])
                                )
                        else:
                            kept.append(polygon)
                    path.set("d", "".join(to_path(p) for p in kept))
            x, y, x2, y2 = bounds
            scale = (y2 - y) / height
            left = (x + x2) / 2 - width * scale / 2
            angle = config["business"]["rotations"].get(slug, 0)
            group = ET.Element(
                f"{{{NS}}}g",
                {
                    "id": "business-consistent-head",
                    "data-face-model": mode,
                    "transform": (
                        f"rotate({angle} {(x + x2) / 2} {y2}) translate({left} {y}) scale({scale})"
                    ),
                },
            )
            for path in head:
                group.append(path)
            svg.insert(1, group)
        ET.SubElement(svg, f"{{{NS}}}title").text = f"Business {slug}: consistent two-eye design"
        destination = OUT / "business" / f"{slug}.svg"
        destination.parent.mkdir(exist_ok=True)
        ET.ElementTree(svg).write(destination, encoding="unicode")
        entry["previous_src"] = entry.get("layered_src", entry["src"])
        entry["src"] = f"/static/avatar/design-v5/business/{slug}.svg"
        if entry["motion"] == "seated-hand":
            entry["layered_src"] = entry["src"]
        entry["asset_version"] = hashlib.sha256(destination.read_bytes()).hexdigest()[:12]
        entry["face_design"] = "two-eye-v5"
        entry["design_status"] = "candidate"
        entry["gaze_target"] = (
            "clipboard" if authored else "work" if mode == "down" else "conversation"
        )
        report.append(
            {
                "id": entry["id"],
                "source": str(source.relative_to(STATIC)),
                "head_bounds": bounds,
                "head_model": mode,
                "removed": removed,
                "paper": paper,
                "inward_board": board,
            }
        )
    (OUT / "business-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Built {len(report)} Business poses; writing boards face the character.")


def recolor_image(data, role, target):
    pixels = np.array(Image.open(io.BytesIO(data)).convert("RGBA"))
    colors = np.array([tuple(bytes.fromhex(c[1:])) for c in target], dtype=np.uint8)
    pixels[:, :, :3] = colors[palette_classes(pixels, role)]
    pixels[pixels[:, :, 3] == 0, :3] = 0
    out = io.BytesIO()
    Image.fromarray(pixels).save(out, format="PNG")
    return out.getvalue()


def dark_variants(entries, config):
    dark = STATIC / "avatar/dark"
    dark.mkdir(exist_ok=True)
    for entry in entries:
        source_url = entry.get("layered_src", entry["src"])
        source = STATIC / source_url.removeprefix("/static/")
        role = entry["role"]
        destination = dark / role / source.name
        destination.parent.mkdir(exist_ok=True)
        palette = config["darkPalettes"][role]
        if source.suffix == ".png":
            destination.write_bytes(recolor_image(source.read_bytes(), role, palette))
        else:
            root = ET.parse(source).getroot()
            for element in root.iter():
                if element.get("fill") in PALETTES[role]:
                    element.set("fill", palette[PALETTES[role].index(element.get("fill"))])
                href = element.get("href", "")
                if href.startswith("data:image/png;base64,"):
                    image = recolor_image(base64.b64decode(href.split(",", 1)[1]), role, palette)
                    element.set("href", "data:image/png;base64," + base64.b64encode(image).decode())
            ET.ElementTree(root).write(destination, encoding="unicode")
        entry["dark_asset_version"] = hashlib.sha256(destination.read_bytes()).hexdigest()[:12]
        entry["dark_src"] = f"/static/avatar/dark/{role}/{destination.name}"
        if entry.get("layered_src"):
            entry["dark_layered_src"] = entry["dark_src"]
    print(f"Built {len(entries)} role-colored dark-background variants, without outlines.")


def build_design(entries):
    config = json.loads((ROOT / "config/avatar-design-v5.json").read_text())
    business_design(entries, config)
    dark_variants(entries, config)
