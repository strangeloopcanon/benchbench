# Shadow Weave Topology

Shadow Weave Topology is a 30-item raster benchmark for perceptual layer reasoning. Each item shows six labeled paper strips crossing under local shadows and occlusions. Four probe rings mark contact points. The solver must answer with the label of the visibly top strip at probes A-D.

The benchmark is designed to punish cheap shortcuts. Strip color, screen position, printed number chips, and endpoint order are all decoys; the answer is determined only by local occlusion topology at the probe centers.

## Required Commands

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

Gold and prediction rows contain exactly `id` and `answer`. Solver item image paths are relative to `solver_bundle`.
