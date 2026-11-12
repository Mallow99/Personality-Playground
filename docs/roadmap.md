# Roadmap: a capable local AI companion

**Purpose:** the owner's product direction, an honest picture of where the code is,
comparable projects to learn from, and the order of work. It began as a brief written
for one review session on November 12, 2026 and is now the standing roadmap. It does
not claim that proposed features exist.

**How to use it:** the concrete, ready-to-start work is in [tasks.md](tasks.md). This
file explains why those tasks exist and what comes after them. Also read the
[working agreement](../AGENTS.md), [architecture](architecture.md), and
[verification notes](verification.md). When documents disagree, trust the code and the
owner's most recent direction, then fix the stale text.

## The owner's goal

Build a **standalone desktop handler for local AI characters** that can be as useful
and polished as an online assistant: hold conversations, remember appropriately,
operate tools and the desktop, work on meaningful tasks, manage models, and improve
over time. Local operation and user control matter. Optional, clearly disclosed
frontier-model delegation is welcome where it genuinely helps; local-first does not
mean pretending cloud calls are local or that every task must be handled locally.

The defining ambition is **a recognizable, useful character whose personality can
be trained into model weights**. Voice, opinions, priorities, habits, uncertainty,
practical competence, and visual identity all matter. LoRA is a legitimate route.
Prompts, memory, skills, tools, and interface design are valuable supporting layers;
none alone is weight training. Do not quietly replace the training goal with a
prompted persona. The actual character, model family, research question, and training
stack remain open for deliberate decisions with the owner.

The owner wants to learn and own the system. Make consequential tradeoffs legible,
point to the relevant code, and preserve reproducibility without turning every
change into homework. Avoid Cyberpunk and Capri story spoilers in examples or data.

### Non-negotiable direction

- The primary product is a **standalone desktop application**, targeting the
  owner's Windows PC. Do not make a web page, browser tab, or web dashboard the
  primary interface. Browser automation can be a future *tool used by the desktop
  app*; it does not change the form of the application itself.
- GitHub is the source of truth for project code and documentation. Keep the repo
  reviewable and avoid relying on untracked files for the project to build. The
  current GitHub repository is public: private conversations, credentials, personal
  exports, local environments, downloaded weights, adapters, and run artifacts are
  deliberately excluded. Keep reproducible configurations and documentation in Git;
  do not publish private data or huge generated files just to avoid a local copy.
- No model, server, hardware capability, tool result, learned memory, or successful
  action should be implied when it has not actually been verified. Never silently
  substitute the mock for failed inference.
- The initial target is one local user, not a public multi-user service. Real local
  inference, GPU use, and AMD training need measurement on the owner's PC.

## Current baseline on `main`, checked November 12, 2026

- `python -m bfi` opens a Tk desktop window. The window calls a plain Python
  `ChatService` ([bfi/service.py](../bfi/service.py)) directly; there is no web
  server, HTTP layer, or browser anywhere in the app. A separately started model
  server may listen on loopback.
- Conversations, SQLite history, JSON export, deletion, one provisional character
  snapshot per conversation, backend status, and reply provenance exist.
- The default backend is a labeled scripted mock. The other adapter calls a
  configured loopback OpenAI-compatible server. No real server or model has been
  verified on the owner's machine.
- One generation at a time, plain text, no streaming, no way to stop a reply except
  closing the window, approximate character budgeting. It runs from Python; it is
  not a packaged Windows app.
- It does **not** execute tools, control the desktop, keep cross-conversation memory,
  offer more than one character, manage models, delegate to cloud providers, train a
  model, update itself, or read the calendar.
- Evidence: 40 automated tests, including tests that drive the real Tk window on a
  virtual display, and a Linux smoke run. Nothing has been run on Windows by a
  person, against a real model, on a GPU, or for training. See
  [verification](verification.md).

The planned PC is a Windows 11 machine with an RX 7900 XTX (24 GB VRAM), 32 GB RAM,
and a 1 TB SSD. Verify actual hardware, drivers, and stability when available. An
approximately 27B companion model and a smaller fallback are aspirations, not proven
fits; training feasibility is a different question from inference fit. Do not assume
additional RAM, a Linux installation, cloud training budget, or outside funding.

## Earlier work on other branches

Before the app became desktop-only, about twenty commits of work were built on the
original **browser** interface. They were never merged, and `main` restarted from the
first commit. That work is real and tested, but it is welded to a web UI the owner has
since ruled out, so it is a **source to port from, not something to merge**.

| Branch | State | What is there |
| --- | --- | --- |
| `work` (draft PR #1) | Frozen. Visual work paused by the owner; the "V5" artwork was rejected. | Avatar art pipeline and 128-pose catalog (about 170 MB of assets), three character themes, an optional PySide6 transparent overlay window, browser pages. |
| `bfi/handler-core` (draft PR #2, built on `work`) | Frozen. | Everything in `work`, plus the pieces listed below. 104 backend tests. |

Worth porting from `bfi/handler-core` (read a file with
`git show origin/bfi/handler-core:<path>`):

| Piece | Source files on that branch | Where it lands |
| --- | --- | --- |
| Streaming replies and cancellation | `bfi/backends.py` (`complete_stream`), `bfi/jobs.py`, `tests/test_handler.py` | [Task A1](tasks.md) |
| Three selectable character profiles | `config/profiles.json`, `bfi/config.py` (`for_profile`), `tests/test_profiles_tools.py` | [Task A3](tasks.md) |
| Read-only project-file tools and a bounded tool loop (at most three calls) | `bfi/tools.py`, `bfi/backends.py` (`complete_with_tools`), `docs/tools.md` | [Tasks A4–A5](tasks.md) |
| Owner-saved memory with scopes, corrections, forgetting | `bfi/knowledge.py`, `docs/handler.md` | Later; listed in tasks.md |
| Personality settings with revisions | `bfi/personality.py` | Later |
| Research library (SQLite FTS5) and research reports | `bfi/knowledge.py`, `research/tooling/` | Later |
| Memory "sleep" review with LangMem | `bfi/memory_sleep.py` | Later; needs a real tool-capable model first |
| Character directions and personality drafts | `docs/character-directions.md`, `docs/personality-drafts.md` | Already copied to `main` |

Rules for porting: copy the logic and its tests, not the FastAPI routes, the
JavaScript, or the asyncio job queue. Port one piece per change. Do not merge or
rebase those branches into `main`, and do not copy the avatar assets while visual
work is paused. The branch's own `docs/HANDOFF.md` records the owner's art feedback.

## What to learn from other products

These are comparison points, not claims of equal capability or instructions to copy
whole products. Features, repositories, and licenses can change. Confirm the exact
version and upstream documentation before implementation. Comparisons below reflect
public upstream descriptions reviewed November 12, 2026, not independent benchmarks.

| Product | Relevant documented ideas | What to consider for BFI | Important distinction |
| --- | --- | --- | --- |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Persistent memory, reusable skills, toolsets, multiple model providers, and a learning workflow. Its [memory guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) distinguishes a real memory tool call from a model merely saying it remembered. | Inspectable memory with actual write confirmation; load relevant skills on demand; see whether its agent loop or components can be reused or integrated. | Its learned notes and skills are not, by themselves, personality training into weights. Evaluate behavior, runtime requirements, and integration fit rather than assuming feature parity. |
| [Cursor Agent](https://cursor.com/docs/agent/overview) | A model, instructions, and tools working together; code search/editing, command execution, task visibility and checkpoints. | A clear activity timeline, change previews, bounded project context, checkpoints, and a good working relationship with the user. | Cursor is a coding-focused commercial product. Treat its documented behavior as product inspiration, not open source code to copy. BFI should also support non-coding companion tasks. |
| [OpenClaw](https://github.com/openclaw/openclaw) | An extensible agent with integrations and a gateway/tool architecture. Its docs discuss [sandboxing and tool policy](https://docs.openclaw.ai/gateway/sandboxing) and [execution approvals](https://docs.openclaw.ai/tools/exec). | Investigate its agent loop, integration approach, policy enforcement, and reusable components. Prefer a small understandable integration over adopting a large gateway blindly. | Defaults and execution environments are configuration-specific. Its security docs do not mean every install is sandboxed; test the exact setup and do not expose the user's PC by accident. |
| [Open Interpreter](https://github.com/openinterpreter/openinterpreter) | A provider-oriented coding agent with computer-use work described in its repository. | Investigate tool interfaces and desktop-control approaches, especially whether components can be isolated and evaluated. | Verify current architecture, platform support, licenses, and actual behavior; do not assume Windows or local-model compatibility from a feature list. |
| [LM Studio](https://lmstudio.ai/docs/developer/core/server) and [Ollama](https://docs.ollama.com/capabilities/tool-calling) | Examples of local model serving and, where supported, structured tool calling. | Learn from model discovery, local endpoints, lifecycle controls, and backend-specific capabilities; use documented APIs rather than scraping a UI. | A model server is not the whole agent. API compatibility, tool calls, streaming, and load/unload features vary by server, model, and version. |

### Code reuse is encouraged

The owner explicitly welcomes building on existing work and adapting useful code.
Compare **integrate as a dependency**, **adapt a small component**, **fork**, and
**independent implementation**. Prefer the option that delivers real value while
remaining understandable, maintainable, and compatible with a desktop-first app.

As reviewed above, the upstream GitHub repository pages identify Hermes Agent and
OpenClaw as MIT licensed and Open Interpreter as Apache-2.0 licensed. That is a
starting point, not blanket clearance for every file, dependency, model, dataset,
logo, or bundled asset. Cursor's documentation describes its product, not a grant
to copy proprietary implementation. Before incorporating source:

1. Identify the exact upstream repository, file/component, commit or release, and
   applicable license; inspect nested notices and third-party dependencies.
2. Preserve required copyright notices, licenses, attribution, and any other applicable
   terms. Check compatibility with the intended distribution and dependencies.
3. Record the provenance and local changes in the repository; document how to update
   or replace the component. Review whether it makes network calls or broadens access.
4. Do not assume BFI itself has a chosen open-source license: it currently does not.
   Ask the owner when choosing a project license or when an upstream obligation
   requires a decision. Consult appropriate expertise for uncertain legal questions.

No source has been copied as part of this brief.

## Product capabilities to aim for

These are candidate requirements, not a demand to ship them together. For each
feature, distinguish a useful first slice from later polish and write observable
acceptance criteria. Let user feedback and hardware evidence change the order.

### 1. A real agent, not just an attractive chat

- Support a bounded model → tool request → validated execution → actual result →
  model continuation loop, with a meaningful completion or clear failure.
- Give the user an activity timeline showing task status, tool name, relevant inputs,
  real results, errors, and a concise final account. Offer stop/cancel, progress,
  and recovery where the underlying operation supports them.
- Tool calls must be structured and validated; arbitrary model text is not proof
  a tool ran. Handle malformed or unsupported calls, timeouts, limits, loops, and
  providers that do not support tool calling. Cap steps and output to stay usable.
- Start with a narrow, genuinely useful workflow against a user-selected workspace:
  for example, inspect files and produce a sourced summary. Later, preview proposed
  changes before applying them and show exact results. Separate observing, editing,
  command execution, and external actions into distinct capabilities.
- Provide appropriate user controls for consequential actions, scoped access, and
  clear information about what data is sent where. Untrusted files, web pages, tool
  output, and generated content must not acquire authority merely by appearing in
  the context. Do not claim a sandbox exists until it is implemented and tested.
- Treat inference quality and tool reliability as measurable. Different local models
  may fail tool formatting, planning, or long tasks; provide graceful failure, not a
  fabricated success. A visible cursor is not required for useful agency.

### 2. Desktop and application control

Support computer use as a later capability of the standalone app, not a replacement
for it. Prefer documented APIs or accessibility controls when suitable, with visual
observation and pointer/keyboard interaction where needed. The model chooses actions;
a separate automation layer executes them and reports observations. Direct cursor
movement can be fast, but screen state, application readiness, and model reasoning
are limiting factors. Re-observe after meaningful changes and stop on uncertainty.

Design for Windows first, keep platform-specific drivers replaceable, and evaluate
permissions, focus, DPI scaling, multiple displays, accessibility, error recovery,
and whether the selected model can actually interpret screenshots. A local text-only
model should not be marketed as able to see the screen. Desktop automation must
never pretend that a click or outside-world action succeeded without evidence.

### 3. Memory and skills

- Separate raw chat history, user facts, preferences, episodic/task records, and
  reusable procedural skills. Give each a clear purpose rather than stuffing the
  entire transcript into every prompt.
- Make memory inspectable, correctable, deletable, and attributable to a source and
  time. Provide a clear approach to consent, sensitive information, conflicts,
  stale facts, and deletion. Show what was actually retrieved for a reply.
- Permit skills to be discovered and loaded on demand. Skill text and third-party
  content remain untrusted. Explicitly record when a memory or skill was actually
  written, rather than relying on model prose.
- Do not silently turn private conversations into training data. Curated,
  consent-based training is a separate workflow.

### 4. Local models and honest delegation

- Inspect server capabilities instead of assuming all OpenAI-shaped endpoints support
  the same model lifecycle, context sizes, streaming, image input, or tool calling.
- Model selection should eventually show exact identity/revision where known,
  quantization, source/license, requested vs reported model, server, context and
  actual load/unload state. Measure load time, generation rate, and memory instead of
  claiming hardware fit. Preserve the smaller-fallback option.
- Optional external providers should be explicit and separately configured; show
  what content leaves the device, provider/model, and usage/cost where available.
  A chat subscription is not necessarily API access or API credit.
- Avoid implicit failover to a different backend or mixing incompatible contexts.
  Preserve user control of network access, model switching, and GPU resources.

### 5. Self-updating and recovery

Self-updating is a desired feature, not present today. Distinguish: (a) updating the
app and dependencies, (b) updating model files, (c) updating skills/integrations,
and (d) updating model weights through a training experiment. Each has different
risks, storage needs, licensing, and user choices.

A reasonable first target after packaging is an optional check for versioned GitHub
releases, human-readable changes and explicit install action, artifact integrity and
origin verification, compatibility checks, atomic replacement where possible, and
rollback/recovery. Do not execute a mutable script or automatically replace the
running application merely because a remote endpoint says an update exists. Define
how existing SQLite data is backed up and migrated; test a failed update and rollback.
Automatic update preferences can be considered after that foundation works. GitHub
source control and locally installed/running app data are separate things.

### 6. Personality training, voice, and identity

- Preserve [the training plan](training.md): choose a narrow research question,
  verify hardware and serving, curate licensed/consented examples, isolate a held-out
  set, train a small adapter, compare it to the exact starting checkpoint, and verify
  the resulting artifact can be served. Keep task quality and undesired behavior in
  the evaluation alongside personality.
- Make character configuration and eventual visual design cohesive, but leave the
  character's identity open for the owner. Voice input/output and animation are later
  features; assess response latency, device use, privacy, and model compatibility.
- A useful aspiration is an optional review queue that proposes examples or training
  improvements for the owner. It must not silently change weights after each chat.

### 7. Everyday polish

A desktop assistant that feels competitive needs reliable interruption/cancellation,
streaming when supported, keyboard access, understandable onboarding and errors,
transcript search, accessible layouts, understandable settings, data backup/export,
and resource-use visibility. Evaluate a stronger native desktop UI toolkit if the
current Tk prototype becomes a constraint; a toolkit decision should consider
Windows packaging, accessibility, maintenance, performance, and contributor learning.
Keep a working app through any migration.

The school deadline source of truth is Google Calendar with Canvas synchronized to
it. A future read-only integration should show real data, source and freshness, and
sync failures. Do not invent deadlines or assume Canvas sync is working.

## Order of work and completion evidence

| Priority | Milestone | Status and evidence needed before calling it done |
| --- | --- | --- |
| 0 | Harden the desktop foundation | **Done on Linux, November 12, 2026**: service layer, draft retention, close-during-reply prompt, atomic first exchange, window tests. Still open: a person running the [Windows checklist](tasks.md). |
| 1 | Establish actual local inference | On the owner's PC, verify exact server/model versions, successful generation, GPU use, latency, RAM/VRAM, and repeatable startup. Start small. Owner task P2. |
| 2 | Streaming, Stop, and one read-only agent task | Tasks A1–A5: live reply text, a Stop button, a bounded tool loop, and workspace-scoped file reading with a visible record of each call. Fake model for deterministic tests; a real tool-capable model when available. |
| 3 | Previewed changes and controlled execution | Explicitly scoped edits, diffs, checkpoints or recoverable state, and appropriate user controls. Verify denial, failure, and restoration paths. |
| 4 | Memory, a useful integration, and model lifecycle | Real inspect/correct/delete memory, one source-grounded workflow such as calendar reading, and tested server-specific model controls. These can be separate milestones. |
| 5 | First controlled personality adapter | A reproducible, small, held-out before/after study with saved artifact, serving proof, resource measurements, and honest results. The compatibility gate (owner task P4) can start as soon as the PC works; do not wait for app features. |
| 6 | Packaging and safe updates | Windows installer or equivalent, versioned releases, upgrade/rollback and data migration tests. |
| Later | Computer use, voice, cloud delegation, richer character and visuals | Concrete user benefit, real integrations, tested permissions and provenance, hardware and provider evidence. |

Stages can overlap. Priorities 1 and 5 need the owner at the PC; priorities 2–4 can
proceed in parallel without it.

### The agent loop: adapt our own earlier code

The comparison above asks whether to integrate a framework, adapt a component, fork,
or build. Recommendation: **adapt the bounded loop already written on
`bfi/handler-core`**, rather than adopting Hermes Agent, OpenClaw, or Open Interpreter.

- It is about 90 lines the owner already has tests for: at most three tool calls,
  tool names checked against the set enabled for that message, argument size limits,
  every call and result recorded with the reply, and a clear failure when the model
  misbehaves.
- It speaks the standard OpenAI `tools` / `tool_calls` format, which llama.cpp's
  server supports when started with `--jinja`, as do LM Studio and Ollama. Tool-call
  quality varies by model and chat template and has not been measured here.
- A framework would bring its own process model, storage, and permission system into
  an app that is under a thousand lines; that is hard to inspect and harder to explain.
  Revisit if the loop outgrows roughly 300 lines or needs sub-agents.
- First tool: read-only file listing and reading inside one folder the owner picks.
  Acceptance tests and limits are in tasks A4 and A5.
- Main risks: small local models emitting malformed tool calls (handled as a visible
  failure, never a fabricated success), and file contents being treated as
  instructions (tool output is data; say so in the system prompt and never grant
  authority from it). Simulated tool calls in tests are not evidence of real model
  performance.

## Decisions waiting on the owner

These block or shape later work. Each has a recommendation; none has been acted on.

1. **The old branches and draft PRs #1 and #2.** Recommendation: keep both branches
   as an archive and close the two PRs without merging, with a link to this section.
2. **Desktop toolkit: stay on Tk, or move to Qt (PySide6)?** Decide before any task
   that adds a second window. Tk is built into Python and enough for chat. It cannot
   draw SVG, has weak per-pixel transparency, and has no rich-text or Markdown view.
   The avatar overlay on `work` already uses PySide6 for exactly those reasons. Qt is a
   far larger dependency than anything the app has now, and its LGPL license needs
   attention when packaging. Recommendation: if the on-screen character is still wanted, switch
   before building more windows; the window code is about 300 lines today and all
   logic lives in the service, so the switch is cheap now and expensive later.
3. **One character or three.** `main` has one provisional "Companion". The newer
   direction is three specialists; see [character-directions.md](character-directions.md)
   and [personality-drafts.md](personality-drafts.md). Task A3 adds the mechanism
   with the provisional profiles; activating the Olive/Violet/Slate drafts is the
   owner's call.
4. **Project license.** None is chosen. Needed before reusing code with obligations
   or inviting contributions.

## Sources and follow-up research

- [Hermes Agent repository](https://github.com/NousResearch/hermes-agent),
  [memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory),
  and [quickstart and skills](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart).
- [Cursor Agent overview](https://cursor.com/docs/agent/overview) and
  [agent mode and checkpoints](https://cursor.com/help/ai-features/agent).
- [OpenClaw repository](https://github.com/openclaw/openclaw),
  [sandboxing](https://docs.openclaw.ai/gateway/sandboxing), and
  [tool permissions](https://docs.openclaw.ai/gateway/security/tool-permissions).
- [Open Interpreter repository](https://github.com/openinterpreter/openinterpreter).
- [LM Studio local server](https://lmstudio.ai/docs/developer/core/server) and
  [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling).

Primary-source product descriptions are not endorsements, independent benchmarks,
or assurances about current versions. Inspect exact source files and test the chosen
versions before reuse. Product comparisons and recommendations above are our own
interpretation of those sources and the owner's stated goals.
