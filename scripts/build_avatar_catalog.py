"""Package authored poses and transparent proposal cutouts for the runtime avatar."""

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from avatar_matte import remove_baseline_debris, remove_white_matte
from build_avatar_focus import build_focus
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "bfi/static"
OUT = STATIC / "avatar"
(OUT / "cutouts").mkdir(exist_ok=True)
manifest = json.loads((STATIC / "e-preview/assets/poses/manifest.json").read_text())
proposals = json.loads((ROOT / "config/pose-review.json").read_text())["proposals"]
PALETTES = {
    "academic": ["#58402B", "#87A452", "#EBD8AF"],
    "engineering": ["#20171E", "#D9254C", "#F6A0B4"],
    "business": ["#153B64", "#247DD4", "#B9E9FA"],
}
entries = []
for role, poses in manifest["characters"].items():
    for pose in poses:
        entries.append(
            dict(
                id=f"{role}/{pose['id']}",
                role=role,
                label=pose["label"],
                src=f"/static/e-preview/assets/poses/{role}/{pose['id']}.svg",
                tags=pose["id"].split("-"),
                description=pose["label"],
                source="traced-pose",
                motion="reading" if role == "academic" and pose["id"] == "reading" else "none",
            )
        )
for entry in entries:
    if entry["id"] == "business/seated":
        entry["motion"] = "seated-hand"
        entry["layered_src"] = "/static/e-preview/assets/business-seated-layered.svg"
for clean in json.loads((OUT / "clean/manifest.json").read_text()):
    entry = next(e for e in entries if e["id"] == clean["id"])
    entry["original_src"] = entry["src"]
    entry["src"] = clean["src"]
for p in proposals:
    meta = p["image"]
    source = STATIC / "e-preview" / meta["sheet"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == meta["sha256"]
    # Labels occupy the last part of each 512px cell. Unmix the white source
    # matte from edge RGB as well as estimating alpha; keep original sheets.
    image = Image.open(source).convert("RGB")
    x, y = meta["column"] * 512, meta["row"] * 512
    rgb = np.array(image.crop((x, y, x + 512, y + 456)))
    rgba, debris = remove_baseline_debris(remove_white_matte(rgb, PALETTES[meta["illustratedBy"]]))
    cutout = Image.new("RGBA", (512, 512))
    cutout.paste(Image.fromarray(rgba), (0, 28))
    name = p["code"] + ".png"
    cutout.save(OUT / "cutouts" / name)
    entries.append(
        dict(
            id=f"{meta['illustratedBy']}/{p['code']}",
            role=meta["illustratedBy"],
            label=p["label"],
            src=f"/static/avatar/cutouts/{name}",
            tags=[p["code"], *p["id"].split("-")],
            description=p["reason"],
            source="generated-concept",
            approval=p["status"],
            asset_version=hashlib.sha256((OUT / "cutouts" / name).read_bytes()).hexdigest()[:12],
            motion="none",
            provenance=dict(
                sheet=meta["sheet"],
                row=meta["row"],
                column=meta["column"],
                sha256=meta["sha256"],
                art_crop=[0, 0, 512, 456],
                baseline_debris_pixels=debris,
            ),
        )
    )
focus = build_focus()
for record in focus:
    entry = next(e for e in entries if e["id"] == record["id"])
    entry["original_src"] = record["original_src"]
    entry["gaze_target"] = record["target"]
    entry["asset_version"] = record["asset_version"]
    if record["layered"]:
        entry["layered_src"] = record["src"]
    else:
        entry["src"] = record["src"]
assert len(entries) == 128 and len({p["id"] for p in entries}) == 128
catalog = dict(
    version=1,
    poses=entries,
    roles={
        "academic": dict(name="Academic", colors=["#58402B", "#87A452", "#EBD8AF"]),
        "engineering": dict(name="Hacker", colors=["#20171E", "#D9254C", "#F6A0B4"]),
        "business": dict(name="Business", colors=["#153B64", "#247DD4", "#B9E9FA"]),
    },
)
(OUT / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
print("Packaged 74 traced poses and 54 transparent concept cutouts; all source sheets retained.")

# Reuse the exact renderer in the owner-private static demo, with local URL mapping.
demo = STATIC / "e-preview/avatar-runtime"
demo.mkdir(exist_ok=True)
for name in ["avatar.js", "avatar.css", "catalog.json"]:
    shutil.copyfile(OUT / name, demo / name)
shutil.copytree(OUT / "cutouts", demo / "cutouts", dirs_exist_ok=True)

shutil.copytree(OUT / "focus", demo / "focus", dirs_exist_ok=True)

shutil.copytree(OUT / "clean", demo / "clean", dirs_exist_ok=True)
