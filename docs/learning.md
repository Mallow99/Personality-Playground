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
3. **`bfi/workspace.py`**, then **`bfi/jobs.py`** — find `JobInput`, `submit`, and
   `run`. FastAPI validates the request and returns a durable job ID. The queue
   waits for the single generation resource; reloading the page can reconnect.
   In **`bfi/main.py`**, `generate` and `context_for` assemble the model's context.
   The old synchronous `send` route remains available for earlier clients.
4. **`bfi/backends.py`** — compare `MockBackend.complete` and
   `OpenAIBackend.complete` and `complete_stream`. One builds fixed text. The others ask another program
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

## Limited movement inside one authored pose

The reading example preserves the complete seated drawing. `build_limited_motion.py`
puts intact source contours into a fixed body, head, book, and two hand groups.
Each visible hand is one connected source shape. No new anatomy or full-body rig
is inferred. At rest this regrouping retains over 99.99% silhouette overlap with
the original SVG, which remains available as the still comparison.

`limited-motion.js` animates only four transforms: a small head rotation, a shared
book/hand shift, and a tiny local rotation of each hand. The hands inherit the book
movement before adding their grip adjustment. The torso, sleeves, and crossed legs
stay fixed. A timeline and strength control make the motion inspectable; the
close-up uses the same SVG with a tighter viewport. Reduced motion disables autoplay.
This is a pose-specific animation study, not the deferred universal rig project.

## From a visual study to a handler-controlled companion

The artwork is now useful without solving universal rigging. The catalog pairs a
stable pose ID with a local SVG or transparent PNG. The 54 new images are cropped
from their recorded cells, with label strips and near-white background removed;
the original RGB art and full source sheets remain. This is a reproducible paper-cut
packaging step, not another model-generated redraw.

Follow a request in `bfi/main.py`: the existing generation lock starts a thinking
cue, builds only the enabled tools, and wraps the runner with `AvatarTools` when
avatar tools are enabled. That wrapper knows the request's character. Catalog search
returns a few candidates; `avatar_set` validates the chosen ID and updates `AvatarHub`.
The model does not send CSS or arbitrary image URLs. Final reply text starts a timed
text cue. Tool names, arguments and actual results remain in saved provenance.

Then read `avatar/avatar.js`: both the handler and separate overlay poll the same
revisioned state. They render plain text captions and bundled artwork. Reading uses
small local transforms; other poses remain whole. Colors follow the active character.
The static hosted demo reuses the renderer with local scripted state, while the real
local app uses API state. This distinction prevents a pretty preview from being
mistaken for a running model or desktop-control system.

Finally, `bfi/desktop.py` is an optional native host around that browser surface.
It requests an always-on-top transparent window and can pass mouse input through
using a tray toggle. Its dependency is separate from ordinary chat. The wrapper is
provided for PC testing, not claimed as verified Windows behavior. See
[the handoff](HANDOFF.md) and [runtime guide](avatar-runtime.md) for exact commands,
state limits, evidence and next checks.

## Why a plausible assembled image was not enough

I grouped only the visible pixels of each object. That left the hand's footprint
missing from the book or thigh behind it. A silhouette test at rest could pass while
moving the front part revealed a hole. The repair adds explicit rear material and
checks it with the front hands hidden. Rear page reconstruction changes some small
negative-space edges; that is an intentional geometry repair, not an exact tracing
claim. The source image stays available for comparison.

Business seated now has a restored rear thigh and one local hand rotation. Reading
has rear pages beneath both hands. Other poses remain static whole sprites; the
application does not animate their rough experimental anatomical cuts. The old lab
is archived rather than presented as the finished entry point. The full catalog is
checked for image decoding, in addition to handler/overlay behavior and approval data.

## Fixing white edges, work-directed eyes, and apparently inactive controls

The pale fringe had two different causes. CSS applied a pale `drop-shadow` around
all artwork, including every transparent gap. The new PNGs also still contained
white blended into the edge RGB. Lowering their alpha did not remove that white;
it merely made the white edge translucent. Both were visible on dark backgrounds.

`avatar_matte.py` estimates how much of a known character color was mixed with
white in the source. The relationship is `source = alpha × foreground +
(1 − alpha) × white`. The export reverses that mixture before storing transparent
RGBA. Opaque interiors stay opaque; faint paper texture becomes fully transparent.
The original sheets remain unchanged. A synthetic check starts with known colors
and known coverage, composites them on white, and checks their recovery. Inspect
exports on both light and dark backgrounds, not only the source's white page.

