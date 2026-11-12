# Local handler: connections, jobs, memory, and research

The handler coordinates the existing character app and replaceable local model
connections. It now provides an owner workspace at `/handler`, a research library
at `/library`, personality controls at `/personalities`, and queued generation in chat.
It runs without Notion, an API key,
an embedding model, a vector service, or a GPU in explicitly labeled mock mode.
Real responses require a separately running model server.

## Starting and connecting

Use `uv sync --locked`, then `uv run --locked python -m bfi`. Open
`http://127.0.0.1:8000/handler`. The app still binds to loopback and is a
single-process, local-user prototype.

Keep `BFI_BACKEND=mock` for scripted demonstrations. To connect a real runtime,
set `BFI_BACKEND=openai`, choose `BFI_RUNTIME`, and set the actual model ID.
Presets are `custom`, `llama_cpp`, `strata`, `lmstudio`, and `ollama`. Their
conventional `/v1` ports are respectively 8080, 8080, 8080, 1234, and 11434.
`BFI_BASE_URL` always overrides a preset, including a value left in `.env`.
`/handler` can download a settings snippet; review/copy it into `.env` and
restart the app. It does not execute an installer or load a model.

The existing `BFI_ACADEMIC_*`, `BFI_ENGINEERING_*`, and `BFI_BUSINESS_*`
overrides support separate routes. They can now select `RUNTIME`, `TEMPERATURE`,
`MAX_TOKENS`, and `CONTEXT_CHARS`. An explicit per-character `BACKEND` or
`BASE_URL` wins. API keys stay server-side. An adapter label remains provenance
metadata, not a command to load LoRA weights.

Sampling controls are `BFI_TEMPERATURE` and optional `BFI_TOP_P`. Output and
context limits remain `BFI_MAX_TOKENS`, `BFI_HISTORY_PAIRS`, and
`BFI_CONTEXT_CHARS`. Context limits are character guards, not tokenizer-aware
fit guarantees. Effective settings are recorded with each successful reply.
No speculative decoding, GPU offload, or kernel option is silently imposed on
the inference server; tune those in the chosen runtime after measurement.

## Generation jobs

The browser submits `POST /api/conversations/{id}/jobs` and polls the returned
job. A single-resource gate serializes queued requests across all profiles.
The default pending limit is 16 (`BFI_QUEUE_LIMIT`). The old synchronous messages
API remains compatible and rejects overlapping work rather than bypassing the
queue. Request IDs provide idempotent submission: retrying the same ID/payload
returns the same job; changing its payload is rejected.

Jobs persist as queued, running, succeeded, failed, cancelled, or interrupted in
`data/jobs.sqlite3`. A browser reload reconnects to active work. A handler restart
marks unfinished jobs interrupted and never replays them automatically: a tool
could already have run. Inspect state before deliberately resubmitting.

Cancel from chat or `/handler`. Cancelling closes the in-flight client request,
releases the handler's gate, and does not commit an incomplete conversation pair.
Whether the external model server also stops GPU work depends on that server's
disconnect handling; BFI does not claim verified server-side cancellation.
Deleting a conversation also cancels and removes its job records.

For plain-text requests on compatible real endpoints, the adapter reads actual
SSE deltas and exposes them as a provisional preview. A malformed, incomplete,
or failed stream is not committed as a successful reply. The current bounded
tool loop buffers its reply; it is not streamed token by token. Mock replies are
never disguised as streaming inference. Uncheck model avatar/tool permissions to
exercise the plain streaming path. Turn off Live reply preview if the endpoint
does not support SSE. Lifecycle avatar cues still operate.

## Inspectable memory

`/handler` supports saving, correcting, filtering, forgetting, and exporting
memory. Every record has an owner-provided source, kind, scope, and revision
history. Shared records can enter any character context; private records only
enter that profile's context. The server enforces this rule. Corrections are
transactional and remove superseded versions from active retrieval.

The chat's Saved memory checkbox controls context inclusion. Retrieval combines
bounded lexical matches (including alternate recall keywords) with a few important
or recent owner-saved records, suppressing exact duplicates; `BFI_MEMORY_CHARS`
defaults to 4000. The application logs which record IDs/sources were retrieved.
Those references establish supplied evidence, not proof the model used it well.
When Research lookup is opted in, a real tool-capable model can search saved
research and, if Saved memory is enabled, its permitted memory scope.

Models cannot write memory through chat tools. There is no automatic extraction
from conversations, embedding service, or online weight update. The separate sleep
workflow below reviews already-saved records.

Forget removes the connected saved-memory family, including its corrections,
consolidated descendants/retained sources and related review drafts, from memory
and its search index. It does not erase earlier conversation text, completed tool traces,
backups, or exported files. These are separate records and retention choices.
Memory exports include earlier corrected versions and sleep audit/lineage;
ordinary retrieval does not.

