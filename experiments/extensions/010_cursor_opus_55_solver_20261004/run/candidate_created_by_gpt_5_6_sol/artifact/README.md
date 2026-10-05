# AuditWeave

AuditWeave measures whether a solver can reconstruct a corrupted event in a
partially ordered log from lossy checkpoint audits, then execute a
counterfactual query on every feasible reconstruction. It targets a useful
hybrid capability: exact specification following, causal-order search,
abductive consistency, state deduplication, and post-reconstruction reasoning.

The 30-case sample is deterministic and exactly graded. Every case contains
all state-machine rules and evidence needed by an external solver. Generation
rejects any case whose public evidence permits more than one requested answer;
the verifier independently re-enumerates all legal candidates and phase orders.

## Required commands

From this directory:

```sh
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

The generator recreates the gold JSONL and complete solver bundle without
consulting generated artifacts. `gold_private_sample.jsonl` rows have exactly
`id` and `answer`. Prediction rows must have the same exact two-key schema.
Missing predictions count wrong; unknown or duplicate ids are rejected.

## Solver isolation

Give a solver only `solver_bundle/`. The bundle contains a manifest, the item
JSONL, and `solver_packet.md`. It intentionally contains no generator,
verifier, scorer, seed, gold, validation report, traces, or labels.

## Novelty

The closest broad family is formal multi-step reasoning such as MuSR and
algorithmic BIG-Bench Hard tasks. AuditWeave is not a narrative QA duplicate:
its core is abductive recovery of a disputed operation jointly with legal
linearizations, checked by several deliberately lossy audit projections, then
a counterfactual replay. Unlike SWE-bench or LiveCodeBench, it asks for no code
or patch and has a finite exhaustively auditable semantic answer. Fresh seeded
instances also reduce direct answer memorization.

## Files

- `benchmark_spec.json`: machine-readable capability and grading declaration.
- `generator.py`, `auditweave_core.py`: deterministic instance creation and semantics.
- `verifier.py`: schema, DAG, public identifiability, and gold validation.
- `scorer.py`: strict exact-match scorer.
- `solver_bundle/`: isolated public solver material.
- `validation_report.md`: empirical and design validation.
- `failure_modes.md`: limitations and anticipated shortcuts.
