# Handoff: local handler and paused visual work

## Personality workshop drafts

The owner now wants to build the three personalities together before training.
Read [personality-drafts.md](personality-drafts.md): their suggested Academic name
is Olive; Violet (Hacker) and Slate (Business) are assistant-proposed color names.
The drafts develop eccentric teacher/writer, sassy technical partner and serious
coordinator directions. Names and elaborations remain open for discussion.

The owner dislikes dialogue or exposed reasoning that narrates reading persona
instructions. The drafts call for natural task-facing speech, not repeated role
introductions, forced mannerisms or fabricated memories. Prompts still condition
the model; this is not proof the traits are learned or control over internal thought.
No runtime personalities were activated, model training performed, or artwork changed
in this workshop. Stable approved behavior may later inform a curated LoRA/QLoRA
dataset; raw memories and model-generated preferences are not automatically training
data. Capability regressions and the exact starting model still need evaluation.

## Memory sleep and personality controls (2026-11-12)

The owner requested smarter recall, sleep-time consolidation/correction, and a
place to configure the three personalities before crafting them together. They
specifically asked to check existing systems and avoid starting from scratch.

The same `bfi/handler-core` branch / draft PR #2 now adds LangMem-backed typed
review, reversible exact duplicate merges, conflict flags, alternate recall keywords,
importance and a recall inspector. Sleep is manual or idle-triggered and yields
to chat. It reviews saved memories, not raw conversation extraction or model weights.
Only exact duplicates apply automatically; other edits remain inspectable proposals.
Stale edits and unsafe undo are rejected. Forget includes linked consolidations
and relevant review snapshots. The app must be running for idle sleep to work.

`/personalities` exposes independent, persistent settings for Academic, Engineering
and Business, prompt preview, revisions, restore and export. These are deliberately
provisional scaffolds. New chats snapshot the active revision; old chats stay stable.
No final personality, training, GPU performance, voice/media or visual approval is
implied. Review [the implementation guide](handler.md) and
[the comparison note](../research/tooling/memory-sleep-2026-11-12.md).

Validation covers 104 backend tests, Ruff, existing Chromium chat smoke and expanded
handler browser flows. The new flows exercise real LangMem library/HTTP integration
using a simulated tool-capable server, merge/undo, recall enrichment, and personality
save/reload/isolation. Real-model memory quality is still unmeasured.

## Handler checkpoint (2026-11-11)

The owner delegated best judgment on the initial tooling and asked for a working
handler now, with a deeper review later. The implementation is on
`bfi/handler-core`, based on `work` at `ef00ef2`; it does not resume visual work.
Start with [the handler guide](handler.md). Its first version adds:

- Replaceable loopback runtime presets, profile routing, sampling/context controls,
  and a `/handler` setup/inspection workspace.
- Persistent single-resource generation jobs with cancellation, idempotent
  submission, reload recovery, and interruption without replay after restart.
- Actual SSE previews for plain-text compatible requests. Tool-loop replies remain
  buffered; failed/incomplete streams never become successful conversation pairs.
- Owner-saved memory with profile/shared scopes, source references, corrections,
  forgetting, export, and explicit context inclusion. No model-written memory or
  background extraction is enabled.
- A `/library` search/import/export UI backed by SQLite FTS5. The two original
  reports and 168-URL source catalog are versioned in `research/tooling/`.
  Model research tools are read-only and opted in per message.

The full reports and handler handoff also live in the private Notion page
**BFI research library and handler handoff**, linked from the BFI project home.
Future chats with that connection should search that title. Do not rely on this
temporary cloud workspace for continuity. Preserve the reports separately until
the owner asks for the eventual combined report; that consolidation is not done.

Verification: 85 backend tests passed; Ruff checks and real Chromium flows cover
memory corrections/export/forget, library search/import, SSE preview, reload,
cancellation, and desktop/phone layouts. The existing chat smoke check also passed.
The HTTP model server used in browser checks was explicitly simulated. No GPU
inference, PC performance, LoRA loading/training, voice/video, image generation,
external runtime lifecycle, or native Windows overlay result is established.

Provisional choice: keep FastAPI/httpx and SQLite without adding an embedding
service, vector database, heavy orchestration framework, or GPU dependency. The
memory/provider boundary and compatible model endpoints remain replaceable. This
is a single-process local prototype. Starting the app defaults to visibly labeled
mock mode; real replies require a separately running model server.

The next machine session should identify the actual PC/OS, run one compatible
model, record model/server/quantization/context/latency/RAM/VRAM, and validate tool
calling before choosing optimization or adding voice/media/training services.
Training personality into weights remains a central separate experiment.

## Visual handoff remains in effect

**Latest owner decision (2026-11-10): the latest artwork dropped significantly in
quality across the board. V5 is rejected. The owner requested a handoff and will
resume in another chat. Stop visual implementation here.**

The cause is **not established**. Earlier claims of a completed visual pass and
passing tests did not establish acceptable artwork. Do not carry those claims
forward as owner approval. This handoff leaves the current assets and hosted
preview unchanged so the regression can be compared and diagnosed.

