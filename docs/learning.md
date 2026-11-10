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

## Read the character artwork as code

The chosen [E sheet](../research/visual-studies/option-e.png) is a PNG: a grid of
colored pixels. It records the design, but cannot expose an arm or book as a separate
movable piece. The [selection record](../research/visual-studies/baseline.json) names
the chosen sheet, role identities, and constraints; the app does not load this record.

Open an [earlier D SVG proof](../research/visual-studies/code-proof/academic-d.svg)
in a text editor. Each `polygon` has `points` listing its corners and a `fill` color.
The `g` elements group related shapes; `data-piece` labels parts that future code
could move together. These are inspectable building blocks, not a completed animation
rig. E now has its own editable proof geometry and presentation components; see the [design brief](../research/visual-studies/README.md).

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


## Trace the new E proof

The rejected first proof is archived at
`research/visual-studies/rejected-e-proof/academic-standing.svg`. Its hand-written
polygon illustrates the format, but does not implement the chosen art faithfully:

```xml
<g data-piece="legs">
  <polygon points="151,335 184,349 179,408 155,466 166,566 139,568 125,461 148,398"
           fill="#58402B" />
</g>
```

Each x/y pair is a corner in a 400-by-600 drawing space. The browser connects those
corners and fills the shape. `data-piece` gives related shapes an inspectable name.
The gaps between pieces are transparent space, not extra white shapes.

In the first proof (now archived), `CharacterActor.setPose` fetched a bundled SVG, cloned it,
and replaced the visible art. A generation number stopped an older fetch from winning
if you select another character quickly. Short opacity/position animations smoothed
the pose swap. The named-piece replacement is explained below.
`setSpeaking` now toggles presentation gestures. `show`/`hide` control appearance independently.

Then follow a profile button in `studio.js`: it changes theme tokens, chooses art,
and starts the book/error-window/clipboard transition. `AgentCursor.update` takes
coordinates for the pointer's hotspot and draws an input-transparent illustration.
No mouse clicks or operating-system commands are executed.

`node scripts/export_e_art.mjs` regenerates the cursor files and review sheets from
the component/source SVGs. `node scripts/check_e_preview.mjs` exercises cancellation,
late-response ordering, asset references, and cursor coordinates without a browser.
The optional motion exporter creates a GIF directly from SVG frames; it is not a
recording of a model or computer agent. See the [proof README](../bfi/static/e-preview/README.md)
for the exact verification limits and how to open the live controls.

## Why the first conversion failed, and how to check the replacement

The first SVGs were independently drawn interpretations. Their proportions and
negative-space shapes drifted from E. Passing XML, palette, and code tests did not
prove that the drawings matched the chosen art. The owner rejected that result.

The replacement starts with generated pose references, then traces the actual
boundaries. Read `scripts/trace_e_poses.py`: it classifies pixels into the three
character colors plus empty space, collects exposed pixel edges, walks closed
contours, and writes compound SVG paths. No redraw or hidden raster is substituted.
The source sheets, crop bounds, and hashes make the conversion reproducible.

This produces faithful but dense paths. Simplifying them or dividing a head, arm,
and book into rigged parts must preserve their contours and be checked again.
Overlap/color scores compare rendered SVGs to the normalized reference at source
resolution. They cannot grade good posing or similarity to E. Use the live source
comparison instead of accepting a passing test as a verdict on the artwork.

## A hand that stays the same hand

The new rig uses names such as `left-hand`, `left-forearm`, and `prop-main` in every
pose. Read a guide in `config/rigs`: `leftWrist: [330, 160]` is a point in that pose's
source cell. Head bounds and prop polygons help separate a face from a nearby hand
or a book from the fingers holding it. Frame matrices account for a figure spilling
outside its generated cell. The original image remains intact.

