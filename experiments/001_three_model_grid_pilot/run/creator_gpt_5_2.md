Built a new 30-item raster-only benchmark, **Folded Strip Order (FSO) v1**, in this directory.

- Generates folded-strip PNG items + solver bundle via `generator.py`, with exact-match answers (label permutation from START→END) in `gold_private_sample.jsonl`.
- Enforced strict contracts and no-leak solver bundle with `verifier.py`; scoring via `scorer.py`.
- Validated end-to-end: generator + verifier OK; gold self-score `30/30`; weak random baseline `0/30`; leakage scan passed. See `validation_report.md`.