## Current repository state

- Repository: `Mallow99/Personality-Playground`, branch `work`.
- Last **art/code** checkpoint: `8cab2754d2311edba93367942af5060bd30504a7`.
  Later handoff-only commits do not represent another art revision.
- [Draft PR #1](https://github.com/Mallow99/Personality-Playground/pull/1) remains
  unmerged. No merge, rollback, regeneration or new deployment was requested now.
- The owner-private preview still serves rejected v5. Its URL is in the conversation
  and private Notion board; do not copy that private URL into public GitHub material.
- Technical integration remains in place. The owner rejected the visual result;
  they did not ask to discard the whole application or its handler/tool integration.

## What the owner actually wants

This is a skill-building project. The owner wants to understand the code, decisions
and process well enough to explain and own it. Keep a durable learning trail.

The selected **E reference** remains the basis for wardrobes, personality and shape
language: [option-e.png](../research/visual-studies/option-e.png). It is not approval
of every later conversion, palette adjustment or face replacement.

- Simple, loose, angular geometric shapes suggesting anime-like adult characters.
  Avoid overdesigned human anatomy, realistic shading, visual clutter and face mascots.
- Roughly three colors per character, with no cross-character palette overlap.
  Academic is neutral, Hacker feminine, Business masculine.
- Preserve pose quality. Authored set poses are preferred over a generic whole-body
  rig that makes them worse. Full poseable-model research remains Later.
- When parts move, restore the complete rear surface beneath them. A leg or object
  must not retain a hand-shaped hole. Keep coherent whole geometric forms.
- Hacker's flirty pose must have readable complete arms and a sensible stance.
  The replacement at v4 was not explicitly signed off as a final design.
- Business's face must read coherently. The owner objected to inconsistent covered-
  eye/cyclops readings. **The shared two-eye v5 head was the assistant's proposed
  solution, not an owner-approved identity decision.**
- In Business **writing** poses the paper faces him. We see the clipboard's plain
  back, not a spreadsheet presented to the camera. Supporting fingers can wrap
  around the near edge; the writing hand/pen nib are on his side. Displaying a
  document to the viewer is a separate presentation pose.
- Dark-background readability matters, but the v5 brighter palettes were not
  approved. Do not equate visibility or a numeric contrast ratio with good design.
- The 54 suggested pose ideas were approved. That does not approve every subsequent
  raster extraction, SVG conversion, head swap or regenerated interpretation.

## Checkpoints for comparison — none is a blanket “last good build”

| Commit | What it contains | Owner feedback / limits |
| --- | --- | --- |
| `97d96f3` | Focused Academic reading movement example | Owner said the limited movement/tweening was acceptable. This was not whole-library approval. |
| `4408faf` | Handler tools, 128-pose catalog, local overlay and optional native host | Later feedback identified flat layers and missing material beneath hands. |
| `3d2ddda` | Rear book/thigh repairs, recorded approval of 54 suggestions | Later feedback identified white edges, gaze problems and ineffective controls. |
| `18b2a45` | Matte/edge changes, actual hide/loading fixes, Hacker flirty replacement, eye overlays, runtime review page | Pre-v5 comparison point only. Owner still found dark-background, Business face and clipboard problems. |
| `8cab275` | Shared Business heads across 42 poses, two regenerated writing poses, 128 dark variants, owner contrast preference | **Latest rejected visual experiment. Owner reports a significant quality drop across the board.** |

Preserve these snapshots. Do not reset the branch or revert a mixed commit blindly:
art changes and useful functional fixes are interleaved.

## What v5 changed and what to investigate

These are concrete changes and plausible regression mechanisms, **not confirmed
causes**:

1. **Global dark-art recoloring.** `recolor_image()` in
   [build_avatar_design.py](../scripts/build_avatar_design.py) maps every PNG RGB
   pixel to the nearest role color, then replaces it with a brighter palette.
   That can flatten source variation, change perceived character identity and
   reduce detail even when alpha and contrast checks pass. It affects all roles.
2. **Business head replacement.** The same builder fits three generated head views
   to 42 existing poses using guide bounds and a few exceptions. Shared heads can
   lose pose-specific proportions, expression and integration with the body.
   The guides were draft annotations. A first attempt produced a double head in
   a reframed reclining pose; that was caught and corrected, but other placement
   quality still needs judgement. Forehead-hand poses use local eye patches.
3. **Two full regenerated Business endpoints.** `working` and `formal-report`
   changed body art as well as clipboard orientation. `authored_writing()` resizes,
   quantizes to three colors, thresholds alpha above 220, traces and simplifies.
   Those steps can change edge/detail quality. Correct orientation alone did not
   make the new artwork successful.
4. **Earlier export changes may contribute.**
   [avatar_matte.py](../scripts/avatar_matte.py) estimates/unmixes a white matte;
   [build_avatar_clean.py](../scripts/build_avatar_clean.py) removes small baseline
   contours and known neighboring fragments;
   [build_avatar_focus.py](../scripts/build_avatar_focus.py) adds local eye edits.
   Compare their outputs with source crops rather than assuming all are beneficial.
5. **Review method was insufficient.** Image decoding, silhouette overlap, palette
   counts, opacity, contrast and contact-page inspection missed design problems.
   They are useful engineering checks, not aesthetic acceptance criteria.

## Important pipeline trap

**Do not run `build_avatar_catalog.py` casually to copy the renderer or “refresh
assets.” It automatically calls `build_design(entries)` and rebuilds rejected v5
Business art and dark variants.**

First isolate or decouple that hook if a later task chooses a visual rollback.
Do not silently regenerate the whole library while trying to fix one sprite.
Frozen build/runtime metadata may still say `candidate`; the owner rejection in
this handoff supersedes that metadata. It was left intact for reproducibility.

## Files and references to inspect

- Original selected sheet: `research/visual-studies/option-e.png`.
- Earlier generated pose sheets and recorded crops:
  `research/visual-studies/poses-v2/`, `poses-v3/`, and
  `pose-proposals/`. Original glamour art is retained.
- Source-vs-code assets: `bfi/static/e-preview/assets/poses/<role>/`
  (`*.source.png`, `*.reference.png`, `*.svg`, `*.boundary.svg`).
- Hacker flirty repair record: `research/visual-studies/poses-v4/`.
- Rejected v5 references and recipe: `research/visual-studies/poses-v5/README.md`,
  `config/avatar-design-v5.json`, `scripts/build_avatar_design.py`.
  The first v5 sheet has presentation-facing writing boards; its lower poses were
  superseded by the separate inward-writing reference. Neither is now approved art.
- Current outputs: `bfi/static/avatar/{clean,focus,design-v5,dark,cutouts}/` and
  `catalog.json`. Business entries retain `previous_src`; this is a comparison
  resource, not proof that the previous version was good.
- Shared renderer: `bfi/static/avatar/avatar.js` and `avatar.css`.
- Static preview: `bfi/static/e-preview/runtime-demo.*`, `art-review.*` and the
  packaged `avatar-runtime/` copies. The old mapping lab is an archive.
- Learning/engineering history: [learning.md](learning.md),
  [architecture.md](architecture.md), [avatar-runtime.md](avatar-runtime.md).
- Review JSON and old “completion” notes document prior checks; do not interpret
  `inspected` or a passing report as owner approval.

## Recommended next session

Start with diagnosis and a small comparison, not another whole-library rewrite.

1. Read this handoff and the latest owner feedback before changing anything.
2. Compare original E/source art, pre-v5 exports and current v5 at the **same size**
   on light and dark backgrounds. Separate source-drawing quality, export damage,
   pose/prop logic and palette effects. Ask the owner for their preferred reference
   only if it cannot be established from the actual comparisons.
3. Use one Business writing pose to establish a better result while preserving
   the inward-facing clipboard requirement. Keep source and code versions side
   by side; check the face, whole silhouette, hands, edges and material layering.
4. Identify exactly what improves the image before considering a broader rollout.
   Any later user direction takes precedence over this suggested workflow.
5. Keep functional fixes separate from the visual decision. Do not automatically
   restore an old outward-facing writing clipboard merely to undo v5.

Safe comparison examples (read-only Git inspection):

```sh
git log --oneline -8
git diff 18b2a45..8cab275 -- scripts/build_avatar_design.py scripts/build_avatar_catalog.py bfi/static/avatar/avatar.js
git show 18b2a45:bfi/static/avatar/catalog.json > /tmp/bfi-catalog-before-v5.json
```

For isolated browsing, a detached worktree at a historical commit is preferable
to resetting `work`. Ignored screenshots under `runs/` may not exist in a new
workspace. `render_avatar_contact_pages.py` can render the existing catalog without
regenerating art, but its output is only another inspection aid.

## Engineering state worth preserving

- Local FastAPI handler; three profile configurations and stable pose IDs.
- Request-scoped own-character `avatar_catalog` / `avatar_set` tools, bounded tool
  calls and retained real provenance. Mock replies remain labeled mock.
- Shared ephemeral state for chat and `/overlay`; owner visibility, dock, size,
  motion and contrast preferences. Models cannot override owner display preferences.
- Actual hide/show CSS fix and shared loading-promise fix.
- Motion reset removes only known motion transforms, preserving authored placement.
- Restored rear material in the Academic reading and Business seated examples.
  Only two poses have local movement; the rest are intact static artwork.
- Optional PySide6 desktop host. Windows transparency, topmost, click-through,
  scaling and tray behavior have **not** been validated on the new PC.
- Static hosted demo is scripted; it exposes no local API, model or private history.
- Full-body rigging remains Later. Training personality into model weights, AMD
  performance/model selection, simultaneous serving/fast swaps, LoRA serving,
  frontier routing, voice, autonomous jobs and OS control remain separate work.

At the last code checkpoint, 65 backend tests, Ruff, asset checks and browser
regressions passed, including 256 image decodes. **The visual result was still
rejected.** No tests, art builds, rollback or preview deployment are needed merely
to make this handoff.

Keep credentials, history, private exports and model files outside Git. The local
single-process app must not be publicly exposed without authentication work.
