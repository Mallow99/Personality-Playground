# Route to the first complete personality-training experiment

This is a plan, **not a working training pipeline**. No adapter is trained in
milestone 01. The first study should change personality through model weights,
remain small enough to debug, and compare against the exact unmodified starting
checkpoint. It need not target 27B immediately.

## 1. Choose the question together

Keep the question open until the owner can explain the alternatives. Possible narrow
questions include whether a LoRA makes a character more willing to offer justified
opinions, or produces a consistent expressive voice without reducing task accuracy.
These are candidates, not a preselected hypothesis. Choose one practical purpose,
one or two measurable traits, and a definition of unacceptable regressions.

Write an experiment record from [`research/experiment-template.md`](../research/experiment-template.md).
Register the question, scoring rubric, comparison conditions, and success threshold
before seeing the test results. A disappointing result is still useful evidence.

## 2. Pass hardware and serving gates first

- Choose an exact, licensed starting checkpoint and revision. A community fine-tune
  is valid; “unmodified” then means that checkpoint before our changes, not necessarily
  the original upstream base. Document its lineage.
- Prefer a small model, perhaps in the 1–4B range, for the first feasibility test.
  This is a planning range, not a guarantee of AMD or memory compatibility. Keep the
  eventual ~27B goal recorded rather than making it a prerequisite to learning.
- Check the official GPU/OS/training stack matrix and test actual tensor operations,
  then a tiny LoRA forward/backward/optimizer step. Record peak memory, stable loss,
  finite gradients, and deterministic seeds where supported. CUDA-only quantization
  recipes must not be assumed to work on AMD.
- Save and reload a tiny adapter. Establish a viable serving route with the selected
  architecture **before** producing a large dataset. Possible routes are serving the
  adapter in a compatible Transformers runtime, converting a supported adapter for
  llama.cpp, or merging into a compatible base then exporting/quantizing. Each route
  has architecture, format, memory, and licensing constraints.
- If the gate fails, record the error and reduce scope or investigate supported
  alternatives. Do not assume additional hardware, cloud training money, or funding.

## 3. Build a small, curated dataset

Use a few hundred carefully reviewed multi-turn examples as a starting pilot, with
actual size chosen for the question. Include normal assistance, disagreement,
uncertainty, correction, emotional tone, and staying useful under pressure. Include
neutral tasks to detect style overwhelming competence. Keep story spoilers out.

Record sources, rights, consent, deduplication, and review decisions. Synthetic
examples need human review; do not train on private conversations automatically.
Separate train, development, and held-out evaluation by scenario families before
training, so near-duplicates and paraphrases do not leak across splits. Hash and
version the files. Keep private raw data and generated artifacts outside Git.

## 4. Run and record LoRA training

Freeze the base weights and train low-rank adapter weights for selected layers. The
adapter is a learned weight change, unlike a system prompt. Low rank reduces the
number of trainable parameters, but does not eliminate base-model and activation costs.

The eventual script must consume a versioned config and record: base and tokenizer
revisions, dataset hashes, chat template, seed(s), layer targets, rank, alpha,
dropout, precision, optimizer, learning rate/schedule, batch and accumulation,
sequence length, epochs/steps, loss curves, checkpoint selection rule, package and
driver versions, and peak resource use. Save the adapter and config. Verify the
base checkpoint remains unchanged and that the adapter reloads separately.

We have not selected a training library, invented tested commands, or assumed a
Windows/ROCm recipe. Write and validate those scripts after the compatibility gate.

## 5. Compare fairly

At minimum, run the held-out scenarios with **the exact starting checkpoint, adapter
disabled**, and **the same checkpoint, adapter enabled**, keeping prompt, memory,
tools, chat template, context, and decoding settings identical. Use the same minimal
neutral prompt in both conditions to isolate the adapter's effect. A prompt-only
character condition can be a useful additional control, not a substitute for training.

Randomize and blind labels during scoring. Evaluate the chosen personality traits,
task correctness, grounded uncertainty, instruction-following, and unwanted behavior.
Use multiple generations or seeds where feasible and report variation, sample counts,
failures, and human rubric examples. An automated judge is optional and fallible;
document its identity and any cloud use. Do not infer broad personality change from
training loss, a few attractive replies, or one score.

## 6. Close the loop in the app

Serve the adapter, or the verified merged/exported artifact, through BFI's configured
endpoint. Confirm the server actually loaded it; an alias string alone is not proof.
Repeat the base/adapter comparison after conversion or quantization, since export can
change behavior. Record the served file hash, adapter identity, backend version,
quantization, and successful load evidence in the experiment record. Start separate
app conversations for each condition and export representative results.

A first complete experiment ends with a saved/reloadable learned artifact, repeatable
commands and dependencies, a base comparison, held-out results, a served-model check,
resource measurements, and an honest conclusion. We can then decide what was learned
and whether scaling up is worthwhile. Curated future training updates may develop
the character over time; every chat does not immediately modify weights.
