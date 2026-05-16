# Validation Report

Generated on 2026-05-16 for the fixed private sample command.

## Commands Run

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions weak_baseline_predictions.jsonl --out weak_baseline_score_report.json
```

## Results

- Generated 30 solver items and 30 gold rows.
- Verifier result: `VERIFIED 30 items`.
- Gold-as-prediction scorer result: `SCORED 30/30`.
- Weak constant baseline (`KKKK`) result: `SCORED 0/30`.
- Image audit: 30 PNG files, each `520x520` RGB.

## Leakage Check

The solver bundle contains only:

- `SOLVER_MANIFEST.json`
- `items_private_sample.jsonl`
- `solver_packet.md`
- `images/swt_001.png` through `images/swt_030.png`

Searches for hidden-solution terms found no gold, seed, trace, layer-order, coordinate, source-vector, or solution-label leakage in solver-visible content. The only matched string was the required public item filename `items_private_sample.jsonl` inside the manifest.

## Human Auditability

Each strip has visible letter labels near both ends. Each probe ring is placed directly on a crossing, and the answer is determined by the strip that visibly occludes the other at the ring center. Printed number chips are documented decoys and are not used by the scorer.