`build_e_rigs.py` assigns regions to those guides and intersects them with the
existing vector contours. The pieces reconstruct the accepted drawing. Guide
ownership is estimated: a bad wrist point can assign some sleeve to the hand even
when the assembled picture looks right. Inspect outlines and correct the guide.

`rig-actor.js` matches the same named part and color in two poses, samples outline
points, aligns their order, and interpolates coordinates. Missing pieces can shrink
or appear. This is geometric interpolation, not physics, motion capture, or model
reasoning. Intermediate shapes can deliberately look mechanical. At the end, the
complete target paths replace the temporary sampled outlines. Independent drift
adds small movements to individual SVG groups; Motion off/reduced motion stops it.

Select a hand in the studio, move it, then change poses. Its stable name makes the
relationship inspectable in both the DOM and exported piece map. Preview offsets
are separate from the saved artwork. The [pose plan](pose-plan.md) records what
exists, what is proposed, and which application states can reuse a drawing.

For overlapping fingers, joint proximity is only a first estimate. Selected poses
now add `ownershipRegions`: a polygon and allowed palette indices for each hand.
The builder disables that hand's automatic region, then assigns only the specified
pixels to it. This prevents a hand from taking some sleeve or book with it. Reading,
coding, and formal-report poses are the first manually bounded examples; other
poses still use draft joint estimates. Their assembled art remains unchanged.

You can rebuild just those examples instead of the entire library:

```sh
uv run --with numpy --with cairosvg --with shapely python scripts/build_e_rigs.py academic/reading engineering/coding business/formal-report
```

The builder updates those exports and their existing report rows while retaining
all other poses. Omitting selections rebuilds the complete library.

## Preserve a geometric form before assigning anatomy

The owner pointed out why the region method still felt wrong: it could cut a single
intentional sleeve or leg into several arbitrary fragments. Academic standing/seated
now use a whole-shape proof. `componentAssignments` assigns complete connected color
forms to meaningful groups, preserving their contours. A hand comb shape stays whole;
a long continuous leg stays whole. Major forms were assigned explicitly. Tiny texture
fragments still use an estimated owner, so this is not a finished authoring rig.

Each visible form has a pose-local `data-shape` ID, inside a stable `data-part` body
group. Dragging a group moves its shapes together; single-form dragging moves just
one shape. Do not assume that `c0-3` means the same shape in a different source pose.
The body group supplies the cross-pose identity. Flat generated pictures do not
contain hidden hand layers: genuinely joined shapes require an authored joint if
we decide to separate them. Other poses are still labeled as legacy region maps.

`turnPair` separates a contour's center from its local coordinates and estimates
its rotation toward the target. That lets the form turn during its journey instead
of only stretching corners along straight lines. Remaining contour differences still
interpolate; this is not skeletal animation. Use the three transition modes to judge
what feels appropriate before expanding the rig.

Talking is a visible state: voice marks, small gestures, and a readable indicator.
It is deliberately independent of future audio. Audio amplitude, word timing, or
mouth shapes would require a separate input and alignment design.

The pose checklist uses stable review codes and local browser storage. All 54 ideas
start unreviewed; exporting decisions is explicit. The exported file can later inform
which art to generate, without silently turning suggestions into approvals.

## An image for every proposal, without changing the rigs

The owner explicitly requested generation of all 54 suggested poses for review.
Nine six-cell sheets provide one image per proposal. Shared ideas rotate the
character used to demonstrate them, rather than creating three copies of every idea.
The original PNGs stay intact. `images.json` assigns the row/column, source hash,
and demonstrating role to each review code. The browser clips the corresponding
cell with CSS; the zoom dialog uses the same mapping. This changes presentation,
not the source artwork or the 74 active vector poses.

`config/pose-review-reasons.json` explains why each pose is useful. The plan builder
joins those reasons and image references to the existing codes. Saved review choices
stay separate from generated metadata, and exported decisions identify the exact
sheet/cell/hash. Generating an illustration does not mean it was approved or rigged.
