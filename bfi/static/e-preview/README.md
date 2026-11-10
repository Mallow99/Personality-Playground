# E pose and body-piece studio, revision 3

The owner-private hosted demo is linked in the project conversation and private
board. Locally open `/static/e-preview/index.html` with BFI running. This preview
runs without models or computer control; ordinary chat artwork remains unchanged.

There are **74 poses**: Academic 24, Hacker 26, Business 24. New greeting, listening,
confused, celebrating, concerned, and sultry poses supplement the existing library.
The Hacker specialist poses were regenerated with coding, debugging, security
review, working, testing, and code review. Original glamour poses remain unchanged.
The [pose plan](../../../config/pose-plan.json) separates available artwork, proposed
additions, priorities, reasons, and application states that can reuse poses.

## Try the pieces

Choose a pose in the stage dropdown, then another pose. Each character has the same
17 body-piece IDs: head, neck, torso, upper arms, forearms, hands, thighs, shins,
feet, and two props. Visible pieces move/morph to their counterpart in the next pose.
Absent/occluded pieces may collapse or appear. The full target paths are restored
at the end; intermediate outlines use sampled geometry and can look intentionally
mechanical. Changing characters uses its separate motif transition.

Under **Piece by piece**, enable outlines, select/click a body part, and move or
rotate it. Drag pieces can be enabled for direct movement. Reset restores the
preview offsets. Download piece map exports guides, named paths, pivots, and preview
offsets. Subtle piece motion is independently switchable. Motion off/reduced motion
settles immediately on the target pose and disables drift. A speaking gesture does
not imply audio or lip synchronization.

## How it is built

Original generated sheets and frame corrections are recorded under
`research/visual-studies/poses-v2` and `poses-v3`. Direct contour traces, source PNGs,
normalized references, exact-boundary alternatives, and wipe views remain inspectable.
Crop spill is corrected through explicit frames, not by clipping missing limbs.

`config/rigs/*.json` contains per-pose joint guides, head bounds, prop regions, and
occlusion notes. These are draft estimates that can be corrected. The builder maps
foreground to named bones/props, intersects those regions with the existing SVG
contours, and writes `.rig.svg` and `.rig.json` without redrawing the character.
Reassembled rigs currently retain at least 99.7% silhouette overlap with their
unsplit vectors at source resolution. This is a rendering measure, not proof that
every anatomical assignment is right. Inspect the piece maps, especially crossed
arms and occluded limbs. They are prototypes, not motion-capture anatomy.

## Interfaces

`CharacterActor.setPose(pose, profile)` now interpolates semantic pieces, with stale
loads/cancellation protection. `setSpeaking`, `show`, `hide`, `destroy` remain.
`setIdle`, `showParts`, `selectPart`, `setPartOffset`, `resetParts`, and `exportRig`
serve the inspector. Guides stay inspectable in source-cell coordinates; frame
matrices map them into each exported pose canvas. Morphing is independent of model
loading, tools, and personality training.

## Reproduce

```sh
uv run --with cairosvg --with numpy python scripts/trace_e_poses.py
uv run --with cairosvg --with numpy --with shapely python scripts/build_e_rigs.py
python scripts/build_e_pose_plan.py
node scripts/check_e_preview.mjs
uv run --locked --group browser python scripts/browser_e_preview.py
```

Run from the repository root. `rig-report.json` records coverage and reassembly
checks. Source comparisons and rig debug masks are saved under ignored `runs/`.
Browser recordings are genuine Chromium playback, without audio or model calls.

Reading, coding, and formal-report hand maps now use explicit ownership polygons
and palette filters to separate fingers from sleeves and held objects. Other
maps remain joint-based drafts. Pass optional `role/pose` arguments to the rig
builder to rebuild selected poses while keeping the rest of the report intact.
