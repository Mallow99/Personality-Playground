# Preserve the full idea

Best Friend Initiative aims to build local AI characters that are both useful and
recognizable. Voice, priorities, habits, opinions, and responses across situations
should eventually be shaped through training, with LoRA among the legitimate methods.
System prompts and application features are supporting layers, not a quiet change of goal.

## Character direction remains open

Two appealing directions are a helpful, opinionated, responsible character with a
somewhat serious Jarvis feel, and a helpful, sassy, expressive character with a more
cyberpunk identity. Neither is chosen as the final character. The owner's later
direction develops this into three specialists (Academic, Hacker, and Business), with
draft personalities recorded in [character-directions.md](character-directions.md) and
[personality-drafts.md](personality-drafts.md). Those are discussion drafts. The app
itself still ships one provisional “Companion” configuration, which is scaffolding,
not a character decision.
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

## Route

The ordered milestones, the evidence each needs, and the decisions still open are in
the [roadmap](roadmap.md). Work that is ready to start is in the [task cards](tasks.md).
Do not assume the purchased hardware is stable, RAM upgrades are worthwhile, or school
funding is available before checking.
