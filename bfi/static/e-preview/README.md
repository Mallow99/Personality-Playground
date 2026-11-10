# E pose and whole-shape studio, revision 4

The owner-private hosted demo is linked in the project conversation and private
board. Locally open `/static/e-preview/index.html` with BFI running. Models, voice,
and computer control are independent of this visual proof.

All **74 poses** share the main library: 24 Academic, 26 Hacker, 24 Business.
Teasing, flirty, glamour, silly, and sultry are mixed in with other everyday poses.
The separate adult-studies section/filter is removed. No original artwork is deleted.

## Whole-shape mapping proof

Use **Compare Academic standing / seated**, then enable **Show mapped pieces**
and **Isolate selected part**. These two poses group complete connected source
forms into the face, hands, sleeves, book, torso, and continuous legs. A long leg
stays one piece instead of receiving arbitrary thigh/shin cuts. Source components
are named individually with `data-shape` and grouped under stable `data-part` IDs.

Enable **Drag pieces** to move a body group. Also enable **Drag single form** to
move one geometric form independently. Reset restores offsets. Form offsets reset
on pose changes; form IDs belong to a particular source pose. Body-group IDs match
across poses. Map download preserves both kinds of offsets.

These two whole-shape maps are the focused replacement proof. The remaining 72
poses retain earlier region maps and are labeled **LEGACY** in the inspector.
Tiny source-texture fragments still use estimated ownership. Where a hand/arm or
both legs form a continuous silhouette, source pixels contain no hidden authoring
layers. A deliberate authored joint would be required to separate that silhouette.
Do not mistake source fidelity for perfect anatomy or claim all mappings are fixed.

## Pose changes and talking

**Turn and reshape** moves the matched contours around their centers and turns
them toward the target orientation, with remaining shape interpolation. Compare it
with **Direct shape morph** and **Still swap**. Full target paths are restored at
rest; intermediate ring correspondence remains approximate. Character switching
continues to use its separate motif transition. Motion off/reduced motion disables
animated effects.

Talking has three selectable cue studies: voice marks beside the head, small
head/hand gestures, or both. A readable stage indicator remains useful without
animation. These are silent state cues, not audio-driven lip-sync or speech timing.
The original face geometry remains intact. Browser playback recordings are embedded.

## Pose approval

**Review 54 suggested poses** contains 24 shared concepts and 10 for each
individual, with purpose and silhouette notes. Every proposal begins unreviewed;
recommendations are not approvals. Keep/Revise/Skip and notes save in this browser.
**Download my decisions** exports a JSON file to share. Nothing is sent to a model,
GitHub, or Notion automatically. See [the written checklist](../../../docs/pose-plan.md).

## Build and inspect

`config/rigs/academic.json` identifies the whole-shape proof and explicit major
component assignments. The builder groups complete color components without region
intersection in this mode. Legacy maps still use joint regions and hand overrides.
`.rig.json` records source components, grouping, guides, geometry, and source hashes;
`.rig.svg` is the assembled export. The new pair retains over 99.99% silhouette
occupancy overlap with unsplit vectors at source resolution.

```sh
uv run --with numpy --with cairosvg --with shapely python scripts/build_e_rigs.py academic/standing academic/seated
python scripts/build_e_pose_plan.py
node scripts/check_e_preview.mjs
uv run --locked --group browser python scripts/browser_e_preview.py
```

The 17 registered anatomical/prop IDs are a compatibility interface, not a demand
to cut every drawing into 17 pieces. Original generated sheets, direct traces,
source crops, normalized references, exact boundary alternatives, and wipe views
remain inspectable. Ordinary chat artwork remains the earlier prototype.

## Illustrated proposal review

All 54 suggestions now have a generated concept image and a specific reason.
The shared 24 ideas rotate the demonstrating character; the 30 specialist ideas
use their own character. Tap a picture for an enlarged view and rationale, or open
its original six-cell sheet. CSS displays one cell from a preserved source PNG;
these images have not been traced or added to the active 74-pose animation library.

`pose-review-reasons.json` and the proposal source manifests feed the plan builder.
Exported decisions include the sheet hash and cell so the reviewed picture remains
identifiable. Saved choices retain the same review codes. Validate image coverage,
hashes, modal behavior, and phone layout with `scripts/check_e_preview.mjs` and
`uv run --locked --group browser python scripts/browser_e_review.py`.
