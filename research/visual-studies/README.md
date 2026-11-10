# Character design studies

These are **unselected reference studies**, not final character assets. Animation
implementation is paused while the character language is refined. The app has not
been updated with these proposed designs. The owner prefers **D**, followed by **A**;
E and F are newer alternatives awaiting feedback. A–C were too similar to each other.

## Keep this brief intact

- Suggest an anime-ish character using a small number of loose, separated, angular
  2D shapes. The gaps and silhouette matter. Head, torso, limbs, and hand gestures
  should read clearly without reconstructing realistic human anatomy.
- Avoid rounded face mascots and detailed, shaded, low-poly people. No skin shading,
  clothing seams, elaborate fingers/boots, gradients, or decorative clutter.
- Roughly three flat colors per character. Each role has its **own** palette,
  including its dark and light tones; no shared black/white character fills.
- Hacker presents feminine; business presents masculine; academic may be neutral.
- Full character pose references and optional simplified icon/identity cards are
  separate deliverables. The earlier icon studies are **not confirmed**.
- Explore meaningful alternatives: silhouette, hair, expression, outfit, shape
  construction, and gestures, not just scale or proportions.
- Every selected design must be reconstructible in code as a manageable set of
  polygon pieces, with poses and animation considered later.
- User-supplied Capri artwork and the owner's sketch guide the shape language.
  Do not research or introduce Cyberpunk/Capri story spoilers. Uploaded reference
  images are not copied into this repository.

## Reference sheets

Open [the local gallery](index.html), or the individual images:

| Sheet                                      | What it explores                                                             | Feedback / state                                               |
| ------------------------------------------ | ---------------------------------------------------------------------------- | -------------------------------------------------------------- |
| [Initial icons](icon-study.png)            | Heads and a few identity objects                                             | A substantial improvement; possible icon use only, unconfirmed |
| [First poses](first-pose-study.png)        | Standing and seated bodies built from loose shapes                           | Much closer; shared colors still needed correction             |
| [A — Loose](option-a.png)                  | Long open shapes, airy poses                                                 | Second preference                                              |
| [B — Bold](option-b.png)                   | Wider shapes and proportions                                                 | Too close to A/C to count as a substantially different design  |
| [C — Sharp](option-c.png)                  | More diagonal wedges                                                         | Earlier preference, but D superseded it                        |
| [D — New silhouettes](option-d.png)        | Distinct hair, clothing shapes, posture, and expression                      | Current leading reference, not a final selection               |
| [E — Different wardrobes](option-e.png)    | Cardigan/poncho academic, short-bob/cropped hacker, waistcoat business       | New alternative; awaiting feedback                             |
| [F — Different construction](option-f.png) | Offset plates, hair ribbons, banner-like jacket panels, active/relaxed poses | New alternative; awaiting feedback                             |

The PNG sheets are generated concept references. Final production geometry and exact
colors will need their own review; they should not be treated as already rigged art.

## Proving the code route

The small [SVG feasibility studies](code-proof/) approximate D's standing silhouettes.
They use flat filled polygons grouped by logical part, without raster images,
scripts, shading, or outside assets. These are prototypes rather than final traces.

| Character | Dark               | Accent            | Light               |
| --------- | ------------------ | ----------------- | ------------------- |
| Academic  | Oak `#58402B`      | Olive `#87A452`   | Parchment `#EBD8AF` |
| Hacker    | Charcoal `#20171E` | Crimson `#D9254C` | Rose `#F6A0B4`      |
| Business  | Navy `#153B64`     | Blue `#247DD4`    | Ice `#B9E9FA`       |

These three SVG palettes have no shared fill values. F also explores revised color
families; those changes are not selected. Do not silently adopt F's palette.

## Entrance animation brief — paused

Entrance motion is about the role's **objects and motifs**, not assembling the
character itself:

- Academic: books thrown into the air and green glasses; smoothly transition the
  workspace toward oak with green highlights.
- Cybersecurity: red/black error prompts converge into eyes, wink, and close;
  transition to black with red highlights.
- Business: a blue clipboard crosses the screen with white spreadsheet papers
  flying away; transition toward the business palette. Reconcile the paper tone
  with the newer no-overlap palette requirement when production colors are chosen.

Keep motion short, skippable, and compatible with reduced motion. It must not claim
that a model has loaded. The earlier prototype is saved privately in ignored
`data/paused-visual-prototype/`, including an `implementation.patch`, so it can be
revisited after a visual direction is chosen. It is not shipped in this commit.

## Reopen and reproduce

Open `index.html` directly from a local checkout; it uses local images and SVGs and
makes no external requests. Inspect a proof's `polygon points` and `data-piece`
groups to see what would move independently. The existing app, tools, model routing,
history, and personality-training goal are unchanged by this design-only checkpoint.
