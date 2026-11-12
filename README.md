# Best Friend Initiative

A local AI character workbench, and a place to learn how to build and train one.
The GitHub repository is currently named **Personality-Playground**; Best Friend
Initiative is the working project name.

The ambition is useful characters with distinct voices, priorities, habits, opinions,
visual identities, persistent memory, and tools. **Training personality into model
weights is a central goal.** LoRA is a valid route. Prompts, memory, and application
code support that research; they do not replace it.

This project also builds its owner's skills. AI can do much of the coding, but the
owner should be able to inspect it, reproduce the results, explain the choices, and
make informed changes. Start with [the code walkthrough](docs/learning.md).

Where the project is going: the [roadmap](docs/roadmap.md). Work that is ready to
start, written so it can be handed to an AI model: the [task cards](docs/tasks.md).

## Milestone 01: a small, working foundation

- A standalone desktop chat window for one provisional character.
- A replaceable backend: a clearly labeled scripted mock, or a configurable
  loopback OpenAI-compatible chat endpoint.
- Saved conversations in SQLite, JSON export, and deletion.
- A readable character configuration, snapshotted when a conversation begins.
- Connection checks, understandable errors, and source information on each reply.
- A [route to the first personality-training experiment](docs/training.md), with
  an unmodified-model comparison and a research question still open for discussion.

**Default mode is mock. It runs no model.** Real inference requires a separate server
and model. The app never silently switches to mock if that server fails.

There is no personality training, tool execution, cloud delegation, calendar access,
voice, model management, or cross-conversation memory implemented yet. Saved chat
history is the first persistence layer; it is not a general memory system.

## Run it

