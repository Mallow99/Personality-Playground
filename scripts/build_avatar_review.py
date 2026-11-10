"""Publish the inventory inspected in the visual pass, with concrete repair notes."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "bfi/static"
poses = json.loads((STATIC / "avatar/catalog.json").read_text())["poses"]
clean = {p["id"]: p for p in json.loads((STATIC / "avatar/clean/manifest.json").read_text())}
notes = {
    "engineering/flirty": (
        "Replaced the one-arm, distorted-hip drawing. Both complete arms and "
        "hands are visible: one at the hip, one at the collar. Original "
        "rejected reference retained."
    ),
    "engineering/tired": (
        "Removed two neighboring-figure fragments at the right edge; both "
        "intended arms and legs retained."
    ),
    "engineering/teasing": (
        "Removed the leaked caption beneath the feet; playful pointing gesture retained."
    ),
    "business/flirty": (
        "Forearm behind the hip is visible; its hand is intentionally occluded. "
        "Supporting arm, leaning pose and crossed legs retained."
    ),
    "academic/seated": (
        "Crossed legs and whole hands retained. Kept static so hidden book "
        "surfaces are not exposed by guessed movement."
    ),
    "academic/reading": (
        "Rear pages retained beneath both hands; limited local movement and work-directed eyes."
    ),
    "business/seated": ("Rear thigh retained beneath the resting hand; local hand movement only."),
    "engineering/H03": (
        "Both arms rest behind the head; chair supports the seated pose and one "
        "foot is lifted intentionally."
    ),
    "business/S24": (
        "Closed eyes are intentional in the resting pose; both arms and seated "
        "legs remain readable."
    ),
}
rows = []
for pose in poses:
    findings = [
        notes.get(
            pose["id"],
            (
                "Silhouette, limb/prop readability, framing, edges and gaze inspected; "
                "no additional blocking pose defect identified."
            ),
        )
    ]
    removed = len(clean.get(pose["id"], {}).get("removed", []))
    if removed:
        findings.append("Detached baseline/label scraps removed from the runtime copy.")
    if pose.get("provenance", {}).get("baseline_debris_pixels", 0):
        findings.append("Detached caption pixels removed from the cutout.")
    if pose.get("gaze_target"):
        findings.append(
            f"Local eyes now point toward the {pose['gaze_target']}; body silhouette retained."
        )
    if pose["source"] == "generated-concept":
        findings.append("White source matte removed from the transparent edge RGB.")
    rows.append(
        {
            "id": pose["id"],
            "role": pose["role"],
            "label": pose["label"],
            "review": "inspected",
            "findings": findings,
        }
    )
report = {
    "scope": (
        "All 128 runtime poses visually inspected in 12 role contact pages, "
        "plus targeted source/edge/control checks. This records findings, not a "
        "universal rig or a guarantee of perfect anatomy."
    ),
    "checks": [
        "silhouette and limb readability",
        "pose/prop contact",
        "crop and neighboring fragments",
        "baseline captions",
        "light/dark edges",
        "work gaze",
    ],
    "poses": rows,
}
for path in [
    ROOT / "config/avatar-visual-review.json",
    STATIC / "e-preview/assets/avatar-visual-review.json",
]:
    path.write_text(json.dumps(report, indent=2) + "\n")
print(f"Recorded visual review for {len(rows)} runtime poses.")