## Memory sleep and review

The owner asked for an existing approach rather than inventing a consolidation
engine. We compared Letta dreaming, Mem0 Dream and LangMem. The
[research note](../research/tooling/memory-sleep-2026-11-12.md) records sources,
tradeoffs and the implemented boundary. `langmem` and `langchain-openai` are now
locked dependencies. `create_memory_manager` performs typed proposal extraction;
it does not directly write or delete BFI's database.

At `/handler`, Memory sleep runs manually with **Sleep now**, or automatically
while the app remains running. Defaults: enabled, ten idle minutes, at least an
hour between automatic attempts, up to 20 candidate records, and a 2048-token
model output limit. The page can change these values, disable model review, or
disable automatic exact merges. Oldest unreviewed records get considered first;
context fit may reduce coverage. A run reports how many records it reviewed.
Cross-batch semantic comparisons are not comprehensive.

Exact duplicate cleanup needs no model. It compares text after whitespace
normalization, preserving case/punctuation, scope and kind. Automatic merges keep
original records as superseded, retain source links and offer **Undo change**.
Model-assisted review needs a real endpoint with structured function-tool support.
Mock mode explicitly reports that limitation; it never pretends to have reviewed
meaning or verified facts. It can still perform exact cleanup.

LangMem can propose semantic merges, evidence-supported wording corrections,
alternate recall keywords, or conflicts. Only exact duplicates apply automatically.
Review/edit other proposals in the page, then apply or dismiss them. Resolving a
conflict requires your own text and source/reason. Pending valid conflicts are
marked in recall/context so a character is not silently given a settled fact.
This checks consistency against supplied evidence; it is not internet fact checking.

Shared memories use the selected shared reviewer connection. Each private scope
uses only its own profile's endpoint, in a separate call. No hosted model fallback,
embedding request or LangSmith tracing is enabled. Sleep holds the same local
generation lock as chat, and a new chat request preempts/cancels sleep. Closing
the external HTTP request does not prove the runtime immediately stops GPU work.

Review runs, proposals and settings persist in `knowledge.sqlite3`. Restarted work
becomes interrupted without replay. Applying checks that the exact source records
are still current; undo refuses to overwrite newer edits. Forget purges related
proposal snapshots, preventing undo or a late model result from restoring forgotten
text. Separate old exports/conversations/backups remain separate records.

Use **Test recall** to check keywords and character scope. Importance (1–5) affects
which records remain available as general context; it is not model confidence.

## Personality settings ready for later crafting

`/personalities` provides independent Academic, Engineering and Business editors:
display name, purpose, tone, traits, values, interests, relationship/speaking style,
humor, initiative, response length, boundaries, fictional backstory and custom notes.
The initial values are provisional scaffolds based on the existing profiles, not
final characters. The optional backstories are blank.

Preview shows the actual compiled system prompt. Saving creates a durable revision;
history can restore an earlier revision as a new one. Export includes all revisions.
Stale saves are rejected so two browser tabs do not overwrite each other's work.
New conversations snapshot the active revision and record it in reply provenance.
Existing conversations retain their earlier prompt; start a new chat for new settings.
The original profile's evidence/tool rules remain part of the compiled prompt.
Style controls do not grant tools, change memory scope or train model weights.

## Research library and cross-chat continuity

The two original research reports, 168-URL source catalog and later research notes are bundled under
`research/tooling/`. A manifest indexes them into SQLite FTS5 at startup. Results
retain the source, review date, document ID, and section number. Indexing uses no
model calls or remote service. Quotes and operators in queries are treated as
literal words, not executable FTS syntax.

At `/library`, search reports, read full text, add a sourced report, or export the
library. Owner-added reports persist in `data/knowledge.sqlite3`; bundled reports
remain individually versioned in Git. This does not automatically merge reports
or claim their documented capabilities were tested on the PC.

Full copies of the reports, their source catalog, and a handler handoff also live
in the private Notion **BFI research library and handler handoff**, linked from
the BFI project home. Future chats with that connection can search this title.
Notion access is not required by the local application and is not guaranteed in
every chat. Private page identifiers are not published in repository files.

## Verification and remaining work

Automated tests use scripted backends and simulated HTTP/SSE. Browser checks use
real Chromium against a visibly simulated local server. They establish actual
queue, UI, persistence, streaming transport and failure behavior; they do not
establish model reasoning, GPU performance, training, adapter loading, voice,
external model lifecycle, or native Windows overlay behavior.

`uv run --locked pytest`
`uv run --locked ruff check .`
`uv run --locked ruff format --check .`
`uv run --locked --group browser python scripts/browser_handler.py`

The browser script currently uses `/usr/bin/chromium` in the cloud environment.
The existing smoke script accepts `--chromium PATH` for other installations.
The visual regression stays paused; no artwork was regenerated or deployed.
