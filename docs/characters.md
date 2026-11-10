# Characters, models, and personality training

The application now has three **working, selectable profiles** in
`config/profiles.json`. Each has a separate prompt, visual theme, and conversation
snapshot. They can use different local endpoints and model aliases. The names and
voices are provisional; they do not settle the research question or prove trained
personality.

| Profile     | Useful starting purpose                                            | Provisional voice                                | Implemented appearance                     |
| ----------- | ------------------------------------------------------------------ | ------------------------------------------------ | ------------------------------------------ |
| Academic    | Explain a concept, support study/research, make a manageable plan  | Warm, patient, curious; opinionated with reasons | Brown/green, rounded body, glasses         |
| Engineering | Code, debugging, tests, technical and authorized security learning | Direct, precise, expressive; light dry humor     | Black/red, angular body, sharper eyes      |
| Business    | Planning, research, analysis, drafting, decisions                  | Composed, practical, decisive                    | White/grey/blue, structured body and frame |

Choose a profile using the selector in the chat sidebar. Switching starts a fresh
conversation rather than inserting another character into an existing transcript.
Reopening a conversation restores its original character and appearance. A changed
model/backend/adapter label requires a new conversation; existing histories remain
readable. Older foundation conversations retain the original draft character.

## The pieces are separate

```text
Character profile
  ├── Name, provisional personality prompt, specialty
  ├── Visual theme, shape, poses
  ├── Backend endpoint + model alias
  ├── Optional adapter label (a declaration, not a loading command)
  └── Explicit tool permissions for the current message
```

The **base model** generates text. A **personality LoRA** is a learned set of weight
changes for a particular compatible base. A **software backend adapter** is Python
code that talks to a server. A **visual skin** changes the interface. Those uses of
“adapter” must not get confused. None of the three profiles has a trained LoRA yet.

## One, two, or three?

The code provides three candidates so you can compare them. That does not commit
the project to operating all three. Start with one useful vertical slice and expand
when it earns its place. BFI serializes generation; it does **not** automatically
load or unload external model processes or guarantee that only one model occupies
VRAM. Manage loading in the loader until lifecycle integration is verified.

Two eventual arrangements are valid:

- A shared compatible base with separate personality LoRAs. This can reduce duplicate
  weight storage, but adapter switching and compatibility must be demonstrated.
- Different bases for specialties when measured usefulness justifies the disk,
  loading time, training complexity, and evaluation cost.

## Flash Next or ~27B: do not assign by costume

Use a ~27B companion candidate for a role only if it performs the relevant tasks and
has a viable training/export/serving route. A smaller compatible model is the first
training feasibility target. Qwen3.8-Flash-Next through Strata is an inference
candidate for whichever tasks justify it; its documented low-RAM path does not prove
comfortable performance on this PC or a suitable personality-training route.

Suggested comparison tasks, with the same evidence and scoring standard:

| Role        | Representative test                                                                         |
| ----------- | ------------------------------------------------------------------------------------------- |
| Academic    | Explain an unfamiliar idea, identify uncertainty, and make a realistic study step           |
| Engineering | Explain a small codebase, suggest a reviewable change, and correctly interpret test results |
| Business    | Compare options using supplied evidence, state assumptions, and recommend an action         |

Record quality, personality consistency, factual grounding, latency, RAM/VRAM, and
adapter feasibility separately. Keep the final mapping open until those observations
exist. Compare the unmodified starting checkpoint against the learned adapter using
the [training plan](training.md), not merely different prompts.

## Motion that exists now

The chat app and `/concepts` studio have original geometric artwork, a layered
entrance, blinking, attentive/thinking/speaking/docked poses, motion-off controls,
and reduced-motion support. The optional in-app corner character shows a short
extract of the actual last assistant reply. Its “speaking” motion is visual; no
audio or speech synthesis is implemented. The studio's sample line is explicitly
scripted. Character changes animate presentation, never assert model readiness.

The corner character belongs to the browser window. A true Windows desktop overlay,
window-edge seating, click-through behavior, multi-monitor handling, background
presence, and opt-in proactive appearances remain future work. Model-requested
attention and computer control are different permissions; neither is enabled by an
avatar animation.
