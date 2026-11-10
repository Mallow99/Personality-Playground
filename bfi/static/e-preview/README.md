# E pose studio, revision 2

The private hosted preview is linked in the project conversation and board. Locally,
open `/static/e-preview/index.html` with BFI running. This static page makes no model
calls and does not operate the computer. Ordinary chat artwork is unchanged.

The owner rejected the original hand-built E SVGs. This revision generated nine
pose sheets **before** conversion and directly traced 54 poses, 18 per character.
The [source record](../../../research/visual-studies/poses-v2/README.md) preserves
the sheets, crop bounds, method, and limitations. Earlier approximations are archived.

Each role has 11 everyday poses, three specialist poses, and four optional adult
playful studies. Academic includes reading, chalkboard teaching, prose writing, and
Dungeons & Dragons planning. Hacker includes security review, coding, and debugging.
Business includes coordination, formal reports, and task completion. The playful
set is a manual choice, not an automatic working state.

The preview includes generated-source, normalized-reference, SVG and wipe views,
face/motif icons, role cursor exports, revised motif transitions, speaking gestures,
and appearance/pose controls. A speaking gesture is not lip synchronization or audio.

## Fidelity

Each SVG follows the actual reference pixel boundaries. Palette normalization
removes generated texture and keeps three distinct colors per role. All 54 exact boundary traces match their normalized reference's occupancy at
source resolution. The displayed SVGs clean the contours within 0.75 source pixels
for crisp scaling; occupancy overlap is 99.03–99.69% and palette agreement on
shared occupied pixels is 99.67–99.93%. Both versions are inspectable. That does not prove pose quality, agreement with E, or pixel equality
to the unnormalized generated source. Inspect the source/SVG slider yourself.
These are contour traces, not yet semantic head/arm/prop rigs.

## Reusable interfaces

`CharacterActor.setPose(pose, profile)` loads a catalog pose with stale-response
protection. `setSpeaking`, `show`, `hide`, and `destroy` are presentation controls.
`explaining` remains an alias for the character's specialist explanation pose.
`poseForActivity(profile, activity)` suggests a visual mapping; it grants no tools.
`MotifTransition.play(profile)` and `stop()` manage the revised cancellable WAAPI
motifs. Skip/Escape, reduced motion, and Motion off end their animations cleanly.
`AgentCursor.update({profileId, shape, x, y})` positions an input-transparent pointer
at its hotspot. It does not click or install a native operating-system cursor.

## Reproduce

```sh
UV_CACHE_DIR=/tmp/bfi-uv-cache uv run --with cairosvg --with numpy python scripts/trace_e_poses.py
node scripts/check_e_preview.mjs
uv run --locked --group browser python scripts/browser_e_preview.py
```

Run from repository root. The trace manifest contains source/vector hashes and
comparison measurements. Browser screenshots and recordings are saved under ignored
`runs/e-preview-v2`. Exported sheets are regenerated with `node scripts/export_e_art.mjs`.

## Verification of revision 2

Real Chromium checks passed all 54 pose selections, source/reference/vector image
loads, category filters, desktop/tablet/phone widths, motif playback/cancellation,
rapid switching, speaking/appearance sequence, reduced motion, and cursor sampling,
with no page errors. Screenshots were inspected. The playback videos in the page
are actual Chromium recordings at native timing, not rendered SVG-frame exports.
Record them again using `uv run --locked --group browser python scripts/record_e_preview.py`.
The code/palette and trace checks, Ruff, and 43 existing Python tests passed.
