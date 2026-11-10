# Project working agreement

This is both a local AI character application and a skill-building project for its
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
history, credentials, model files, adapters, and run artifacts outside Git. The app
is a single-process local prototype; do not expose it publicly without designing
authentication and reviewing its data boundaries.

The owner expects requested features to be implemented in the repository, not only
captured as board ideas. Preserve the distinction between working code, a visual
study, and future plans. The live optional planning board is in Notion; private IDs
may be available in ignored `data/project-links.json`. Do not publish personal
captures. Keep the Next shortlist small and capture new ideas without artificial
deadlines. The app must run without Notion or a hosted service.

Three provisional profiles now exist in `config/profiles.json`. Their prompts and
themes are not trained personality. Do not imply an adapter label loaded a LoRA,
or an entrance animation established model readiness. Local inference, AMD training,
adapter serving, and native desktop overlays require separate evidence. Model tools
are explicitly opted in per message; keep tool outputs inspectable and bounded.

Visual baseline is now **E**, selected after the pose studies. Read
`research/visual-studies/README.md` and `baseline.json` before further art work.
Preserve E's separate palettes, neutral academic, feminine hacker, and masculine
business character, with loose geometric standing/seated poses. Earlier D SVGs are
feasibility proofs, not the chosen E artwork. Icons remain unconfirmed. Animation
and further design work are paused for review; do not resume them implicitly.
