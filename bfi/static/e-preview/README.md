# E avatar preview and approved pose library

`index.html` opens `runtime-demo.html`, the scripted presentation of the same E
renderer used by the local handler. It has 128 catalog entries: 74 existing SVG
poses and 54 owner-approved transparent cutouts. The owner-private hosted URL is
kept in the conversation and private board. No model, chat history, or local API
is exposed by this static preview.

- **Handler presentation:** `runtime-demo.html` — switch roles, poses, matching
  themes, text reply cues, visibility and motion. All replies here are scripted.
- **Full runtime visual review:** `art-review.html` — all 128 packaged sprites,
  source comparison, background choices and per-pose repair notes.
- **Approved proposals:** `pose-library.html` — all 54 images with reasons and
  source references. The approved baseline defaults to Keep. Existing saved
  revision choices take precedence; exporting decisions remains local.
- **Reading layer inspection:** `limited-motion.html` — compare the original,
  pause/scrub local movement, and reveal complete book material behind both hands.
- **Business layer inspection:** `runtime-demo.html?pose=business/seated` — turn
  motion off and use Reveal rear layer to inspect the thigh beneath the hand.
- **Historical mapping lab:** `mapping-lab.html` — retained for learning and source
  comparisons. Its approximate region maps and morphs are not the production
  renderer and do not establish complete rear surfaces.

## What moves

Academic reading groups whole source contours into head, book and hands, with the
body fixed. Authored olive page material lies beneath both hands. The seated
Business example has a whole hand above restored navy thigh material; only that
hand rotates slightly. These are pose-local layers, not a universal skeleton.
The other 126 entries remain intact sprites. Reduced motion disables local motion.
Talking uses a silent timed reply cue, not voice playback or lip sync.

The repair deliberately changes the reading footprint where missing material was
exposed: source silhouette overlap is 99.50%. Silhouette similarity alone did not
catch the earlier defect. The builder also hides front hands and checks pixels on
the rear surfaces. Originals and source hashes remain available.

## Rebuild and verify

```sh
python scripts/build_e_pose_plan.py
uv run --with numpy --with cairosvg --with shapely python scripts/build_limited_motion.py
uv run --locked python scripts/build_avatar_clean.py
uv run --with numpy --with pillow --with cairosvg --with shapely python scripts/build_avatar_catalog.py
uv run --with numpy --with cairosvg --with shapely python scripts/check_avatar_art.py
uv run --locked python scripts/build_avatar_review.py
node scripts/check_e_preview.mjs
uv run --locked --group browser python scripts/browser_e_review.py
uv run --locked --group browser python scripts/browser_limited_motion.py
uv run --locked --group browser python scripts/browser_avatar.py
uv run --locked --group browser python scripts/browser_avatar_controls.py
```

The catalog builder copies the actual renderer, catalog and cutouts into
`avatar-runtime/` so the private static demo can run without the local backend.
For real handler tools, shared overlay state and native launch instructions, read
`docs/avatar-runtime.md`. For the completion boundary, see `docs/COMPLETION-REVIEW.md`.

The source art, prior experiments, 74 SVGs, whole-shape maps and earlier recordings
are retained. Shared proposal ideas have one demonstrating character each; they do
not silently become three different character images.

## Edge and gaze revision

All 54 PNGs now unmix the white source matte from edge RGB, and the shared renderer
no longer adds a pale outline. Use the demo's Studio, Theme, Light and Dark surfaces
to inspect the result. Thinking selects a real thinking pose; Hide removes the
rendered avatar; Idle ends the reply cue. Each action reports its result. Reveal
only appears for supported layered poses, and a still pose says what Motion affects.

Fifteen main work poses have explicit local eye corrections, pointing toward their
book, workbench, keyboard, panel or report. Other poses retain their authored gaze.
The original source artwork remains unchanged; focus variants and their configuration
are separate. Rebuild focus variants after rebuilding the reading layers.

## V5 candidate

Business now uses a consistent two-eye design. The regenerated working/report
clipboards face the character: their visible backs are plain and opaque. The paper
is on the far side. Display boards remain presentation poses with solid paper.
All 128 sprites have dark-background variants; Auto changes the artwork palette
as well as the background. Explicit Light/Dark is available in the app and overlay.
The owner has not yet approved this candidate. See poses-v5 for source references.
Run check_avatar_design.py and browser_avatar_design.py for material, contrast and
shared-control checks. Authored head transforms remain intact when motion stops.
