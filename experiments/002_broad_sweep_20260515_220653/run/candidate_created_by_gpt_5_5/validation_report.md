# Validation Report

Generated: 2026-05-16

## Package Summary

- Benchmark: Protocol Archaeology
- Private sample size: 30 items
- Solver-visible examples per item: 14
- Gold schema: exactly `id` and `answer`
- Prediction schema: exactly `id` and `answer`
- Scoring: deterministic exact match on 8 lowercase hex characters

## Required Command Checks

Generation completed successfully:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
```

Verifier passed:

```json
{"gold": 30, "items": 30, "status": "ok"}
```

Gold self-score passed:

```json
{"accuracy": 1.0, "correct": 30, "malformed_count": 0, "total": 30}
```

Weak shortcut baseline used the first observed example response for each item as
the query answer. It failed all items:

```json
{"accuracy": 0.0, "correct": 0, "malformed_count": 0, "total": 30}
```

## Leakage Inspection

Solver bundle files:

- `solver_bundle/README.md`
- `solver_bundle/SOLVER_MANIFEST.json`
- `solver_bundle/items_private_sample.jsonl`

The solver bundle intentionally mentions forbidden private files in its rules,
but does not include those files. A direct intersection check found zero overlap
between private gold answers and solver-visible example responses.

Private files outside the solver bundle:

- `generator.py`
- `verifier.py`
- `scorer.py`
- `gold_private_sample.jsonl`
- `private_audit_traces.jsonl`
- `validation_report.md`
- `failure_modes.md`
- `benchmark_spec.json`

## Acceptance Gate Status

- Validity: pass. The named construct is trace-grounded protocol reverse
  engineering, not generic model failure.
- Solvability: provisional. The task is intended for qualified engineers with
  scripting, but measured human baselines have not yet been collected.
- Grading: pass. Exact-match scorer is deterministic and reports malformed,
  missing, duplicate, and extra ids.
- Frontier resistance: provisional. The package includes a frontier pre-screen
  protocol, but no frontier solver run has been performed inside this artifact.
- Novelty and contamination: pass for MVP. Items are fresh synthetic byte traces
  generated locally from a seed, not drawn from public puzzle or coding corpora.
- Statistical readiness: partial. Item-level scoring is emitted, but solver
  pass rates and confidence intervals require future multi-solver runs.
- Cost: pass. The benchmark is small, local, and cheap to regenerate and score.
- Abuse and bias: pass. The task is synthetic protocol inference and does not
  rely on identity attributes or harmful operational content.

## Known Limitations

The generator family is public in this package, as required for reproducibility,
so real leaderboard runs should keep the generation seed, gold, and audit traces
private and give solvers only the isolated bundle. The current MVP has a human
baseline plan rather than measured human data.

