"""Build the pose inventory and an owner-review checklist; never infer approval."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "bfi/static/e-preview/assets/poses/manifest.json").read_text())
# Code, name, useful context, distinguishing silhouette/gesture.
shared = [
    (
        "pointing-left",
        "Pointing left",
        "Guide an explanation",
        "One clear extended arm; other hand relaxed.",
    ),
    (
        "pointing-right",
        "Pointing right",
        "Direct attention elsewhere",
        "A separately authored opposite gesture, keeping anatomical identity.",
    ),
    (
        "open-palm",
        "Open-palm presentation",
        "Introduce an option",
        "One open palm, upright relaxed posture.",
    ),
    (
        "small-wave",
        "Small wave",
        "Casual greeting or goodbye",
        "Compact raised hand with readable fingers.",
    ),
    (
        "polite-bow",
        "Polite bow",
        "Acknowledge a request or thank someone",
        "Slight torso tilt, hands kept clear.",
    ),
    (
        "leaning-listen",
        "Leaning in to listen",
        "Attentive conversation",
        "Forward tilt and open shoulders, no work prop.",
    ),
    (
        "curious-inspection",
        "Curious inspection",
        "Notice an unfamiliar detail",
        "Head tilted toward a small floating detail.",
    ),
    (
        "chin-rest",
        "Chin resting on hand",
        "Quiet contemplation",
        "Seated elbow support with face and hand separated.",
    ),
    (
        "eureka",
        "Eureka",
        "Connect two ideas",
        "Raised finger, lifted head, sudden confident posture.",
    ),
    (
        "skeptical",
        "Skeptical",
        "Disagree or question evidence",
        "One raised brow/tilted head; asymmetrical arm gesture.",
    ),
    ("surprised", "Surprised", "Unexpected result", "Hands slightly spread and shoulders lifted."),
    (
        "reassuring",
        "Reassuring",
        "Encourage without lecturing",
        "Open hand offered forward, soft lean.",
    ),
    (
        "apologetic",
        "Apologetic / correcting",
        "Acknowledge a mistake",
        "Small downward head tilt and corrective hand gesture.",
    ),
    (
        "relieved",
        "Relieved",
        "A quiet successful outcome",
        "Lowered shoulders, hand against chest or side.",
    ),
    (
        "disappointed",
        "Disappointed",
        "A setback worth acknowledging",
        "Slumped but attentive posture, no exaggerated despair.",
    ),
    (
        "embarrassed",
        "Embarrassed",
        "An awkward or funny moment",
        "Turned head and one hand near cheek.",
    ),
    (
        "determined",
        "Determined",
        "Commit to a difficult task",
        "Firm stance and forward-facing shoulders.",
    ),
    (
        "smug",
        "Smug / teasing",
        "A sharp but playful observation",
        "Hip shift, tilted head, one small presenting gesture.",
    ),
    (
        "arms-folded-amused",
        "Arms folded, amused",
        "A dry joke lands",
        "Relaxed crossed arms; tilted head.",
    ),
    (
        "deadpan",
        "Deadpan",
        "Understated humor",
        "Still upright silhouette and one minimal hand gesture.",
    ),
    (
        "facepalm",
        "Facepalm",
        "React to a silly mistake",
        "One hand to brow; face shape remains legible.",
    ),
    (
        "double-take",
        "Double take",
        "React, then reconsider",
        "Over-shoulder head turn with paused body.",
    ),
    ("stretching", "Stretching", "Take a break", "Arms overhead, long angular silhouette."),
    (
        "sleepy-nod",
        "Sleepy nod",
        "Wind down after a long session",
        "Seated with lowered head, supported by one hand.",
    ),
]
special = {
    "academic": [
        (
            "storytelling",
            "Storytelling / DM narration",
            "Narrate prose or a D&D scene",
            "Book aside; broad narrative gesture.",
        ),
        (
            "diagram-building",
            "Building a diagram",
            "Explain visually",
            "One hand places a shape, the other links it.",
        ),
        (
            "annotating",
            "Annotating a passage",
            "Close reading",
            "Book or page flat, writing hand distinct.",
        ),
        (
            "experimenting",
            "Experiment / discovery",
            "Follow a curious question",
            "Simple experiment prop and attentive lean.",
        ),
        (
            "comparing-books",
            "Comparing sources",
            "Weigh conflicting explanations",
            "Two books/pages held at different heights.",
        ),
        (
            "rolling-dice",
            "Rolling dice",
            "Resolve a tabletop action",
            "Hand just released, a few geometric dice.",
        ),
        (
            "dm-screen",
            "Behind a DM screen",
            "Run a tabletop scene",
            "Head and hands visible above a simple screen.",
        ),
        (
            "world-map",
            "Building a world map",
            "Plan a setting",
            "Seated over a map, pointing and drawing hands separated.",
        ),
        (
            "reading-aloud",
            "Reading aloud",
            "Deliver prose or explain a quotation",
            "Book in one hand, conversational free hand.",
        ),
        (
            "quill-pause",
            "Writer pausing mid-sentence",
            "Consider wording",
            "Pen suspended above a page, tilted head.",
        ),
    ],
    "engineering": [
        (
            "patch-review",
            "Reviewing a diff",
            "Compare a proposed code change",
            "Two small panels, a precise pointing gesture.",
        ),
        (
            "log-investigation",
            "Investigating logs",
            "Follow diagnostic evidence",
            "Lean toward a narrow stack of log panels.",
        ),
        (
            "build-wait",
            "Waiting for a build",
            "A quiet working pause",
            "Sideways seated, one foot moving lightly.",
        ),
        (
            "terminal-focus",
            "Terminal focus",
            "Inspect a local terminal session",
            "Compact forward lean with both hands at keyboard.",
        ),
        (
            "breakpoint",
            "At a breakpoint",
            "Explain paused program state",
            "One hand on keyboard, other indicates a single variable.",
        ),
        (
            "tests-pass",
            "Tests passed",
            "A small earned victory",
            "Brief fist lift or satisfied lean back.",
        ),
        (
            "local-reproduction",
            "Reproducing a bug locally",
            "Check a controlled example",
            "One small test window, concentrated asymmetric pose.",
        ),
        (
            "dependency-tangle",
            "Untangling dependencies",
            "Make a confusing system readable",
            "Holds a knot of links, separates one connection.",
        ),
        (
            "system-sketch",
            "Sketching a system",
            "Design architecture",
            "Side-on at a board with a few boxes and arrows.",
        ),
        (
            "keyboard-flourish",
            "Keyboard flourish",
            "Silly confidence after finishing",
            "An angular keyboard balanced in one hand.",
        ),
    ],
    "business": [
        (
            "design-critique",
            "Design critique",
            "Evaluate a layout or proposal",
            "Standing beside a layout, one measured gesture.",
        ),
        (
            "delegating",
            "Delegating a task",
            "Make a clear handoff",
            "Hands a task card toward another character.",
        ),
        (
            "report-delivery",
            "Delivering a report",
            "Present a finished result",
            "Closed report offered forward.",
        ),
        (
            "negotiating",
            "Weighing a tradeoff",
            "Consider competing options",
            "Two open hands at unequal heights.",
        ),
        (
            "prioritizing",
            "Prioritizing",
            "Choose what matters next",
            "Moves one task card above a short stack.",
        ),
        (
            "meeting-listen",
            "Listening in a meeting",
            "Receive context before deciding",
            "Seated, hands calmly together, slight forward lean.",
        ),
        (
            "budget-review",
            "Checking a budget",
            "Review money and constraints",
            "Spreadsheet beside a small calculator; pointing hand clear.",
        ),
        (
            "job-monitoring",
            "Monitoring a long task",
            "Check progress during agentic work",
            "Standing at a compact progress board.",
        ),
        (
            "risk-review",
            "Reviewing a risk",
            "Flag a consequential tradeoff",
            "One hand holds a caution card, other steadies report.",
        ),
        (
            "closing-laptop",
            "Closing the laptop",
            "Wrap up and report completion",
            "Hand on closing lid, relaxed shoulders.",
        ),
    ],
}
proposals = []
for prefix, role, rows in [
    ("S", "shared", shared),
    ("A", "academic", special["academic"]),
    ("H", "engineering", special["engineering"]),
    ("B", "business", special["business"]),
]:
    for n, (slug, label, reason, visual) in enumerate(rows, 1):
        proposals.append(
            dict(
                code=f"{prefix}{n:02}",
                id=slug,
                role=role,
                label=label,
                reason=reason,
                visual=visual,
                recommended=n <= 4,
                status="unreviewed",
            )
        )
# Generation was explicitly requested for all concepts; approval remains a separate decision.
reasons = json.loads((ROOT / "config/pose-review-reasons.json").read_text())
image_manifest = ROOT / "research/visual-studies/pose-proposals/images.json"
images = json.loads(image_manifest.read_text()) if image_manifest.exists() else {}
for proposal in proposals:
    proposal["useCase"] = proposal["reason"]
    proposal["reason"] = reasons[proposal["code"]]
    if proposal["code"] in images:
        proposal["image"] = images[proposal["code"]]

review = dict(
    version=1,
    title="Suggested poses for owner review",
    proposals=proposals,
    rules=[
        "No suggestion is approved automatically.",
        "Available art is separate from proposed additions.",
        "Personality and humor extend beyond job specialty.",
    ],
)
plan = dict(
    version=2,
    rules=[
        "Poses can be reused across application states.",
        "All existing expressive poses appear in the main library.",
        "Generated concepts remain unapproved until the owner reviews them.",
        "Whole-shape mapping proof currently covers Academic standing/seated only.",
    ],
    stateBindings={
        "idle": "standing",
        "listening": "listening",
        "thinking": "thinking",
        "blocked": "concerned",
        "success": "celebrating",
    },
    characters={},
)
for role, items in manifest["characters"].items():
    plan["characters"][role] = {
        "available": [{k: p[k] for k in ["id", "label", "category"]} for p in items],
        "planned": [
            {**p, "priority": 1 if p["recommended"] else 2, "status": "proposed_not_approved"}
            for p in proposals
            if p["role"] in ["shared", role]
        ],
    }
for name, data in [("pose-plan", plan), ("pose-review", review)]:
    text = json.dumps(data, indent=2) + "\n"
    (ROOT / f"config/{name}.json").write_text(text)
    (ROOT / f"bfi/static/e-preview/assets/{name}.json").write_text(text)
lines = [
    "# Suggested poses for sign-off",
    "",
    (
        "54 proposed pose concepts: 24 shared, then 10 for each individual. Each now has a "
        "generated concept image and a reason; none is approved automatically. "
        "Existing 74 poses remain available, including "
        "teasing, flirty, glamour, silly, and sultry in the main library."
    ),
    "",
    (
        'Reply with codes (for example, "keep S01–S04 and A01; revise H03") or use the '
        "live checklist and download your decisions. Shared means one concept adapted "
        "separately for each character. First four per group are recommended starting "
        "points, not approvals."
    ),
    "",
]
for role, label in [
    ("shared", "Shared — range beyond a specialty"),
    ("academic", "Academic — explanation, prose, curiosity, D&D"),
    ("engineering", "Hacker — code, diagnostics, personality"),
    ("business", "Business — design, planning, long tasks"),
]:
    lines += ["## " + label, ""]
    for p in proposals:
        if p["role"] == role:
            lines += [
                f"- [ ] **{p['code']} · {p['label']}** — {p['reason']} Pose: {p['visual']} "
                f"([image sheet, cell {p['image']['row'] * 3 + p['image']['column'] + 1}]"
                f"(../bfi/static/e-preview/{p['image']['sheet']}))"
            ]
    lines += [""]
lines += [
    "## Review and animation direction",
    "",
    (
        "Decide which silhouettes and gestures earn new artwork. Thinking, writing, "
        "listening, and speaking need distinct states, but a new application event need"
        " not require a new drawing. Talking can use voice marks, small gestures, and a"
        " readable speaking indicator. The current proof is silent and is not lip-sync."
    ),
    "",
    (
        "Whole connected forms are being grouped intact for Academic standing/seated. "
        "Their face, hands, sleeves, book, and continuous legs travel as meaningful "
        "shapes. Joined forms are not automatically divided into anatomical joints. The"
        " rest of the library retains legacy region maps pending refinement. Pose "
        "changes offer turning contours, direct morphing, and a still comparison."
    ),
    "",
]
(ROOT / "docs/pose-plan.md").write_text("\n".join(lines))
print(f"Built {len(proposals)} unreviewed pose suggestions.")
