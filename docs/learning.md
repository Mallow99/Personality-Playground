# Make this project yours

The goal is both a useful local character and understanding how to build and train
one. The primary interface is a standalone desktop window. AI can help with code;
the important thing is being able to inspect, reproduce, and question the result.

## Follow a message

1. **`bfi/__main__.py`** starts the desktop application.
2. **`bfi/desktop.py`** builds the Tk window. `send` reads the draft, runs an
   operation on a worker thread, and renders the saved result. `request` passes the
   request to the application in process; it does not open a web server.
3. **`bfi/main.py`** validates the request and chooses a bounded set of recent
   exchanges in `context_for`.
4. **`bfi/backends.py`** either returns clearly labeled scripted text or calls the
   separately running local model server. A mock is not model inference.
5. **`bfi/store.py`** commits the user and assistant messages together in SQLite.
6. The desktop displays the result. **Reply source details** shows recorded model
   provenance; **Export JSON** saves the transcript and metadata to a chosen file.

## Try it

Run the commands in the README, send a message in mock mode, and inspect the reply
source. Close and reopen the app to confirm the conversation is saved. Change the
character configuration and start a new conversation to see the new snapshot;
old conversations retain the original configuration. Keep private exports out of Git.

Look at `git diff` before and after a change. Run `uv run --locked pytest` to check
the application behavior. The automated tests use temporary databases and simulated
model-server responses: they do not prove that a real model or GPU works.

## Questions to explore

- Which process generates a reply, and what history does it receive?
- Why is a saved transcript different from cross-conversation memory?
- Why is editing a prompt different from changing model weights?
- What would demonstrate that a trained adapter was actually loaded and improved
  the target behavior without harming task performance?
