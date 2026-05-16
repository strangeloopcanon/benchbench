# Validation report — Folded Strip Order (FSO) v1

Date: 2026-05-16 (America/Los_Angeles)

## What was validated
- The generator deterministically produces 30 items and writes all required artifacts.
- The strict IO contracts hold:
  - gold JSONL rows contain **exactly** `id` and `answer`
  - items JSONL rows contain **no** `answer`
  - solver bundle paths are **relative** and exist on disk
- The scorer performs **exact-match** scoring.
- The solver bundle contains **no gold leakage** (no gold files, no generator/verifier/scorer, no hidden labels).

## Commands run
Generate:
`/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .`

Verify:
`/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`

Gold self-score (sanity):
`/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions_gold.jsonl --out score_report_gold.json`

Weak baseline (random label permutations):
`/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions_weak.jsonl --out score_report_weak.json`

## Results
- Verifier: **OK** (30 items; ids match; contracts satisfied; files exist)
- Gold self-score: **30/30** exact match (accuracy 1.000)
- Weak baseline: **0/30** exact match (accuracy 0.000)

## Leakage check (solver_bundle)
- No `.py` files present.
- No gold files present.
- No filenames containing `gold`, `seed`, or `answer` (except `SOLVER_MANIFEST.json` and `README.md`, which only describe schemas).

