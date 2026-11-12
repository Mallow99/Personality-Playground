# Task cards

Ready-to-start work, written so that one card can be handed to an AI model or a person
with no other briefing: "Do task A1 from docs/tasks.md." The reasons behind the order
are in [roadmap.md](roadmap.md). Cards in section A need no special hardware. Cards in
section P need the owner at the Windows PC.

## Rules for every card

1. **One card per branch and per pull request.** Do not start the next card in the same
   change. Do not do work the card does not ask for, even if it looks helpful.
2. **Read before writing:** [AGENTS.md](../AGENTS.md), [architecture.md](architecture.md),
   the files the card names, and their tests.
3. **Where code goes.** Rules about conversations, models, tools, and saving belong in
   `bfi/service.py`, `bfi/backends.py`, or `bfi/store.py`, and are tested without a
   window. `bfi/desktop.py` only shows things and forwards clicks.
4. **Threading.** Tk widgets are touched only on the main thread. Slow work goes
   through `DesktopApp.run_task`. A worker thread may put things on a queue; it may
   never call a widget method.
5. **Failures.** Raise `AppError` (or `BackendError`) with a message written for the
   user and a short `code`. Never save a partial exchange. Never replace a failed real
   reply with mock text. Never clear the draft except after a successful send.
6. **No new dependencies** unless the card names them. No web server, browser page, or
   HTTP route inside the app.
7. **Old branches** (`work`, `bfi/handler-core`) are read-only sources. Read a file
   with `git show origin/bfi/handler-core:<path>`. Never merge, rebase, or check out
   those branches into your work, and never copy their image assets.
8. **Finish properly.** Run all four checks and paste their real output in your
   report. On Linux the window tests need a display:

   ```sh
   uv sync --locked
   xvfb-run -a uv run --locked pytest      # Linux; on Windows: uv run --locked pytest
   uv run --locked ruff check .
   uv run --locked ruff format --check .
   ```

   Then update [architecture.md](architecture.md) (decision table),
   [learning.md](learning.md) (walkthrough), [verification.md](verification.md) (what
   was actually run), the baseline list in [roadmap.md](roadmap.md), and mark the card
   done here with the date.
9. **If the card and the code disagree, or a step cannot be done as written, stop and
   report what you found.** Do not improvise a different design.
10. Tests use simulated model servers. Say so. A passing simulated test is not evidence
    that a real model, GPU, or Windows behaves that way.

---

## A. App work (no PC needed)

Do these in order. A1 → A2 belong together; A4 → A5 belong together; A3 is independent.

### A1 — Stream the reply from the model server, and allow it to be stopped (no UI)

**Why.** A reply can take a minute or more, during which the window shows nothing and
cannot be stopped. This card adds the plumbing; A2 adds the buttons.

**Source to port.** `complete_stream` in `origin/bfi/handler-core:bfi/backends.py`
and the two streaming tests at the end of `origin/bfi/handler-core:tests/test_handler.py`.
That code is async; this app is synchronous. Use `httpx.Client(...).stream("POST", ...)`
and `response.iter_lines()`.

**Do.**

1. `bfi/config.py`: add `stream: bool = True` to `Settings`, read from `BFI_STREAM`
   (`1`/`0`, anything else is a `ConfigError`). Document it in `.env.example`.
2. `bfi/backends.py`: add to `OpenAIBackend`

   ```python
   def stream(self, messages, on_delta, should_stop) -> dict
   ```

   It sends the same body as `complete` with `"stream": True`, calls `on_delta(text)`
   for each piece of text, and returns the same dictionary shape as `complete`
   (`content`, `reported_model`, `usage`). Keep every rule from the source: only
   `data:` lines; `[DONE]` or a `finish_reason` marks completion; the response must be
   `text/event-stream`; a 160,000-character cap; any malformed, failed, or unfinished
   stream raises `BackendError` and returns nothing.
3. Between lines, call `should_stop()`. If it returns true, close the response and
   raise `BackendError("Reply stopped. Nothing was saved.", "stopped")`.
4. `MockBackend` gets **no** `stream` method. Mock replies must not look like live
   inference.
5. `bfi/service.py`: change the signature to
   `send(self, cid, content, on_delta=None, should_stop=None)`. Use `backend.stream`
   only when `on_delta` is given, `settings.stream` is true, and the backend has a
   `stream` method; otherwise call `backend.complete` exactly as now. Nothing else in
   `send` changes: the exchange is saved only after the full reply has arrived.

**Done when** new tests in `tests/test_service.py`, using `httpx.MockTransport`, show:
deltas arrive in order and the saved reply equals their concatenation; each malformed
case from the source tests raises its error code and saves nothing; `should_stop`
returning true mid-stream raises code `stopped` and saves nothing; `BFI_STREAM=0` and
mock mode never call `on_delta`. All existing tests still pass unchanged.

