# Verification

The initial application tests were run in a Linux cloud workspace, not on the
purchased Windows PC. They use temporary databases and simulated model-server
responses. They cover persistence, snapshots, backend separation, validation,
context trimming, source metadata, failures, and overlapping generation. They do
not establish real inference, GPU performance, training, or Windows compatibility.

Run the current checks with:

```sh
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

On November 12, 2026, the Tk desktop was launched in the Linux cloud desktop
using a disposable database. A mock exchange was sent, the application was
restarted, the saved conversation reopened, and a second message sent. This does
not establish Windows behavior or real model inference.

For a desktop check, run `uv run --locked python -m bfi` on a machine with a
working graphical desktop and Tk. In mock mode, send a message, inspect source
details, close and reopen the app, select the saved conversation, export it, and
check deletion on disposable data. Also check that an unavailable model server
shows an error and retains the draft. Desktop usability, accessibility, and the
Windows build still require validation on the target machine.

Actual local inference, AMD training-stack compatibility, a trained adapter and
held-out comparison, and verified custom-model serving remain open milestones.
