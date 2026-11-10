# E poses, generated before tracing

The owner rejected the previous hand-built SVG interpretation and slideshow-like
transitions. The original E design stays selected. These nine new generated sheets
were created first, using E as the character reference; SVG conversion followed.
Two earlier transparent generations with unwanted glow were rejected, not traced.

| Character | Everyday poses | Reactions and work | Specialist and playful |
| --- | --- | --- | --- |
| Academic | [A](academic-a.png) | [B](academic-b.png) | [C](academic-c.png) |
| Hacker | [A](engineering-a.png) | [B](engineering-b.png) | [C](engineering-c.png) |
| Business | [A](business-a.png) | [B](business-b.png) | [C](business-c.png) |

Each character has 18 poses: standing, standing 2, seated, seated 2, tired, lying
down, thinking, working, laughing, frustrated, exasperated, three specialty poses,
and four optional adult playful studies (teasing, flirty, fully clothed glamour,
silly). Academic specialties are reading, chalkboard explanation, and writing
prose; working includes tabletop/Dungeons & Dragons planning. Hacker specialties
are security review, coding, and debugging. Business specialties are coordination,
formal reports, and task completion. These are visual activities, not new agent tools.

## Conversion and what the measurements mean

`sources.json` records each source sheet, pose order, and label-gutter crop bounds.
`scripts/trace_e_poses.py` extracts each original cell without stretching the body,
normalizes generation texture to that character's documented three-color palette,
and follows the actual pixel boundaries into SVG compound paths. It does not redraw
anatomy, approximate a seated silhouette from memory, or embed a raster in an SVG.
An initial simplified vectorizer lost fine boundaries and was rejected.

The output lives in `bfi/static/e-preview/assets/poses/`. Each pose has the cropped
generated source, normalized transparent reference, and SVG. `manifest.json`
records hashes, crop rectangles, source-resolution geometry overlap and color
agreement. All 54 exact `.boundary.svg` traces reproduce the normalized occupancy at 512×512.
The displayed `.svg` uses at most 0.75 source pixels of contour cleanup for crisp
scaled edges: measured occupancy overlap is 99.03–99.69%, and palette agreement
on shared occupied pixels is 99.67–99.93%. Both variants remain available.

Those measurements establish conversion fidelity to the **normalized reference**.
They do not establish identity consistency, pose quality, agreement with E, or
pixel equality to the textured generated PNG. The live wipe comparison and the
unaltered source sheets make those visual judgments inspectable. The exact boundary option retains source pixel steps. The default uses bounded
edge cleanup. Neither is yet a semantic production rig. Semantic head/arm/prop groups require a separate careful rigging
pass that preserves the contours.

## Reproduce

```sh
UV_CACHE_DIR=/tmp/bfi-uv-cache uv run --with cairosvg --with numpy python scripts/trace_e_poses.py
node scripts/check_e_preview.mjs
uv run --locked --group browser python scripts/browser_e_preview.py
```

Trace comparison PNGs and browser screenshots/video are written under ignored
`runs/`. The ordinary chat artwork remains the earlier prototype. The rejected
hand-built E poses are retained in `../rejected-e-proof/` for history.
