# E interactive proof

[Open the private live demo](https://bfi-e-character-proof.poyoboi29.chatgpt.site).
Owner sign-in may be required. This hosted preview has no backend/model connection.

Open `/static/e-preview/index.html` while BFI is running, or serve this directory
with any local static HTTP server. This demo works without model or Python API calls.
The hosted copy uses the same HTML, CSS, JavaScript, and assets. The ordinary chat
and `/concepts` artwork remain the earlier prototype.

Included: 12 SVG poses (standing, seated, explaining, thinking), six face/motif SVGs,
three skippable 2.5-second theme transitions, a 12-second character sequence, speaking
and visibility controls, and 13 cursor states per role. All three characters support
the controls; Academic is the default sequence. Captions are scripted; there is no audio.

## Integration interface

`components.js` exports `CharacterActor`, `ProfileTransition`, and `AgentCursor`.
Use a separate actor instance for each visible character. `setPose(pose, profile)`
returns a promise; late asset responses cannot overwrite the latest selection.
`setSpeaking(boolean)`, `show()`, and `hide()` change presentation. `destroy()` clears
pending loads and removes art. A host can call these from actual application events;
it must not use visual state as evidence of model readiness.

`ProfileTransition.play(profile)` cancels its previous sequence; `stop()` clears it.
The page's theme is controlled independently through `data-theme`. Global Motion off
and `prefers-reduced-motion` suppress animated effects. The sample sequence still
shows timed static poses/captions when reduced motion is active.

`AgentCursor.update({profileId, shape, x, y})` places the cursor's **hotspot** at x/y
in its positioned container, and `hide()` removes it. Overlay input is transparent.
The user's normal pointer stays visible. `cursorSVG(profile, shape)` exports the same
art shown in the pad; `cursorHotspot(shape)` provides coordinates for future native
integration. Browser SVG downloads do not install Windows cursors.

## Reproduce checks

```sh
node scripts/check_e_preview.mjs
node --check --input-type=module < bfi/static/e-preview/components.js
node --check --input-type=module < bfi/static/e-preview/studio.js
```

Run these from the repository root. The deterministic checks cover asset references,
shared-palette exclusions, cursor exports/hotspots, stale actor loads, and transition
cancellation/skip/reduced-motion logic. They do not establish browser rendering.

The shared-browser runtime was unavailable and the managed preview relay timed out
in this session. Full-page browser layout and playback QA remain unverified. The
hacker/business asset contact sheets were inspected separately. Exported contact
sheets/GIFs illustrate the actual SVG assets; they are not a screen recording.

Current checkpoint: 43 existing Python tests passed, Ruff lint/format passed, both
JavaScript modules passed syntax checks, and the deterministic component checks
passed. All SVG exports parse and the reference/documentation links resolve. Pose,
icon, and cursor contact sheets were rendered from SVG and visually inspected.
