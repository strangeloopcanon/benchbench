Done. I built the benchmark package in the required directory.

Created **Prior Authorization Forensics (PAF) v1**: a deterministic cross-document claim-adjudication benchmark with 30 generated dossiers, closed JSON answers, verifier, scorer, solver bundle, validation report, and failure-mode notes.

Verification completed:

- Generated 30 items with the required command.
- `verifier.py`: `verified 30 items`
- Gold self-score: `30/30`
- Weak approve-zero baseline: `0/30`
- Weak deny-as-missing-auth baseline: `5/30`
- Leakage scan over `solver_bundle/`: no private filenames, seed, audit traces, scorer/generator/verifier references, or answer-key terms found.

Required files are present, including `README.md`, `benchmark_spec.json`, `generator.py`, `verifier.py`, `scorer.py`, `gold_private_sample.jsonl`, `validation_report.md`, `failure_modes.md`, and the isolated `solver_bundle/`.