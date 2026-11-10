# What was actually verified

Milestone 01 was checked in a Linux cloud development workspace on November 9,
2026, using Python 3.12.14, uv 0.13.5, and Chromium 156.0.8078.79. This workspace is not the purchased Windows
PC, and has no configured inference server or selected model. No claim about its
7900 XTX performance, AMD training, or learned personality follows from these checks.

## Automated application checks

```sh
uv sync --locked
uv run --locked pytest -q
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Result after the profiles/tools increment: **43 tests passed**; lint and Python formatting passed. The tests cover
restart persistence, character snapshots, backend separation, request validation,
deletion, context trimming, API request shape, source metadata, credential exclusion,
backend errors, model-status uncertainty, local browser boundaries, and overlapping
generation. HTTP adapter tests use simulated responses; they do not run a model.
New coverage verifies the three distinct profile prompts, per-profile routing,
credential exclusion, old-route separation, actual project reads, hidden/private
path rejection, symlink boundaries, explicit tool permissions, a complete simulated
model/tool/model round trip, persisted trace and token totals, tool-call limits,
and Brave request/source/error behavior. Live web search is not verified without a key.

The installed Starlette test client emits one upstream deprecation warning about
its use of `httpx`. This does not fail the suite; revisit the development test
transport when upgrading dependencies. JavaScript syntax was also checked with
`node --check bfi/static/app.js`; Node is not needed to run the application.

GitHub Actions is configured to run the Python checks on Windows and Linux with
Python 3.11. Those hosted runs have not been observed in this workspace. Local Linux
success should not be reported as a successful Windows or hosted CI run.

## Repeatable browser check

The optional [`scripts/browser_smoke.py`](../scripts/browser_smoke.py) starts two
temporary application processes: a labeled mock and an endpoint configuration whose
server is deliberately unavailable. It uses disposable databases, then terminates
those processes. It does not open or delete your normal conversation data.

Install the optional browser-test dependencies and browser, then run:

```sh
uv sync --locked --group browser
uv run --locked --group browser playwright install chromium
uv run --locked --group browser python scripts/browser_smoke.py
```

This environment already had system Chromium, so the actual successful command was:

```sh
uv run --locked --group browser python scripts/browser_smoke.py --chromium /usr/bin/chromium
```

Result: **passed**. Verified visibly labeled mock replies, sending with Enter,
plain-text rendering, per-reply provenance, JSON export, reload persistence,
new/reopened conversations, the status dialog, deletion, draft retention after a
real HTTP connection failure, and continued operation with browser storage disabled.
Checked layouts at 1440×1000, 768×1024, and 390×844 with no horizontal page overflow.
The main test page produced no JavaScript errors or external network requests.
The extended script also checks all three profiles in actual chat, studio-to-chat
selection, themes, poses, motion controls, in-app corner presence, and actual reads
from a disposable project fixture. It saves all three studio directions. Separate
1440×1080 screenshots of all three studio/chat themes were visually inspected; the
studio mobile text-fit issue found during inspection was corrected and rechecked.

Screenshots and the scripted test export are saved under `runs/browser-smoke/`,
which Git ignores. Initial home and mobile screenshots were also visually inspected.
To inspect without installing browser automation, repeat these actions manually
using the walkthrough in `learning.md` and the normal mock app.

## Remaining validation

- Actual local inference on the delivered PC, including GPU use and latency.
- Specific Windows/AMD driver and training-stack compatibility.
- Real model aliases, templates, context/token limits, and quantized artifacts.
- A trained adapter, held-out base comparison, conversion/reload, and custom serving.
- Human usability and accessibility feedback beyond keyboard controls, semantic
  labels, focus styling, reduced-motion handling, and the browser layout checks.

No real-model benchmark or training result has been manufactured to fill those gaps.
