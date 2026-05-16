# Folded Strip Order (FSO) v1

This BenchBench candidate is a **raster-only perceptual topology** benchmark.

## Task
Each item is a single PNG image showing one folded paper strip with:
- a **START** marker (green ring),
- an **END** marker (red ring),
- several **labeled visible segments** (letters in white rounded boxes).

Your job is to infer the **true order** of the labeled segments encountered when traversing the strip from START to END.

## Answer format
For each item, output a single string containing the labels in order, with **no separators** (e.g. `ABCDE`).

## Why this stays hard
The visually obvious shortcut (2D left-to-right order, or nearest-neighbor continuity in the image plane) is intentionally unreliable because the strip folds back on itself, crosses, and is partially occluded. The intended cue is continuity of the strip's texture at segment boundaries.

## Reproducible CLI contract
Generate:
`/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .`

Verify contracts and leakage constraints:
`/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`

Score:
`/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

