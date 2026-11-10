# Business v5 candidate: consistent eyes and inward writing boards

The owner identified unresolved dark-background readability, lost Business quality,
hollow-looking clipboard cells and inconsistent one-eye/cyclops face construction.
They then clarified that the writing clipboard must face him, so the viewer cannot
see the paper. This supersedes the earlier presentation-facing writing examples.

- `business-design-reference.png` supplies front, three-quarter and downward
  two-eye heads. Its lower writing boards still face the viewer and are **not** the
  writing reference used in the final candidate.
- `business-inward-clipboard-reference.png` replaces those writing examples. The
  viewer sees the plain rear of the board, with the paper and pen nib on his side.
- `config/avatar-design-v5.json` stores head crops, material planes, pose exceptions
  and distinct dark palettes. `scripts/build_avatar_design.py` implements them.

The candidate updates all 42 Business runtime entries while retaining most body
poses. Forehead-hand overlaps use local face edits. Closed resting eyes remain
closed. The working and formal-report endpoints are regenerated and traced from
true-alpha foreground masks; pale fingers remain opaque. An authored navy plane
completes each board beneath its gripping fingers. Source sheets and previous
runtime URLs remain inspectable.

All 128 runtime entries have a separate role-colored dark variant. Auto chooses
using the app surface; explicit Light/Dark covers unknown desktop backgrounds.
There are no pale edge glows. The three colors in each dark palette remain distinct
from the other characters' colors. The owner can compare the candidate in the
runtime demo and all-pose review; aesthetic approval is still open.

Rebuild and check:

```sh
uv run --locked python scripts/build_avatar_clean.py
uv run --with numpy --with pillow --with cairosvg --with shapely python scripts/build_avatar_catalog.py
uv run --locked python scripts/build_avatar_review.py
uv run --with numpy --with cairosvg python scripts/check_avatar_design.py
uv run --locked --group browser python scripts/browser_avatar_design.py
```

The catalog builder also copies the exact renderer and assets into the static
preview. It does not publish the local API, model endpoint or private history.
