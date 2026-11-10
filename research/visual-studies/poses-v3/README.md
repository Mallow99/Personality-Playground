# Pose additions and semantic body maps

The owner accepted the previous reference poses except the Hacker specialty set,
asked to retain all glamour poses, and requested sultry additions, a fuller pose
inventory, independent body pieces, matched-piece morphs, and small piece motion.

- [Hacker specialist revision](engineering-specialist.png): coding, debugging,
  security review, working, testing, code review.
- [Academic additions](academic-new.png), [Hacker additions](engineering-new.png),
  [Business additions](business-new.png): greeting, listening, confused,
  celebrating, concerned, sultry. All are adult stylized characters.
- [Retained glamour hashes](retained-glamour.json) preserve the previous references
  and vectors. They were not replaced by the sultry additions.

The reclining figures spill outside their generated grid cells. Explicit wider
frames preserve hands and heads, and remove neighboring fragments from Concerned.
Small source spill in Hacker resting/testing/review poses is similarly corrected.
Frame bounds and cell-to-canvas matrices are stored with the source manifest.

The [complete pose inventory](../../../config/pose-plan.json) lists 74 available
poses and prioritized missing artwork. Planned entries are clearly not generated.
States such as waiting, blocked, or success can reuse suitable poses instead of
requiring a new drawing for every application event.

## Body pieces

[Academic](../../../config/rigs/academic.json),
[Hacker](../../../config/rigs/engineering.json), and
[Business](../../../config/rigs/business.json) have per-pose joint/head/prop guides.
Seventeen stable anatomical IDs are present in every rig. Left/right refer to the
character's own sides; crossed limbs need careful review. All guide ownership is
marked draft. Occlusion is recorded instead of inventing visible hidden limbs.

The builder partitions the existing shapes with those guides, then intersects with
the source contours. It retains the artwork, rather than redrawing a hand for each
state. The actor samples and aligns rings within the same part/color during pose
changes, and restores the complete target paths at rest. This is deliberately a
geometric, somewhat mechanical transition, not a claim of natural human movement.

The studio exposes part selection, outlines, dragging, translation/rotation,
independent idle drift, morph speed, and map export. Correct the source guides and
rebuild when a piece owns the wrong region. Preview offsets do not rewrite the
reference artwork. See the [studio guide](../../../bfi/static/e-preview/README.md).