The eye correction is deliberately local. `config/avatar-focus.json` records eye
apertures and pupil polygons for fifteen work poses. `build_avatar_focus.py`
keeps the head/body contours and glasses, fills the old pupil area, then clips a
new pupil toward the book, keyboard, panel or report. Reading's eye group lives
inside its moving head. A rendered comparison checks that no pixels outside the
head changed. Other poses retain their original authored gaze; this is not
automatic eye tracking or a full-library face rig.

The Hide button exposed a testing mistake. Its HTML `hidden` property changed,
but `.avatar-view { display: flex }` overrode the browser's default hiding rule.
The old test checked the property, so it passed while the character stayed on
screen. An explicit `.avatar-view[hidden] { display: none !important }` fixes the
rendered result. Browser checks now ask whether it is actually visible.

A second bug involved asynchronous loading: repeated state updates while the same
SVG was loading returned early. The newest render could hide the reveal control,
then never revisit it when the SVG arrived. The renderer now returns the same
pending loading promise to those callers. The regression test deliberately holds
the SVG request, changes the controls, then releases it and checks readiness.

The preview now changes the actual thinking pose, reports every action visibly,
provides an Idle state and contrasting background choices, and shows layer reveal
only on supported drawings. It identifies still poses honestly and offers a moving
example where one exists. Reply marks remain a silent text cue, not audio.

## An image loading successfully is not a visual review

The missed Hacker flirty correction was present in its reference, not introduced
by SVG tracing. Faithfully tracing a defective drawing preserved the defect. The
fix required a new reference with both arms clear, then the same trace/comparison
pipeline. `pose_sources` in the source manifest overrides just this cell; `--only`
rebuilds its stable role/pose ID. Other art and the old sheet are retained.

The full review used twelve larger contact pages covering all 128 runtime sprites.
It also found a neighboring figure leaking into Hacker tired and small caption
scraps beneath multiple figures. Runtime clean copies remove detached baseline
scraps; a separate explicit rule removes that known neighboring fragment. This is
not anatomical slicing, a limb redraw, or inferred hidden geometry. The final
contact pages were inspected again to check the feet and limbs stayed intact.
`render_avatar_contact_pages.py` reproduces the pages. The web review page shows the
same runtime assets beside source views, and records specific repairs by pose ID.

Six newer task poses use local eye overlays over embedded transparent cutouts;
nine older poses use vector eye edits. Their bodies remain authored images or
traces. Work-directed gaze is pose-specific; other poses retain their source gaze.

## Design v5: objects have a front, a back and a purpose

The earlier pass removed edge artifacts but missed a more basic design error:
Business appeared to write on a clipboard whose paper faced the camera. Opaque
paper alone would not fix that. The writing task needs the paper facing him, with
the board's plain rear face toward us. The regenerated standing and seated writing
references now use that arrangement. The pen nib and paper are on the far side;
the supporting fingers wrap around the near edge. A complete navy backing polygon
sits beneath the gripping fingers so their contours cannot punch holes in it.
Presentation boards remain separate poses that can legitimately face the viewer.

The original Business head often had one long eye slit. Moving its pupil preserved
that ambiguity. V5 uses one reference family with two separated eyes for front,
three-quarter and downward looks. Most existing body poses keep their authored
silhouettes; resting poses retain closed eyelids. Forehead-hand poses have explicit
local eye edits to preserve the overlapping hand. Head coordinates use the source
manifest's cell-to-canvas transform: failing to apply it briefly produced two heads
in the reclining proof, which the contact-page inspection caught before publishing.
The two regenerated writing poses are full authored endpoints, not head swaps.

True-alpha references are classified into the three role colors while retaining
foreground coverage, including pale fingers. They do not use white as a fourth
background class. White-looking details inside an object can be solid material.
That distinction matters: treating every pale patch as background made clipboard
cells into holes. Display sheets now have explicit opaque paper planes; writing
clipboards instead have plain opaque rear planes. The reference/crop definitions
and all source files remain available under poses-v5 and avatar-design-v5.json.

Dark backgrounds exposed another limitation: a navy or charcoal silhouette can be
correctly cut out and still disappear on black. Dark variants raise each role's
own tones instead of adding a pale contour glow. There are 128 normal/dark pairs.
Auto chooses from the visible app surface; the owner can choose Light or Dark
explicitly for an unknown transparent desktop background. Model tools cannot
change that owner preference. Three-color families remain separate between roles.

Finally, motion reset must remove only runtime motion transforms. Removing every
SVG transform would also remove a head's authored placement. The renderer now
resets only its known moving groups; browser checks preserve the seated head's
placement when motion is paused and resumed.

This is a design candidate. Numeric checks establish material opacity, contrast,
asset loading and control behavior; they do not establish the owner's aesthetic
approval or a universal body rig.

## Paused after the v5 quality regression

The owner rejected the latest version as a significant quality drop across the
board and requested a new-chat handoff. No single cause has been established.
The brighter palettes and shared two-eye heads were proposed fixes, not accepted
character-design decisions. They should not become requirements by repetition.

