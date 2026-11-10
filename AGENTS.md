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
feasibility proofs, not the chosen E artwork. The E proof pack now lives in
`bfi/static/e-preview/`, with editable poses/icons, motif transitions, and agent
cursor studies. These proofs await visual review; ordinary chat artwork remains
the earlier prototype. Preserve the broader individual directions in
`docs/character-directions.md`. Model training, autonomous jobs, frontier routing,
and OS control are separate work, not established by the demonstration.


The owner rejected the first hand-built E SVGs and transitions. Use the generated
pose sheets in `research/visual-studies/poses-v2/` and their direct boundary traces.
Do not hand-redesign the figures during conversion. Verify source/SVG overlays;
technical tests alone do not establish aesthetic similarity. Keep all generated poses and
source crops inspectable. Adult playful poses are optional manual choices, separate
from ordinary activity. Academic also supports prose and Dungeons & Dragons goals.


The latest source inventory is 74 poses (24 academic, 26 engineering, 24 business).
The owner accepted the prior art except Hacker specialist poses; the replacement
sheet is in poses-v3. Original glamour sources and vectors must be retained alongside
new sultry poses. Semantic rig guides are in config/rigs; named pieces preserve
anatomical identity across poses, with draft ownership and visible inspection tools.
Pose transitions morph matched pieces; do not replace this with whole-card slides.
Always check crop spill, geometry fidelity, and actual rendered movement.

Latest owner correction: stop arbitrarily cutting big geometric forms into body
regions. Prove whole-form grouping on Academic standing/seated before expanding.
The other 72 mappings are legacy drafts. A hand should remain one coherent form;
a continuous leg may stay whole rather than acquiring artificial shin cuts. Pose
transformations mean transitions between poses, not transformations into objects.
Mix playful poses into the main library; remove the adult-studies section/filter.
The 54 suggested pose concepts require owner sign-off; do not generate them all or
infer approval. Preserve silent talking-cue and transition comparisons for review.

The owner subsequently explicitly requested an image and reason for every one of
the 54 suggestions. They are generated under research/visual-studies/pose-proposals,
with one demonstrating character per shared idea and their own roles for specialties.
They remain unapproved concepts and are separate from the 74 active SVG poses.
Preserve review codes, saved choices, image cell mappings, hashes, and reasons.

Current direction: retain authored set poses and add limited local hand/head/prop
motion. A universal poseable model is deferred to the board's Later research card;
do not replace the library with a generic rig. `limited-motion.html` is a focused
Academic reading example with a fixed body and pose-local head/book/hand transforms.
It does not approve new art or establish a reusable full-body model.

The current application now uses E art through bfi/avatar.py and static/avatar/.
There are 128 runtime entries: 74 SVG poses + 54 transparent concept cutouts, with
source/review metadata preserved. Avatar tools are request-scoped presentation calls;
mock mode must not claim model tool use. Chat/overlay share ephemeral state and
matching colors. Native Qt overlay code is optional and Windows behavior is not yet
verified. Read docs/HANDOFF.md and docs/avatar-runtime.md before continuing. Do not
expose the local backend through the static demo or claim voice/OS control/model
training from this integration. Rebuild the demo renderer copy with build_avatar_catalog.py.
