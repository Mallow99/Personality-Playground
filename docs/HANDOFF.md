# Continue the Best Friend Initiative

The repository now includes working handler/avatar integration. Start with
[avatar runtime and launch instructions](avatar-runtime.md), then
[the learning trail](learning.md) and [architecture decisions](architecture.md).

## Latest visual/control correction

`e-preview/art-review.html` shows every runtime pose with source comparison and
repair notes. Hacker flirty was replaced with a clear two-arm pose. All sprites
were reviewed in twelve contact pages; runtime copies remove neighboring fragments,
caption debris and pale matte edges. Fifteen work poses have local gaze edits.
Hide/show and loading-readiness bugs are fixed; controls are checked for rendered
outcomes. The source/learning record is in poses-v4 and docs/learning.md.

## Current result

- Chat uses the selected E artwork and matching Academic/Hacker/Business colors.
- 128 catalog entries: 74 authored/traced poses and 54 owner-approved transparent cutouts.
- Model-callable `avatar_catalog` and `avatar_set`, scoped to the speaking character,
  with actual tool results retained in reply provenance.
- Shared state across the in-app avatar and `/overlay` browser surface.
- Pose-local reading and seated Business hand movement, with restored rear surfaces.
  The other 126 entries remain intact images with reply cues.
- An optional PySide6 native overlay launcher, with topmost/transparency/click-through
  code. Native Windows behavior still needs execution and visual verification.
- A static mobile-friendly presentation preview in `e-preview/runtime-demo.html`.
  It is explicitly scripted and does not expose the local backend.

## Preserve these decisions

Keep set poses as the visual foundation. Avoid arbitrary anatomical slicing or
assuming one generic rig will preserve all poses. Full poseable-model research is
on the board under Later. Existing images remain useful as endpoint artwork and
future pose references. The 54 new ideas have images and specific reasons.
The owner explicitly approved all 54; config/pose-approvals.json records this.

The owner wants to understand the work and be able to explain it. Keep consequential
changes connected to code, validation and limitations in the learning/architecture
documents. Personality in model weights remains a goal; UI/prompt changes do not
establish trained individuals. Model selection, AMD performance, simultaneous
serving/fast swaps, LoRA serving, voice, autonomous jobs, frontier routing and computer
use still need separate implementation/evidence.

## First PC session

1. Run the app in mock mode; confirm pose choices, themes, captions and `/overlay`.
2. Install desktop extras and launch the native host in a second terminal. Check
   transparency, topmost behavior, drag, dock, scale, tray recovery and click-through.
3. Connect a real local model. Leave avatar tools off if its function template is
   unsupported; then enable them and inspect actual tool traces.
4. Inspect the approved library and suggest revisions where useful. Add local hand/face/prop pieces
   only where the pose supports them; do not launch another full-library remapping.

## Verification commands

```sh
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked --group browser python scripts/browser_avatar.py
uv run --locked --group browser python scripts/browser_smoke.py --chromium /usr/bin/chromium
```

The explicit Chromium executable above belongs to this Linux workspace; use an
installed browser or Playwright's supported installation on Windows. Native Qt was
not installed/tested here. Keep data, credentials, model files and private exports
outside Git. Continue on the `work` branch / draft PR #1; no merge was requested.
