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

## What works now

- A browser chat interface with three selectable provisional characters: Academic,
  Engineering (coding/security), and Business. Each has its own prompt, theme,
  conversation identity, and optional local model/endpoint overrides.
- A replaceable backend: a clearly labeled scripted mock, or a configurable
  loopback OpenAI-compatible chat endpoint.
- Saved conversations in SQLite, JSON export, and deletion.
- A readable character configuration, snapshotted when a conversation begins.
- Connection checks, understandable errors, and source information on each reply.
- E character artwork with 128 selectable poses, matching handler colors, an in-app
  corner avatar, a synchronized `/overlay` surface, and model-callable visual tools.
- An optional native overlay launcher; Windows transparency/topmost/click-through
  behavior still needs a PC check. See [avatar setup](docs/avatar-runtime.md).
- Optional read-only project tools and Brave web search, with a real result
  inspector and per-message opt-in for model-requested tool calls.
- A durable generation queue, cancellation, reload recovery, and genuine live
  reply previews for plain-text requests on SSE-compatible endpoints.
- Owner-saved cross-conversation memory with character scopes, sources,
  corrections, forgetting, export, and a searchable research library.
- A `/handler` setup/inspection page and `/library` research page. See the
  [handler guide](docs/handler.md) for connection presets and current boundaries.
- A [route to the first personality-training experiment](docs/training.md), with
  an unmodified-model comparison and a research question still open for discussion.

**Default mode is mock. It runs no model.** Real inference requires a separate server
and model. The app never silently switches to mock if that server fails.

There is no completed personality-training experiment, computer control, code
execution, cloud delegation, calendar access, audio, verified native desktop behavior, model
lifecycle management, or automatic memory extraction yet. Saved memories are
owner-curated; private scopes are enforced by the application. Profiles are currently
prompt configured; the weight-training goal remains explicit.

For the next session, read [the handoff](docs/HANDOFF.md) and [how the avatar works](docs/avatar-runtime.md).

## Run it

Install [Python 3.11+](https://www.python.org/downloads/) and
[uv](https://docs.astral.sh/uv/getting-started/installation/), a tool that installs
this project's Python dependencies into its own `.venv` directory.
In a terminal inside the repository:

```sh
uv sync --locked
uv run --locked python -m bfi
```

Open **http://127.0.0.1:8000** in your browser. The same commands work in Windows
PowerShell and on Linux. Stop the application with **Ctrl+C** in its terminal.
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

4. Restart the app, open the backend status panel, and check the connection. The
   configured model must match a server ID or alias. A successful `/models` check
   establishes reachability, not successful generation. Send a short message to test
   generation, then inspect its source information.

Start a **new conversation** after changing the backend, endpoint, or model. Existing
conversations stay readable but cannot be continued with a different configuration.
This keeps scripted mock history out of real model context. Character edits also
apply to new conversations; older chats keep their original character prompt.
Use the sidebar selector to switch profiles; it starts a fresh conversation. Read
[character and model planning](docs/characters.md) before assigning models by role.

`openai` names an API format, not OpenAI's hosted service. This milestone accepts
loopback HTTP(S) endpoints only and never follows redirects. A local server can
itself proxy a cloud service; the app cannot independently verify where that server
computes. It records the requested ID and the server-reported ID separately, with
“no cloud assistance by this app” rather than claiming verified offline inference.

## Inspect your work

The optional Notion project board holds the live idea inbox and a short Next list.
It is not needed to start or use the local app. See [planning](docs/planning.md).

The selected visual baseline is **[E](research/visual-studies/option-e.png)**. The
[reference gallery and design brief](research/visual-studies/README.md) preserve
the choice and earlier studies. The [E proof pack](bfi/static/e-preview/README.md) now provides 74 generated-reference pose traces, source/SVG comparisons,
17 named body pieces per pose, piece morphing and editing controls, icons, motif
transitions, browser playback recordings, and agent cursor studies. The
[pose plan](docs/pose-plan.md) distinguishes available artwork from future additions. Open
`/static/e-preview/index.html` with the local app running. The private hosted preview is linked in the project
conversation and optional board. The ordinary chat art
remains the earlier prototype while these proofs await review.

To try real project reads, set `BFI_PROJECT_ROOT=.` in `.env`, restart, and open
**Tools & setup**. The inspector works even in mock mode. A real compatible model
can use enabled tools when you opt in for a message. Optional web search requires
`BFI_BRAVE_API_KEY`. See [tools](docs/tools.md) and [local runtime integration,
including Strata research](docs/integrations.md).

| What you want to understand                | Where to start                                     |
| ------------------------------------------ | -------------------------------------------------- |
| What happens when you press Send           | [Learning walkthrough](docs/learning.md)           |
| Why these components were chosen           | [Architecture and decisions](docs/architecture.md) |
| Character name, description, and prompt    | [config/profiles.json](config/profiles.json)       |
| Endpoint, model, and context limits        | [.env.example](.env.example)                       |
| API routes and the request flow            | [bfi/main.py](bfi/main.py)                         |
| Real server requests and the mock          | [bfi/backends.py](bfi/backends.py)                 |
| SQLite tables and persistence              | [bfi/store.py](bfi/store.py)                       |
| Hardware checks and compatibility evidence | [Hardware notes](docs/hardware.md)                 |
| Larger ambition and next milestones        | [Project vision](docs/vision.md)                   |
| First controlled training experiment       | [Training plan](docs/training.md)                  |

## Verify it

```sh
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

The automated suite uses temporary databases and fake HTTP responses to test the API
contract, persistence, context selection, provenance, and failure handling. It does
not download or exercise a model. GitHub Actions runs these checks on Windows and
Linux. See [verification notes](docs/verification.md) for what was actually run here.

An optional [browser smoke script](scripts/browser_smoke.py) checks the UI using
temporary data and saves screenshots. Its extra dependencies are not needed to run
the app; installation and reproduction commands are in the verification notes.

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
Tool-enabled requests also send actual tool results to the selected model. Saved
provenance and exports may include project text and search queries. A configured
adapter label records intent; it does not train, load, or independently identify a LoRA.

One app process, one active model request sequence, and one local user are
intentional limits. Replies display as plain text. There is no authentication;
keep the app bound to `127.0.0.1`. This is not a shared or public deployment service.
The app does not start, load, or unload model servers. Stop the separate inference
process to release its model; merely closing this UI does not free VRAM.
Three profiles do not imply three simultaneously loaded models. The geometric
avatar can be mirrored in this app or shown by the optional native host. Its reply
cues produce no audio. Native Windows behavior remains unverified.

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