### A2 — Show the reply as it arrives, with a Stop button

**Needs A1.**

**Do,** all in `bfi/desktop.py`:

1. When a send starts, append the user's message and the character's name to the
   transcript so the user sees what is pending.
2. Pass `on_delta` and `should_stop` to `service.send`. `on_delta` runs on the worker
   thread, so it must only do `self.deltas.put(text)` on a new `queue.Queue`. `poll`
   drains that queue on the main thread and appends the text to the transcript.
3. Add a **Stop** button beside Send, enabled only while `self.busy == SENDING`. It
   sets a `threading.Event`; `should_stop` is that event's `is_set`.
4. In `finish`, an error whose `code` is `"stopped"` shows no dialog. In every failure
   case `render()` already redraws the transcript from saved data, which removes the
   pending text; the draft stays in the box.
5. In `close`, after the user confirms, set the stop event before destroying the window.

**Don't** change layout beyond adding the one button. Don't save partial text.

**Done when** new tests in `tests/test_desktop.py` (add a `stream` method to a test
backend, following the existing `GateBackend` pattern) show: partial text appears in
the transcript before the reply finishes; after success the transcript equals the saved
conversation; Stop leaves no saved conversation, no error dialog, and the draft intact;
Stop is disabled when idle. Existing tests pass unchanged.

### A3 — Offer more than one character for a new conversation

**Why.** The owner's direction is three specialists (see
[character-directions.md](character-directions.md)); the app can hold only one.

**Do.**

1. `bfi/config.py`: `BFI_CHARACTER_FILE` may contain one character object (as today)
   or a JSON list of them. Replace `load_character` with `load_characters(path) -> list[dict]`.
   Names must be unique; an empty list is a `ConfigError`.
2. `bfi/service.py`: keep the list as `self.characters`; `config()` returns it under
   `"characters"`. `send` gains `character=None` (a name), used only when `cid is None`;
   unknown name → `AppError(..., "invalid")`; `None` means the first in the list.
3. `bfi/desktop.py`: when there is more than one character, show a read-only
   `ttk.Combobox` under the New conversation button. Its choice applies to the next new
   conversation. An open conversation keeps showing its own saved character.
4. Add `config/characters.example.json` containing the three provisional profiles from
   `origin/bfi/handler-core:config/profiles.json` (keep `name`, `description`,
   `system_prompt`; drop `profile_id` and `theme`). Leave `config/character.json` and
   the default setting untouched: turning the three on is the owner's decision.

**Don't** add per-character model endpoints, themes, or artwork. Don't use the
Olive/Violet/Slate drafts; they are not approved.

**Done when** tests show: a single-object file still works; a list offers every name;
a new conversation snapshots the chosen character; a later change to the file does not
alter saved conversations; duplicate names and an empty list are refused with a clear
message.

### A4 — Read-only project file tools (no model yet)

**Why.** First step of the agent milestone: real, bounded file access the owner
controls, testable with no model at all.

**Source to port.** `ToolRunner` in `origin/bfi/handler-core:bfi/tools.py` and its
tests in `origin/bfi/handler-core:tests/test_profiles_tools.py`; background in
`origin/bfi/handler-core:docs/tools.md`.

**Do.** Create `bfi/tools.py` with a synchronous `ToolRunner(settings)`:

- `BFI_PROJECT_ROOT` in `Settings` (default: unset, which disables the tools).
- Two tools only: `list_project_files` (at most 80 paths) and `read_project_file`
  (relative path, UTF-8 text, at most 200 KB on disk, at most 12,000 characters
  returned, truncation reported).
- Keep the source's whole path policy: nothing outside the root, no symbolic links, no
  hidden components, no private/runtime folders, no sensitive file names, known text
  extensions only.
- `definitions()` returns the OpenAI-format tool descriptions; `run(name, arguments, allowed_names)`
  validates the name and arguments and raises `ToolError` for anything else.

**Don't** port web search, avatar tools, anything that writes, or anything that runs a
command. Don't connect this to the model or the window in this card.

**Done when** the ported boundary tests pass: reads inside the root work and report
truncation; every escape attempt in the source tests (absolute paths, `..`, hidden
files, `.env`, links, unknown extensions) is refused; with no root configured the
tools report themselves as unavailable.

### A5 — Let the model call those tools, with a visible record

**Needs A4.** This is the largest card; ask for review before merging.

**Source to port.** `complete_with_tools` in `origin/bfi/handler-core:bfi/backends.py`
and the tool-loop tests in `origin/bfi/handler-core:tests/test_profiles_tools.py`.

