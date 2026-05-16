Done. I built a complete benchmark package in the artifact directory: **Protocol Archaeology**, a deterministic trace-inference benchmark where solvers infer byte-protocol responses from observed examples.

Verified:

- Generated 30 private sample items with the required command.
- `verifier.py` passes: `{"gold": 30, "items": 30, "status": "ok"}`
- Gold self-score is 30/30.
- Weak shortcut baseline scores 0/30.
- Solver bundle contains only:
  - `solver_bundle/README.md`
  - `solver_bundle/SOLVER_MANIFEST.json`
  - `solver_bundle/items_private_sample.jsonl`
- Checked that private gold answers do not appear in the solver bundle.

Main files are in place: `README.md`, `benchmark_spec.json`, `generator.py`, `verifier.py`, `scorer.py`, `gold_private_sample.jsonl`, `validation_report.md`, and `failure_modes.md`.