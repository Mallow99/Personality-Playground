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

Use `uv sync --locked`, `uv run --locked pytest`, `uv run --locked ruff check .`, and
`uv run --locked ruff format --check .` for relevant Python changes. Keep private
history, credentials, model files, adapters, and run artifacts outside Git. The desktop
app is a single-process local prototype; do not expose it publicly without designing
authentication and reviewing its data boundaries.

The primary interface must remain a standalone desktop application, not a browser UI.

Read `FABLE_BRIEF.md` for the owner’s product direction, comparison research, and
prioritized next steps; check the current code and newer user requests for changes.