The failure highlights a limit of the review method: a complete material plane,
correct prop orientation, readable contrast and working controls can coexist with
worse artwork. Quantizing every PNG color and fitting a shared head into draft
guide bounds can preserve mechanical invariants while changing expression,
proportions and character identity. These are hypotheses to compare against the
source and earlier checkpoints, not a diagnosis proved by the tests.

The current state is preserved for comparison. No further art, rollback or preview
deployment was made for this handoff. `docs/HANDOFF.md` records the owner's actual
requirements, known checkpoints, likely investigation points and useful functional
fixes that should not be discarded blindly.

## Why the handler has a queue and a separate knowledge store

A model response may take much longer than a page request. `bfi/jobs.py` gives it a
persistent identity before work starts. The browser can ask for that job after a
reload, display provisional text, or cancel it. A semaphore allows one generation
sequence at a time. Cancellation interrupts an `await`; `finally` releases local
resources. The app cannot promise that an external server stops GPU work merely
because its HTTP client disconnected.

The stream is a preview until the model protocol finishes successfully.
`OpenAIBackend.complete_stream` reads actual SSE frames; it rejects malformed or
incomplete streams. `generate` saves a user/assistant pair only after completion.
That is why a cancelled reply may have appeared on screen without becoming part
of the saved conversation. On a handler restart, queued/running jobs become
interrupted. Replaying automatically would be dangerous once tools have effects,
so retry remains a deliberate new submission.

Conversation history and memory solve different problems. History preserves what
was said in one conversation. `bfi/knowledge.py` stores an explicitly saved fact,
preference, experience or decision with a source and a scope. A correction creates
a new revision and removes the old one from active search. Forget deletes that
memory family, but earlier conversations, tool traces and exports are separate
records. Nothing in this mechanism changes model weights.

SQLite FTS5 is a lexical search engine: it matches words in the saved text. It is
small and inspectable but does not infer semantic similarity like an embedding
model. The first retrieval combines matches with a few recent saved records,
subject to a character budget. Profile checks happen in Python/SQL, so a model
cannot obtain another profile's memory by choosing a tool argument. Context uses
these records as referenced user data, not new system instructions.

The same store indexes full research reports in overlapping sections. Search
results point to the saved report, source and review date. Reading a tool's manual
establishes documented support; it does not show the tool running on your PC.
The research library therefore stays broader than the installed handler. Read
`docs/handler.md` when ready to connect a real runtime and measure what it does.

## What memory sleep can and cannot learn

This increment reuses LangMem rather than inventing a consolidation model.
`langmem_review` in `bfi/memory_sleep.py` creates its typed memory manager and points
it at the configured local endpoint. `ReviewBatch` describes what the model may
suggest. The library returns those suggestions; application code decides how they
can change SQLite. That boundary keeps a model-generated sentence from becoming an
unexamined replacement for an owner fact.

Three operations deserve different treatment. Two identical records can be merged
without guessing their meaning. A paraphrase may contain a date or qualifier that
must survive compression. A contradiction does not identify which version is true.
Exact duplicate changes are reversible; semantic changes wait in the review page.
A pending conflict adds a warning to retrieved evidence, rather than silently giving
the character one chosen answer. Alternate keywords improve lexical recall, while
importance controls which general records remain available in a limited context.

The original and resulting records are linked. Applying checks that the source
snapshot still matches current data, which prevents a delayed model response from
overwriting a newer owner correction. Undo is similarly conditional. Forget follows
correction/consolidation links and purges related review drafts, so the audit log
cannot resurrect that memory. Old exported files and conversation text remain
separate records. Export includes the local review history and source links.

Sleep is an ordinary background task, not a second GPU. It uses the same generation
lock as chat. A new chat cancels the review and takes priority. An idle timer delays
work and limits how often it runs; it cannot run while the application is closed.
The browser tests call the real library through a simulated HTTP server. This proves
the wiring and lifecycle behavior, not whether a real model consolidates well.

## A personality editor is a configuration layer

`bfi/personality.py` provides typed fields for tone, traits, values, interests,
relationship and speaking style, initiative, humor and boundaries. Optional fictional
backstory and custom notes remain editable. The starting values simply make each
character ready for the later personality discussion.

Saving writes a revision rather than overwriting history. Preview shows the compiled
prompt that will be sent to the model; restoring old settings makes another revision.
A new conversation snapshots the active settings. An old conversation retains its
old prompt, so later configuration does not rewrite what that conversation meant.
This makes experiments explainable: compare which revision changed the behavior.
None of this updates model weights. The separate personality-training experiment
remains necessary to test whether a learned adapter can carry the desired traits.
