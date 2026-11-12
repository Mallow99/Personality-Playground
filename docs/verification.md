# Verification

What has actually been run, where, and what it does and does not establish.

## Automated checks

```sh
uv sync --locked
uv run --locked pytest            # Linux: xvfb-run -a uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

The suite has 40 tests. 30 exercise the application rules in `bfi/service.py` with
temporary databases and simulated model-server responses: persistence across a
restart, character and backend snapshots, context trimming, provenance, every backend
failure mode, the one-generation lock, configuration mistakes, and refusing a
database from a newer app version. 10 drive the **real Tk window** with a controllable
backend: a successful send, a failed send keeping the draft and creating exactly one
conversation on retry, controls locking during a reply, the close-during-reply prompt
(both answers), drafts surviving a conversation switch, deletion, an archived
conversation, an unexpected error, a bug inside a UI callback, and a startup problem.

Without Tk or a display, the 10 window tests are skipped. A skip is not a pass. CI
sets `BFI_REQUIRE_TK=1`, which turns a missing display into a failure.

## What was run on November 12, 2026

| Where | What | Result |
| --- | --- | --- |
| Linux cloud workspace, Python 3.11.15, Tk 9.0, virtual display (Xvfb) | All four checks, the suite repeated several times | 40 passed; lint and format clean |
| Same | Each targeted fix was undone on purpose to confirm a test fails: no reschedule after a callback error, New conversation wiping the draft, closing without asking | Each mutation was caught by a window test |
| Same | The app was started with `python -m bfi` and left running; a scripted run sent a mock message, opened Reply source details, closed, restarted, reopened the saved conversation, and sent again | Worked; screenshots inspected |
| GitHub Actions, `ubuntu-latest` | All four checks, window tests on Xvfb | Run 2: 40 passed; lint and format clean |
| GitHub Actions, `windows-latest` (Python 3.11.18, Tk 8.6) | All four checks, window tests on the runner's desktop session | Run 1: 39 passed, 1 error (see below). Run 2, after the test fix: 40 passed; lint and format clean |

The first Windows CI run failed one window test: creating a new Tk interpreter for
every test intermittently could not find its Tcl files. The tests now share one
interpreter, as the real app does. That was a test problem, not an app problem, but it
is the kind of thing only Windows shows.

## What this does not establish

- **Nobody has used the app on Windows.** The Windows CI runner is a server image
  driven by a script. Fonts, display scaling, keyboard behavior, file dialogs, and how
  the window feels are unchecked. Owner task P1 in [tasks.md](tasks.md) is the
  checklist.
- **No real model has replied.** Every model response in the tests is simulated. Real
  inference, GPU use, speed, and memory need the owner's PC (task P2).
- **Closing mid-reply against a real server** is untested: the app discards the
  exchange, but whether the model server stops generating is the server's behavior.
- **A real slow or stalled server.** Timeouts are tested with simulated errors only.
- Training, adapter serving, and AMD training-stack compatibility remain open
  milestones.
