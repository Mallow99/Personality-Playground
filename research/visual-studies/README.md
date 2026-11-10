**Current status: v5 was rejected by the owner for a significant quality drop.
Visual work is paused. [Read the handoff](../../docs/HANDOFF.md) before continuing.
Earlier candidate/review statements below are historical and are not approval.**

Latest runtime work: [Business v5 candidate](poses-v5/README.md) uses a consistent
two-eye family and writing boards whose paper faces the character. The normal/dark
variants are implemented; aesthetic review remains open. The records below are
historical design studies. Current launch instructions are in docs/HANDOFF.md.

# Character design studies

Latest: [54 illustrated pose suggestions with reasons](pose-proposals/README.md).
The active library still has 74 traced poses; the 54 new concepts await review.
The owner rejected the first hand-built E poses and initial motif transitions.

**[Option E](option-e.png) is the selected visual baseline.** Build from E's character
identities, outfits, standing/seated poses, and distinct personalities. Earlier
options remain archived for comparison; the previous preference for D/A is superseded.
The owner subsequently authorized the [E proof pack](../../bfi/static/e-preview/README.md).
It supplies poses, icons, motif transitions, and cursors for the next visual review.

E’s original reference remains the generated sheet. New code-built SVG proofs
are available; they are not yet approved production artwork.
The app's runtime artwork has not been replaced. The older D-style SVG proofs show
that this general construction can work in code; they are not E's implementation.

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
| [A — Loose](option-a.png)                  | Long open shapes, airy poses                                                 | Earlier preference; E selected                                 |
| [B — Bold](option-b.png)                   | Wider shapes and proportions                                                 | Too close to A/C to count as a substantially different design  |
| [C — Sharp](option-c.png)                  | More diagonal wedges                                                         | Earlier preference, but D superseded it                        |
| [D — New silhouettes](option-d.png)        | Distinct hair, clothing shapes, posture, and expression                      | Earlier leader; superseded by E                                |
| [E — Different wardrobes](option-e.png)    | Cardigan/poncho academic, short-bob/cropped hacker, waistcoat business       | **Selected baseline**                                          |
| [F — Different construction](option-f.png) | Offset plates, hair ribbons, banner-like jacket panels, active/relaxed poses | Archived alternative; not selected                             |

The PNG sheets are generated concept references. Final production geometry and exact
colors will need their own review; they should not be treated as already rigged art.

## Proving the code route

The small [SVG feasibility studies](code-proof/) approximate D's standing silhouettes.
They use flat filled polygons grouped by logical part, without raster images,
scripts, shading, or outside assets. These are earlier D prototypes, not E assets.
Recreate E as its own shapes on resumption; do not silently substitute these proofs.

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

Open `index.html` directly from a local checkout, or serve the folder locally if
your browser blocks file URLs:

```sh
python -m http.server 8766 --bind 127.0.0.1 --directory research/visual-studies
```

Then open `http://127.0.0.1:8766`. The gallery uses local images and SVGs and makes no
external requests. Inspect a proof's `polygon points` and `data-piece`
groups to see what would move independently. The existing app, tools, model routing,
history, and personality-training goal are unchanged by this design-only checkpoint.

## Resume from E, after review

1. Recreate E's standing and seated shapes as separate SVG/polygon parts, preserving
   the chosen silhouettes and genders rather than redesigning them.
2. Check proportions, fingers/gestures, negative-space gaps, and distinct palettes
   at phone and desktop sizes. Confirm exact production swatches before rigging.
3. Decide whether separate simplified icons are useful; none is selected yet.
4. Resume the preserved motif animations after the static assets are reviewed.

Academic remains neutral: a loose parchment coat/cardigan, olive book/glasses, and
curious gestures. Hacker remains feminine: short asymmetric crimson bob, cropped
angular jacket/collar, crossed-arm stance and sideways seated pose. Business remains
masculine: navy waistcoat, icy sleeve pieces, blue tie, compact hair, and relaxed
standing/seated poses. This is a visual baseline; model assignments, names, voice,
and personality training are separate decisions.

## First E proof pack (rejected)

Open `/static/e-preview/index.html` with BFI running. The source includes twelve
pose SVGs, six face/motif icons, three motif transitions, speaking and appearance
controls, 39 exported cursor SVGs, and downloadable contact sheets. A 12-second
Academic GIF is a vector-frame export, not a browser recording. See the proof
pack README for component interfaces and the browser verification limitation.

The earlier pause/resume checklist above is historical context. This authorized
pass completed a proof; choosing final refinements and installing it in chat remain
separate from delivery of the demonstration.
