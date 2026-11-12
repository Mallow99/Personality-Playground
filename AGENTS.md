# Project working agreement

This is a standalone desktop AI character application and a skill-building project for its
owner. Explain consequential decisions plainly and point to the actual code. Keep
`docs/learning.md` and the decision record in `docs/architecture.md` aligned with
meaningful changes, so the owner can inspect, explain, and reproduce the work.

Preserve the ambition to train personality into model weights. Prompts, memory,
UI design, and tools support that goal; they do not replace it. The research question,
first character, model, and training stack remain open until deliberately chosen.

Keep milestones modest. Distinguish documented support, automated simulations,
actual inference measurements, training results, and custom-model serving evidence.
Never silently replace failed inference with a mock reply. Avoid Cyberpunk/Capri
story spoilers. Do not assume RAM upgrades, other hardware, or school funding.

The primary interface must remain a standalone desktop application, not a browser UI.
The app contains no web server and no HTTP layer; do not add one.

## Where things are

- `bfi/desktop.py` is the window. `bfi/service.py` holds every application rule and has
  no window code. `bfi/store.py` is SQLite; `bfi/backends.py` talks to the model.
  Put logic in the service and test it without a window.
- Tk widgets are touched only on the main thread. Slow work goes through
  `DesktopApp.run_task`; a worker thread never calls a widget.
- Only complete exchanges are saved, and the draft is cleared only after a successful
  send. Do not weaken either rule.
- `docs/roadmap.md` has the product direction, order of work, and open owner decisions.
  `docs/tasks.md` has the ready-to-start task cards and the rules for doing one.
  Take one card at a time and do only what it says.
- `main` is the only line of development. The branches `work` and `bfi/handler-core`
  hold earlier browser-based work. Read from them with
  `git show origin/bfi/handler-core:<path>`; never merge or rebase them into `main`,
  and do not copy their image assets. Visual and avatar work is paused by the owner.

## Checks

Use `uv sync --locked`, `uv run --locked pytest`, `uv run --locked ruff check .`, and
`uv run --locked ruff format --check .` for relevant Python changes. On Linux, run the
tests as `xvfb-run -a uv run --locked pytest` so the window tests have a display;
without one they are skipped, which is not a pass. Report the real output.

Keep private history, credentials, model files, adapters, and run artifacts outside
Git. The desktop app is a single-process local prototype for one user.
