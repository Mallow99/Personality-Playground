# Experiment record

Status: proposed / feasibility / running / evaluated / inconclusive

## Question and decision criteria (complete before running)

- Practical purpose and personality trait(s):
- Research question / hypothesis (owner-selected):
- Trait rubric, task-quality rubric, unacceptable regressions:
- Predeclared success threshold and what would count as inconclusive:

## Reproduction

- Date, experiment ID, code commit, exact commands:
- Hardware, OS, driver, training and inference stack versions:
- Starting checkpoint ID, revision, lineage, tokenizer, template, license:
- Dataset sources, rights, consent, hashes, split procedure and scenario families:
- LoRA targets, rank, alpha, dropout, precision, optimizer, schedule:
- Seed(s), batch/accumulation, sequence length, steps, checkpoint-selection rule:
- Adapter path/hash, unchanged base hash, dependencies/config paths:
- Peak RAM/VRAM, training time, logs, errors and unresolved limits:

## Comparison

- Base vs adapter vs optional prompt-only conditions:
- Identical prompts, context/memory, tools, decoding settings:
- Held-out prompt IDs, blinded order, raters, rubric:
- Samples/seeds per scenario, scores, variation, failures and examples:
- Judge model/version and cloud usage, if any:

## Serving and conclusion

- Save/reload check and proof adapter was loaded:
- Conversion/merge/quantization steps, versions, hashes and comparison after export:
- BFI configuration, separate conversation exports, backend identity:
- What changed in behavior? What did not? What regressed?
- What evidence supports the conclusion? What remains unknown?
- What can the owner explain and reproduce? Next question:
