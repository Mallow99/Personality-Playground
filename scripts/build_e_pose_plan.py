"""Build the durable pose inventory and distinguish new art from reusable states."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "bfi/static/e-preview/assets/poses/manifest.json").read_text())
common = [
    (
        "pointing-left",
        "Pointing left",
        1,
        "Direct attention to a diagram, document, or UI element.",
    ),
    (
        "pointing-right",
        "Pointing right",
        1,
        "The opposite pointing direction needs clear arm/hand ownership.",
    ),
    (
        "reassuring",
        "Encouraging / reassuring",
        1,
        "Support without turning every emotional moment into concern.",
    ),
    ("surprised", "Surprised", 2, "A distinct reaction to unexpected results or discoveries."),
    (
        "skeptical",
        "Skeptical / disagreeing",
        2,
        "Express a justified objection with room for humor.",
    ),
    ("apologetic", "Apologetic / correcting", 2, "Acknowledge and repair an actual mistake."),
    ("relieved", "Relieved", 3, "A quieter successful outcome than celebration."),
    ("stretching", "Stretching", 3, "A distinct rest/recovery silhouette."),
]
special = {
    "academic": [
        (
            "storytelling",
            "Storytelling / DM narration",
            1,
            "Prose and Dungeons & Dragons narration with a story-focused gesture.",
        ),
        (
            "diagram-building",
            "Building a diagram",
            1,
            "Actively constructing the explanation instead of only pointing.",
        ),
        ("annotating", "Annotating a passage", 2, "Distinguish close reading from drafting prose."),
        (
            "experimenting",
            "Experiment / discovery",
            3,
            "Curious exploration beyond a teacher role.",
        ),
    ],
    "engineering": [
        ("patch-review", "Reviewing a diff", 1, "Explicit comparison of before/after code."),
        (
            "log-investigation",
            "Investigating logs",
            2,
            "Follow evidence across a small set of diagnostic panels.",
        ),
        (
            "build-wait",
            "Waiting for a build",
            3,
            "A calmer working/rest blend; current listening/working can serve first.",
        ),
    ],
    "business": [
        (
            "design-critique",
            "Design critique",
            1,
            "Evaluate a layout or proposal rather than only business numbers.",
        ),
        (
            "delegating",
            "Delegating a task",
            1,
            "Make a clear handoff to another specialist visible.",
        ),
        (
            "report-delivery",
            "Delivering a report",
            2,
            "Present a completed result and the evidence behind it.",
        ),
        (
            "negotiating",
            "Weighing a tradeoff",
            3,
            "Show deliberate consideration of competing options.",
        ),
    ],
}
bindings = {
    "idle": "standing",
    "listening": "listening",
    "thinking": "thinking",
    "needs-clarification": "confused",
    "waiting-for-user": "listening",
    "blocked": "concerned",
    "error": "frustrated",
    "success": "celebrating",
    "greeting": "greeting",
    "resting": "tired",
    "goodnight": "lying-down",
}
plan = {
    "version": 1,
    "rules": [
        "States may reuse poses; a new application event does not always need new art.",
        "Playful adult poses require an explicit manual selection.",
        "Keep original glamour poses alongside sultry additions.",
        "Body part IDs remain stable across generated poses; occluded parts can be absent.",
    ],
    "stateBindings": bindings,
    "characters": {},
}
for role, items in manifest["characters"].items():
    plan["characters"][role] = {
        "available": [{k: item[k] for k in ["id", "label", "category"]} for item in items],
        "planned": [
            {
                "id": id,
                "label": label,
                "priority": priority,
                "reason": reason,
                "status": "planned_not_generated",
            }
            for id, label, priority, reason in common + special[role]
        ],
    }
text = json.dumps(plan, indent=2) + "\n"
(ROOT / "config/pose-plan.json").write_text(text)
(ROOT / "bfi/static/e-preview/assets/pose-plan.json").write_text(text)
print("Built pose inventory:", {r: len(p["available"]) for r, p in plan["characters"].items()})
