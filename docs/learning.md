# Make this project yours

The goal is not just a companion application. It is knowledge you can compound:
understanding a system, changing it deliberately, and explaining what evidence says
it works. AI can handle much of the coding. Ownership comes from being able to
inspect, reproduce, question, and improve the result.

When continuing this project, preserve that approach: explain consequential choices
in plain language, show the relevant code, and separate implemented behavior from
assumptions. Do not turn this into homework before every useful change, but do not
let the owner accumulate code they cannot discuss. Keep this guide and the decision
record in `architecture.md` updated when the design changes.

## Start with the path of one message

Open these files in order. Searching for the named functions is enough; you do not
need to read every line first.

1. **`bfi/static/index.html`** — find `chat-form` and `message`. HTML defines the
   visible controls. It does not run the model.
2. **`bfi/static/app.js`** — find `addEventListener("submit"` and `api`. JavaScript
   captures the draft and makes an HTTP request. `fetch` asks the Python server for
   a result; `await` lets it wait without freezing the page.
3. **`bfi/main.py`** — find `MessageInput`, the `send` route, and `context_for`.
   FastAPI maps the URL to a Python function. Pydantic rejects malformed input.
   Context assembly chooses which saved messages the model will actually see.
4. **`bfi/backends.py`** — compare `MockBackend.complete` and
   `OpenAIBackend.complete`. One builds fixed text. The other asks another program
   for a model response. Their common interface lets the application replace one
   without rewriting the route.
5. **`bfi/store.py`** — find `append_exchange`. SQL inserts the two messages and
   updates the session title. A transaction makes those changes a single unit.
6. **Back to `app.js`** — find `render`. Returned content goes through `textContent`,
   which treats even HTML-looking model output as text. Source details are created
   from the saved provenance, not invented by the character.

An API is an agreement about requests and responses. A backend is the implementation
behind that agreement. The frontend is the part you interact with. None of these
terms implies a model is present; that is why mock labeling matters.

## Inspect an actual exchange

1. Run the app in mock mode and open your browser's developer tools (**F12**, then
   **Network**). Send “Hello foundation”. Look for the POST ending in `/messages`.
2. Inspect its request JSON: `content` contains “Hello foundation”; `project_tools`
   and `web_search` show the permissions for this message. Inspect the response:
   a conversation containing user and assistant messages, plus provenance.
3. Expand **inspect source** under the reply. Explain why `mock-script-v1` is not
   evidence that a local model ran.
4. Reload the page. The transcript persists because it is in SQLite; localStorage
   only remembers which conversation was selected.
5. Click **Export JSON**. Open the file and locate the character prompt, message text,
   and backend identity. Keep private conversation exports out of Git.

## Trace the second increment when you are ready

- Change a selected profile in `config/profiles.json`; trace how the new-conversation
  route snapshots it and how `renderCharacter` applies its theme. This changes a
  prompt and presentation, not trained weights.
- Find `Settings.for_profile` in `config.py` to see where a character's model alias
  and endpoint come from. Compare these with its stored conversation identity.
- Run **Tools & setup** with a configured project root. Follow `/api/tools/inspect`
  to `ToolRunner.run` and its path checks. The text you see is read from a real file.
- Read `OpenAIBackend.complete_with_tools` to understand the model → tool request →
  real tool result → model reply sequence, and inspect it in the new automated tests.
- Compare `characters.css` with `concepts.js`. CSS defines appearance/motion, while
  JavaScript chooses the profile and pose. Neither file trains or loads a model.

These are things to inspect on the PC later, not prerequisites for making requests now.

The machine-readable API reference is at `http://127.0.0.1:8000/openapi.json`. It
describes route names, expected inputs, and response schemas. The app avoids loading
an interactive documentation page from a third-party CDN so mock mode stays offline.

## Small changes you can explain

These are optional experiments, not a prerequisite to continuing development.

| Try                                                                        | Observe                                                               | Explain in your own words                             |
| -------------------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------- |
| Change a name in `config/profiles.json`, restart, start a new conversation | New chat shows the name; old chat retains its snapshot                | Why saving a snapshot matters                         |
| Change `.empty-state h2` in `style.css`, then reload                       | The welcome heading changes                                           | What CSS controls and what it cannot change           |
| Set a real backend with no server listening                                | A clear error appears; your draft stays; no mock reply is substituted | How connection failure differs from model refusal     |
| Run `uv run --locked pytest -q`                                            | Tests use temporary data and fake HTTP responses                      | What a passing test establishes, and what it does not |
| Read the context-window test, then temporarily set `BFI_HISTORY_PAIRS=1`   | Earlier exchanges stay stored but get omitted from future context     | Why persistence and model memory are different        |

Before changing code, use `git diff` to see your current work. Afterward, use it again
to explain the exact change. Once committed, `git log --oneline` and `git show` make
each change inspectable. Revert your experiment before moving on if you do not want
to keep it.

## Questions you should eventually be able to answer

- Where does a message go after I press Send? Which process actually generates text?
- What is in the database, and what subset is sent to the model?
- Why does a prompt edit not constitute a weight update?
- What does the backend status prove? What evidence would establish actual inference?
- Why can a model ID in a reply be useful without proving exactly which weights ran?
- How would I reproduce a training comparison and notice a capability regression?

Not knowing these yet is fine. Keep the questions visible and answer them as the
relevant work becomes concrete. Choose the research question after you understand
the tradeoffs, not because the first implementation happened to suggest one.
