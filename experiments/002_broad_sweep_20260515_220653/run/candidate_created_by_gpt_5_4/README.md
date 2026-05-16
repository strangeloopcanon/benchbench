# Spectrum Assembly with Side Constraints

This package benchmarks whether a solver can reconstruct a unique hidden string from an executable set of overlapping local observations plus global side constraints.

Each item gives:
- a shuffled multiset of every contiguous 4-gram from the hidden string
- exact symbol counts over a fixed alphabet
- a short list of forbidden trigrams
- optional anchor multiset clues over selected positions

The solver must return the one full string that satisfies all visible constraints.

Why this benchmark is interesting:
- It is exact-synthesis rather than multiple choice.
- It rewards building the right search procedure, not pattern-matching a known exam domain.
- It is human-auditable because every answer can be checked directly against visible constraints.
- It is deterministic: exact-match scoring on the reconstructed string.

What it is closest to:
- It is closest to executable reasoning benchmarks such as SWE-bench and LiveCodeBench in spirit because success comes from constructing the right algorithmic procedure under a precise contract.
- It is also adjacent to logic-puzzle and formal-reasoning tasks, but it is not a duplicate of MMLU-style or GPQA-style question answering because the object of work is a constrained reconstruction problem with an exact checker.

Why it is not merely a duplicate:
- The core object is a side-constrained spectrum-assembly problem, not factual recall, code repair, or standard contest math.
- The item structure is generated, uniqueness-checked, and graded by an explicit reference search.
- The visible 4-gram spectrum intentionally creates locally plausible but globally misleading continuations, so shallow stitching heuristics fail.

## Files

- `benchmark_spec.json`: benchmark definition and intended use.
- `generator.py`: deterministic item generation CLI.
- `verifier.py`: uniqueness and gold-consistency verifier.
- `scorer.py`: exact-match scorer.
- `gold_private_sample.jsonl`: private answers for the generated sample.
- `solver_bundle/`: isolated solver-visible bundle.
- `validation_report.md`: package validation evidence.
- `failure_modes.md`: known risks and likely solver mistakes.

## CLI

Generate:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
```

Verify:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
```

Score:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```
