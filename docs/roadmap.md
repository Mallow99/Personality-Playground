# Brief for Fable: build a capable local AI companion

**Purpose:** give Fable and future contributors the owner's product direction, an
honest picture of the starting point, comparable projects to investigate, and a
prioritized roadmap. This is a living brief, not a claim that the proposed features
already exist or an instruction to implement the whole roadmap in one pass.

**Read first:** [working agreement](AGENTS.md), [README](README.md),
[vision](docs/vision.md), [architecture](docs/architecture.md),
[training plan](docs/training.md), [hardware notebook](docs/hardware.md), and
[verification](docs/verification.md). Inspect the current code and Git status before
changing anything; the repository may have advanced since this brief was written.
When the documents disagree, clarify the current state from code and the owner's
most recent direction rather than silently accepting stale text.

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

## Current baseline, checked November 12, 2026

The latest baseline when this was written is commit `a21c5f3`. Re-check HEAD and the
code before relying on the list below.

- `python -m bfi` opens a Tk standalone desktop window. It calls the FastAPI
  application in-process through HTTPX; BFI does not start a listening web server.
  A separately started model server may listen on loopback.
- Conversation creation, selection, SQLite history, JSON export, deletion, a
  provisional character snapshot, backend status, and reply provenance exist.
- The default backend is a labeled scripted mock; the other adapter can call a
  configured loopback OpenAI-compatible server. The real server and model have not
  been verified on the owner's machine.
- It has one active generation, plain text, no streaming, and approximate character
  budgeting. The prototype runs from Python; it is not yet a packaged Windows app.
- It does **not** yet execute tools, control the desktop, maintain general
  cross-conversation memory, manage/load models, delegate to cloud providers, train
  a model, update itself, or integrate the calendar.
- Prior verification recorded 28 passing automated tests and a limited Linux desktop
  mock/send/reopen smoke check. These are not Windows, real model, GPU, or training
  validation. See [verification](docs/verification.md) for the actual evidence.

The planned PC is a Windows 11 machine with an RX 7900 XTX (24 GB VRAM), 32 GB RAM,
and a 1 TB SSD. Verify actual hardware, drivers, and stability when available. An
approximately 27B companion model and a smaller fallback are aspirations, not proven
fits; training feasibility is a different question from inference fit. Do not assume
additional RAM, a Linux installation, cloud training budget, or outside funding.

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

- Preserve [the training plan](docs/training.md): choose a narrow research question,
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

## Proposed order and completion evidence

| Priority | Milestone | Evidence needed before calling it done |
| --- | --- | --- |
| 0 | Harden the current desktop foundation | Review thread/UI lifetime, draft retention, cancellation/close behavior, concurrent access and error handling. Focused tests plus actual desktop checks; record Windows gaps. |
| 1 | Establish actual local inference | On the owner's PC, verify exact server/model versions, successful generation, GPU use, latency, RAM/VRAM, and repeatable startup. Start small. |
| 2 | Agent architecture and one read-only task | Select or adapt a harness; implement a bounded loop and one useful, workspace-scoped, read-only tool. Demonstrate actual result, validation, failure handling, stop/limits, and readable activity. Use a fake model for deterministic tests and a real capable model when available. |
| 3 | Previewed changes and controlled execution | Explicitly scoped edits, diffs, checkpoints or recoverable state, and appropriate user controls. Verify denial, failure, and restoration paths. |
| 4 | Memory, a useful integration, and model lifecycle | Real inspect/correct/delete memory, one source-grounded workflow such as calendar reading, and tested server-specific model controls. These can be separate milestones. |
| 5 | First controlled personality adapter | A reproducible, small, held-out before/after study with saved artifact, serving proof, resource measurements, and honest results. Begin compatibility investigation early; do not wait for all app features. |
| 6 | Packaging and safe updates | Windows installer or equivalent, versioned releases, upgrade/rollback and data migration tests. |
| Later | Computer use, voice, cloud delegation, richer character | Concrete user benefit, real integrations, tested permissions and provenance, hardware and provider evidence. |

This sequence is a proposal; stages can overlap. For the owner's earlier rough
planning, local inference was estimated at 2–5 engineering days plus troubleshooting;
a narrow tool or memory feature at roughly 1–3 weeks; a first training study at
3–8+ weeks. These are speculative ranges for one developer with AI assistance,
not deadlines or guarantees. Windows packaging, AMD compatibility, evaluation,
integrations, and data work may change the estimate substantially. Re-estimate after
inspecting the chosen implementation and actual PC.

## First assignment for Fable: high value, bounded usage

The owner has limited Fable 5.2 usage. Do not try to implement the entire vision in
one session. Start by reviewing the current desktop app for high-impact correctness
and data-safety issues, especially worker-thread/UI interactions, draft retention on
failure, conversation persistence, closing during a generation, and test gaps.
Compare the agent architecture to Hermes/OpenClaw/Cursor only as needed to identify
an appropriate next seam; do not import a full framework for this first pass.

Deliver in one focused session:

1. Inspect current code and existing tests. Identify a small number of verified,
   consequential problems; distinguish observed failures from hypotheses.
2. Fix the highest-impact issues that fit coherently in the session. Preserve the
   desktop direction, saved data, backend distinction, and current capabilities.
3. Add focused tests for real regression risks; exercise the UI where the environment
   permits. Run the checks in `AGENTS.md`, state actual results and limitations, and
   update the architecture/learning notes if the design meaningfully changes.
4. End with a short proposal for a *separate* narrow agent-loop milestone: recommend
   integrate/adapt/build, identify one useful read-only tool, acceptance tests, and
   likely cost/risks. Do not call simulated tool behavior real model performance.

If the owner instead explicitly asks Fable to implement an agent feature, follow
that newer request. Ask only for decisions that materially block the chosen work;
make routine implementation choices and explain them.

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
