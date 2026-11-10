# Preserve the full idea

Best Friend Initiative aims to build local AI characters that are both useful and
recognizable. Voice, priorities, habits, opinions, and responses across situations
should eventually be shaped through training, with LoRA among the legitimate methods.
System prompts and application features are supporting layers, not a quiet change of goal.

## Character direction remains open

Two appealing directions are a helpful, opinionated, responsible character with a
somewhat serious Jarvis feel, and a helpful, sassy, expressive character with a more
cyberpunk identity. Neither is chosen yet. The initial “Companion” configuration and
green geometric artwork are provisional scaffolding, not a final character decision.
Avoid Cyberpunk and Capri story spoilers in character design, examples, and datasets.

Practical competence matters alongside personality. A character may specialize in a
particular purpose rather than improve every capability equally. Later characters
could have different specialties. A cohesive visual identity should use colors,
broad shapes, and meaningful interface modes rather than decorative complexity alone.

## Intended model setup, still provisional

1. A companion/research model around 27B, plus a smaller option when other programs
   need GPU resources.
2. A larger daily local model, potentially the user-mentioned **Qwen3.8-Flash-Next
   through Strata**, if exact identity, compatibility, memory needs, and measured
   responsiveness support it.
3. A frontier subscription for hard problems a local character can delegate through
   supported interfaces, with explicit usage and limits. Subscription access and API
   entitlements must be checked separately.

Community fine-tunes are legitimate starting points. **Humanlike Chat 2.0, Gemma
StyleTune, and Swift 1.5** are investigation leads, not verified artifact identities
or recommendations. Capture exact model-card links, revisions, base lineage,
licenses, templates, and adapter/export support before testing them.

## Surrounding software

Keep inference replaceable. Make memory persistent and inspectable, tools grounded
in actual results, cloud assistance visible, and every result traceable to its source.
Manage model loading and unloading so the system remains comfortable on an everyday
PC. Preserve reproducible training and evaluation against the unmodified starting
model. Google Calendar, with Canvas synced into it, is the school deadline source
of truth; an AI-generated date is not a replacement for that source.

Memory supports the trained personality. Long-term development may involve curated
training updates; individual conversations should not automatically edit weights.

## Incremental route

| Stage                                       | Useful result                                                 | Evidence before calling it complete                                             |
| ------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 01 — foundation                             | Chat, history, config, backend status                         | API and browser checks; explicit mock/local distinction                         |
| 02 — actual local inference                 | One model on the delivered PC; a smaller fallback             | Recorded versions, correct GPU use, latency, RAM/VRAM, repeatable launch        |
| 03 — first controlled training study        | Small personality adapter and honest before/after comparison  | Complete experiment record, holdout evaluation, served adapter, base comparison |
| 04 — inspectable memory and one useful tool | Correctable facts and a grounded narrow workflow              | Source records, deletion behavior, real tool failures, freshness                |
| 05 — supported frontier help and lifecycle  | Visible delegation limits and usable model switching          | Per-result provenance, usage accounting, measured release/reload behavior       |
| Later                                       | Voice, richer identity, more characters, larger training runs | Clear user benefit and measured hardware feasibility                            |

Stages can overlap when justified. Do not assume the purchased hardware is stable,
RAM upgrades are worthwhile, or school funding is available before checking.
