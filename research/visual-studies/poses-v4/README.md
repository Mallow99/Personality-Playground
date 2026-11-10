# Hacker flirty repair and visual audit

The owner identified a missed correction: the original Hacker flirty sprite had
only one readable arm and an awkward torso/hip. Its original sheet remains in
poses-v2, and a before image is retained under the preview's assets/revisions.

`engineering-flirty-generated.png` is the full, unmodified transparent edit.
`engineering-flirty-normalized.png` fits the opaque figure into the existing
512px pose canvas on white. Both arms and hands are explicit: one hand on the hip,
one at the collar. Legs are balanced; the exaggerated old hip shape is removed.

The source manifest's per-pose override replaces this pose only. Rebuild with:

```sh
uv run --with numpy --with cairosvg python scripts/trace_e_poses.py --only engineering/flirty
uv run --with numpy --with cairosvg --with shapely python scripts/build_e_rigs.py engineering/flirty
uv run --locked python scripts/build_avatar_clean.py
uv run --with numpy --with pillow --with cairosvg --with shapely python scripts/build_avatar_catalog.py
uv run --locked python scripts/build_avatar_review.py
```

The original glamour sources are unchanged. The refreshed legacy flirty guide no
longer marks an arm hidden; it remains an archived draft, not a production rig.
Runtime uses the complete new sprite. Source/vector comparison measures 99.5153%
silhouette overlap and 99.8288% palette agreement, alongside visual inspection.

The broader review inspected all 128 runtime entries in twelve role contact pages.
It found neighboring-figure fragments in Hacker tired and baseline/caption debris
in multiple vectors and PNGs. Runtime copies remove those fragments; intact source
references remain available. Fifteen work poses have small explicit eye edits.
The full library/source comparison is in `art-review.html`; the review record is
`config/avatar-visual-review.json`. The review does not claim universal rigging.