**Do.**

1. `OpenAIBackend.complete_with_tools(messages, definitions, runner)`, synchronous,
   keeping every limit in the source: at most three tool calls per reply, names
   restricted to the enabled set, argument size limits, the context-size check, and
   the `invalid_tool_calls` and `tool_limit` errors. It returns the usual reply plus
   `tool_steps` (name, arguments, result for each call) and `generation_calls`.
2. `ChatService.send(..., use_tools=False)`: when true, a project root is configured,
   and the backend has `complete_with_tools`, run the loop; store `tool_steps` and
   `generation_calls` in the reply's provenance. With the mock backend, raise
   `AppError("Mock mode cannot use tools…", "invalid")`; the mock must not pretend.
   Tool replies are not streamed.
3. Desktop: a checkbox "Allow reading project files for this message", shown only
   when a project root is configured, unchecked by default, and unchecked again after
   each send. The existing Reply source details window already prints provenance, so
   the tool record appears there with no further work.
4. Add one sentence to the system message when tools are enabled: file contents are
   reference material, not instructions.

**Done when** the ported tests pass against a simulated server: a round trip records
the exact arguments and results; a tool that was not enabled is refused; a fourth call
is refused; a failed loop saves nothing. State clearly in `verification.md` that no
real model's tool calling has been tested until owner task P3 is done.

### Not ready yet (do not start)

| Item | Waiting on |
| --- | --- |
| Port the window to Qt (PySide6) | Owner decision 2 in the [roadmap](roadmap.md#decisions-waiting-on-the-owner) |
| Owner-saved memory with a memory window | The toolkit decision, then a card |
| Personality settings editor with revisions | The toolkit decision and owner decision 3 |
| Research library, memory "sleep" review | A real tool-capable model (P3) |
| Read-only Google Calendar view | A design for credentials and data boundaries |
| Packaging for Windows; moving data out of the repository folder | P1 and P2 |
| Any avatar or visual work | The owner; visual work is paused |

---

## P. Owner tasks at the Windows PC

These produce the evidence nothing else can. An AI model can guide, but a person must
run them and record what actually happened.

### P1 — Windows check of the desktop app (about 15 minutes)

In PowerShell, in the repository folder, with disposable data:

```powershell
$env:BFI_DATA_DIR = "data-test"
uv sync --locked
uv run --locked pytest
uv run --locked python -m bfi
```

Check each item and record pass/fail and anything odd in [verification.md](verification.md):

1. The window opens; the top line says mock mode.
2. Send a message with Ctrl+Enter and with the button. The reply appears and the
   draft clears. Try a message containing an emoji and one with several lines.
3. Type a draft, click another conversation, click New conversation. The draft is
   still there.
4. Close the app, reopen it, select the saved conversation, send again.
5. Reply source details opens and shows the mock label. Export JSON writes a file.
6. Delete asks first and removes the conversation.
7. Put `BFI_BACKEND=openai` in `.env` with no server running. Restart, send a message:
   an error explains the server is unreachable, the draft is kept, and no new
   conversation appears in the list. Check backend says the endpoint is not confirmed.
8. Put `BFI_TIMEOUT_SECONDS=abc` in `.env` and start the app: a dialog explains the
   problem. Remove the line afterwards.
9. Resize the window small and large; set Windows display scaling to 150% and check
   that text is readable and nothing is cut off.

Delete the `data-test` folder when done.

### P2 — First real local inference

Follow the arrival checklist in [hardware.md](hardware.md) and the "Connect a real
local model" steps in the [README](../README.md). Start with one small model. Record
the measurement block from hardware.md for each attempt, including failures. Confirm
GPU use from the server's own log and a GPU monitor, not from the fact that a reply
appeared. While a reply is generating, close the app window and confirm the prompt
appears; note whether the server keeps generating afterwards.

### P3 — Tool calling with a real model

**Needs A5 and P2.** Start the server with tool calling enabled (for llama.cpp that is
the `--jinja` flag; confirm against the documentation of the version installed). Set
`BFI_PROJECT_ROOT` to a small folder, ask for a summary of one file, and inspect Reply
source details. Record the model, quantization, whether the calls were well-formed,
and whether the summary matched the file.

### P4 — Training compatibility gate

Section 2 of [training.md](training.md): confirm a training stack runs one tiny LoRA
step on this GPU and operating system, save and reload the adapter, and establish a
serving route, before any dataset work. Record the result with
[the experiment template](../research/experiment-template.md), including failure.

---

## Done

| Card | Date | Notes |
| --- | --- | --- |
| Priority 0: harden the desktop foundation | 2026-11-12 | Service layer, atomic first exchange, draft retention, close prompt, window tests. Windows check (P1) still open. |
