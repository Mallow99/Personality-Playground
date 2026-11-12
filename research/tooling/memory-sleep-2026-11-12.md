# Memory sleep: existing approaches and the BFI integration

Reviewed 2026-11-12. The owner asked for sleep-time memory review and smarter recall,
then explicitly asked to check existing systems and reuse work. This is a separate
research/implementation note to preserve for the eventual combined report. It does
not supersede the original full-stack or memory reports.

## Compared approaches

| System | Documented approach | Relevance and decision |
| --- | --- | --- |
| [Letta memory and dreaming](https://docs.letta.com/configuration/memory) | Git-backed MemFS, background dreaming that reviews conversations and updates memory; optional second agent review before applying; backups for larger reorganizations | Useful separation between active conversation, reflection and revision history. Its current agent/runtime/filesystem model would replace more of BFI than this increment needs. Researched, not installed. |
| [Mem0 Dream](https://docs.mem0.ai/platform/features/dream) | Separates merge, supersede and scheduled synthesis. Synthesized patterns retain links to source memories. Its hosted platform has separate availability/settings for these operations | Adopt the distinction between consolidation, changed facts and new inference, plus explicit source links. Hosted Dream is not assumed to be an included local open-source feature. Not installed or used as a remote service. |
| [LangMem memory manager](https://langchain-ai.github.io/langmem/reference/memory/) and [background guide](https://langchain-ai.github.io/langmem/background_quickstart/) | Reusable Python memory extraction/consolidation with Pydantic schemas, existing-memory input, update/delete controls and background integration. Its examples distinguish transient from persistent stores and discuss delaying work until activity settles | Selected reusable library. BFI calls its typed manager against an explicitly configured local model; BFI retains its existing durable storage and resource scheduling. |

## What was reused

The lockfile records `langmem==0.0.30` and `langchain-openai==1.7.4`, including their
transitive dependencies. This increases the dependency footprint; it avoids writing
a new model memory-extraction engine and keeps the library behind one adapter.
LangMem is MIT licensed; its repository and upstream license are available at
[langchain-ai/langmem](https://github.com/langchain-ai/langmem).

`bfi/memory_sleep.py::langmem_review` uses `create_memory_manager` with a typed
`ReviewBatch`/`Suggestion` schema. The library handles structured generation and
validation. The adapter points ChatOpenAI at the chosen loopback URL/model, not a
hosted default, and disables tracing, inherited proxies and redirects. A structured
tool-capable local endpoint is still required; compatibility is not inferred from
the endpoint advertising a model name.

The manager produces proposals, not direct store mutations. Updates/deletes to a
LangGraph store are disabled. We deliberately do not use the documentation's
in-memory store or default hosted embedding example. BFI's existing SQLite store
remains authoritative, including corrections, forgetting and history.

## Application-specific work

The necessary glue is the resource/lifecycle policy, local UI, scope validation and
audit application. Background thread executors cannot safely bypass BFI's shared
async generation lock on a single local GPU, so BFI schedules the LangMem call in
its own idle loop. New chat work cancels sleep and takes priority. A restart never
replays an unfinished review automatically. The app must remain running.

Conservative automatic cleanup compares exact text after whitespace normalization
within one scope and kind. Case and punctuation are preserved. Applying a merge
keeps old records as superseded, writes the replacement, updates FTS5 and records
parent links in one SQLite transaction. Undo restores the originals only while
the result is unchanged. Later owner edits and forgetting defeat stale proposals.
Related review snapshots are purged when a connected memory family is forgotten.

Semantic merges, corrections, keyword enrichment and unresolved contradictions are
typed proposals for inspection. A model cannot establish the truth of a personal
fact merely by rewriting it. Conflicts require an owner-supplied resolution and
source/reason. Valid pending conflicts are surfaced in retrieval/context. The sleep
model has no search or operating-system tools and no automatic permission to erase
records or invent personal preferences.

## Recall and coverage

Recall remains lexical FTS5, now including up to eight alternate keywords per
memory. This gives a practical way for owner input or reviewed LangMem suggestions
to improve matching without a mandatory embedding server. Importance is a 1–5
owner priority, not confidence; it influences general context retention. Exact
duplicates are suppressed when building context, even before a sleep pass.

Model work is bounded by record count, context headroom, output tokens and timeout.
Oldest unreviewed records are prioritized. A run reports its actual coverage;
relations across unselected batches can be missed. Default idle wait is ten minutes,
minimum automatic interval one hour, review limit 20 records and output limit 2048
tokens. Private records use only that character's route; shared records use the
selected shared reviewer. Repeated reflection is not presumed to improve quality.

## Verification boundary

Tests exercise migrations, scope/kind boundaries, whitespace/case distinctions,
transactional changes, stale source rejection, undo, forgetting during a model
call, conflict warnings, keyword recall, idle scheduling and chat preemption.
One integration test calls the real installed LangMem/ChatOpenAI stack against a
simulated OpenAI transport. Chromium exercises the real local HTTP path with fixed,
visibly simulated tool responses. Neither establishes model reasoning quality or
the delivered PC's inference performance.

Before enabling automatic semantic application, compare real models on paraphrases,
changed preferences, conflicting dates, uncertain claims, source retention, recall
and false-positive merges. Keep original evidence and measure useful outcomes, not
only how many records a summary removes. Personality settings added alongside this
work are versioned prompt scaffolds; they do not train personality into weights.