Install [Python 3.11+](https://www.python.org/downloads/) and
[uv](https://docs.astral.sh/uv/getting-started/installation/), a tool that installs
this project's Python dependencies into its own `.venv` directory.
In a terminal inside the repository:

```sh
uv sync --locked
uv run --locked python -m bfi
```

The command opens the standalone desktop window. Close the window to exit. The same
commands work in Windows PowerShell and on Linux with a graphical desktop and Tk
installed. Python on Windows normally includes Tk; Linux may require its tkinter
package. This is a Python application, not yet a packaged installer or executable.
The checked-in `uv.lock` records exact dependency versions; `--locked` refuses to
silently change that record. No Node.js, GPU, model download, or subscription is
needed for mock mode.

Optional configuration:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```sh
# Linux / macOS
cp .env.example .env
```

Edit `.env`, then restart the app. Environment variables already set in your terminal
take priority over `.env`. Relative paths resolve from the repository root.

### Connect a real local model

1. Separately install a compatible inference server and a supported model. See the
   [hardware and backend notes](docs/hardware.md) before choosing a download.
2. Configure that server to listen on your PC's loopback address. If using
   llama.cpp with an **already downloaded, compatible** GGUF, a starting command
   is below. Executable paths differ by installation and OS. Adjust GPU layers and
   context to fit your machine; this is a setup example, not a measured recommendation.

   ```sh
   llama-server -m /path/to/model.gguf --alias local-model --host 127.0.0.1 --port 8080 -c 4096 -ngl 99
   ```

3. Set these entries in `.env`:

   ```dotenv
   BFI_BACKEND=openai
   BFI_BASE_URL=http://127.0.0.1:8080/v1
   BFI_MODEL=local-model
   ```

4. Restart the app and click **Check backend**. The
   configured model must match a server ID or alias. A successful `/models` check
   establishes reachability, not successful generation. Send a short message to test
   generation, then inspect its source information.

Start a **new conversation** after changing the backend, endpoint, or model. Existing
conversations stay readable but cannot be continued with a different configuration.
This keeps scripted mock history out of real model context. Character edits also
apply to new conversations; older chats keep their original character prompt.

`openai` names an API format, not OpenAI's hosted service. This milestone accepts
loopback HTTP(S) endpoints only and never follows redirects. A local server can
itself proxy a cloud service; the app cannot independently verify where that server
computes. It records the requested ID and the server-reported ID separately, with
“no cloud assistance by this app” rather than claiming verified offline inference.

## Inspect your work

| What you want to understand                | Where to start                                     |
| ------------------------------------------ | -------------------------------------------------- |
| What happens when you press Send           | [Learning walkthrough](docs/learning.md)           |
| Why these components were chosen           | [Architecture and decisions](docs/architecture.md) |
| Character name, description, and prompt    | [config/character.json](config/character.json)     |
| Endpoint, model, and context limits        | [.env.example](.env.example)                       |
| Desktop window, worker thread, dialogs     | [bfi/desktop.py](bfi/desktop.py)                   |
| Application rules, with no window code     | [bfi/service.py](bfi/service.py)                   |
| Real server requests and the mock          | [bfi/backends.py](bfi/backends.py)                 |
| SQLite tables and persistence              | [bfi/store.py](bfi/store.py)                       |
| Hardware checks and compatibility evidence | [Hardware notes](docs/hardware.md)                 |
| Larger ambition                            | [Project vision](docs/vision.md)                   |
| Order of work and open decisions           | [Roadmap](docs/roadmap.md)                         |
| What to build next, card by card           | [Task cards](docs/tasks.md)                        |
| First controlled training experiment       | [Training plan](docs/training.md)                  |

## Verify it

```sh
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

On Linux the window tests need a display; without one they are skipped. To run them
anyway, use a virtual display: `xvfb-run -a uv run --locked pytest`.

The suite uses temporary databases and simulated model-server responses to test
persistence, context selection, provenance, failure handling, and the real Tk window
(sending, failures, draft retention, closing mid-reply). It does not download or
exercise a model. GitHub Actions runs the same checks on Windows and Linux for every
push. See [verification notes](docs/verification.md) for what was actually run and
what still needs a person at a Windows PC.

The app contains no web server and opens no listening port.

## Data and current limits

Conversations live in `data/conversations.sqlite3`, outside Git. They are plain text
on disk, not encrypted. Export JSON before sharing or resetting a conversation;
exports contain private text, the character prompt, endpoint metadata, and provenance.
Deleting a conversation removes its rows, not existing exports or backups. SQLite
deletion is not a secure erase guarantee. Stop the app before backing up its data file.

The app sends the character prompt, current message, and a bounded window of recent
complete exchanges to the configured endpoint. Older text remains saved but may not
be sent; per-reply provenance reports omissions. Character counts and pair limits
are approximate guards, not model-specific token budgeting. Context overflow can
still happen; reduce the limits if your server rejects requests.

Only complete exchanges are saved. If a reply fails, nothing is written and your
draft stays in the message box. If you close the window while a reply is being
generated, the message you sent is discarded; the app asks before closing.

One app process, one active generation, non-streaming text, and one local user are
intentional limits. There is no Stop button yet. Replies display as plain text. The desktop app is intended for one
local user, not shared or public deployment.
The app does not start, load, or unload model servers. Stop the separate inference
process to release its model; merely closing this UI does not free VRAM.

Models, adapters, training runs, conversation data, and `.env` are ignored by Git.
Do not commit credentials or private exports. No open-source license has been chosen
yet; publishing source does not grant a general reuse license. Model and dataset
licenses must also be checked independently.

## Hardware baseline

Purchased PC; specifications and stability await arrival and verification:

| Component   | Planned hardware                                                 |
| ----------- | ---------------------------------------------------------------- |
| CPU         | Intel Core i7-13700K                                             |
| GPU         | Radeon RX 7900 XTX, 24 GB VRAM                                   |
| RAM         | 32 GB DDR5                                                       |
| Motherboard | MSI PRO Z790-P WIFI                                              |
| Storage     | 1 TB NVMe SSD                                                    |
| OS          | Windows 11; a separate Linux installation is a later possibility |

64 or 96 GB RAM is a possible upgrade **only if measurements justify it**. Additional
hardware and school funding are not assumed. No speed, memory-fit, training, or
custom-model serving result from that PC is claimed in this milestone.
