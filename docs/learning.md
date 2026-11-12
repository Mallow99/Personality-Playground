# Make this project yours

The goal is both a useful local character and understanding how to build and train
one. The primary interface is a standalone desktop window. AI can help with code;
the important thing is being able to inspect, reproduce, and question the result.

## Follow a message

1. **`bfi/__main__.py`** starts the desktop application.
2. **`bfi/desktop.py`** builds the Tk window. `send` reads the draft and passes the
   work to `run_task`, which runs it on a worker thread so the window stays
   responsive. `poll` brings the result back to the main thread, and `finish`
   either renders it or shows the error.
3. **`bfi/service.py`** is the application itself, with no window code. `ChatService.send`
   validates the message and chooses a bounded set of recent exchanges in `context_for`.
4. **`bfi/backends.py`** either returns clearly labeled scripted text or calls the
   separately running local model server. A mock is not model inference.
5. **`bfi/store.py`** commits the user and assistant messages together in SQLite.
6. The window displays the result. **Reply source details** shows recorded model
   provenance; **Export JSON** saves the transcript and metadata to a chosen file.

`bfi/config.py` reads settings and the character file. `bfi/errors.py` defines
`AppError`, the one kind of failure the window shows to you word for word.

## Try it

Run the commands in the README, send a message in mock mode, and inspect the reply
source. Close and reopen the app to confirm the conversation is saved. Change the
character configuration and start a new conversation to see the new snapshot;
old conversations retain the original configuration. Keep private exports out of Git.

Two experiments that show why the code is shaped the way it is:

- **Why a worker thread?** In `tests/test_desktop.py`, `GateBackend` holds a reply
  until the test releases it. Read `test_controls_lock_while_generating_and_closing_asks_first`
  to see what the window does in the meantime.
- **Why are both messages saved together?** In `bfi/service.py`, add
  `raise RuntimeError("boom")` just before `self.store.start(`, run the app, and send
  a first message. You get an error, your draft is still there, and no conversation
  was created. Remove the line afterwards.

Look at `git diff` before and after a change. Run `uv run --locked pytest` to check
the application behavior (on Linux, `xvfb-run -a uv run --locked pytest` so the
window tests have a display). The automated tests use temporary databases and
simulated model-server responses: they do not prove that a real model or GPU works.

## Questions to explore

- Which process generates a reply, and what history does it receive?
- Why may only the main thread touch the window, and how does a result get back to it?
- Why is a saved transcript different from cross-conversation memory?
- Why is editing a prompt different from changing model weights?
- What would demonstrate that a trained adapter was actually loaded and improved
  the target behavior without harming task performance?
