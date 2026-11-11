# AuditWeave validation report

Validation date: 2026-08-01 (America/Los_Angeles)

## Outcome

The package generated 30 deterministic items, and all 30 passed structural,
semantic, and public-identifiability verification. Exact gold self-scoring was
30/30. An obvious shortcut baseline scored 0/30.

## Generation and reproducibility

Starting from an empty artifact directory, generation with sample count 30 and
seed 20260516 accepted 30 cases in 32 attempts. Re-running generation with the
same parameters produced byte-identical required artifacts:

| artifact | SHA-256 |
|---|---|
| `gold_private_sample.jsonl` | `77ca5128d140007059ea9ddbc2f112c6f40b4c640eacb57a2e907c7ad4af8b7f` |
| `solver_bundle/items_private_sample.jsonl` | `94b1ad6cef4ff5fb4d986d6a1d304f6241d80823d6a8826f6c61f4e8581bf9d5` |
| `solver_bundle/SOLVER_MANIFEST.json` | `c88c7c78a650f1b252de5c7914a48500a899e25ab58037870828bedaee2b6baa` |
| `solver_bundle/solver_packet.md` | `fa29b8d8a2c4c2b61b4768b5e7df98e9a2d9e3357737be1d3d7b5fc55374912e` |

The first generation did not depend on a pre-existing gold file or solver
bundle. `generator.py` reconstructs both and copies the solver instructions
from the source template, not from a stale generated bundle.

## Semantic and identifiability verification

The verifier loaded only the published items plus candidate gold, validated
the exact schemas, checked every precedence graph for acyclicity, enumerated
all legal topological orders, replayed all four candidate operations, filtered
at every checkpoint audit, applied query operations, and compared the sole
derived answer with gold.

Observed verifier summary:

```json
{"status":"ok","items":30,"unique_answers":30,"total_reconstruction_witnesses":6990,"witnesses_per_item_min":5,"witnesses_per_item_max":1440,"legal_orders_per_phase_min":1,"legal_orders_per_phase_max":120}
```

The 6,990 witnesses are distinct audit-consistent execution paths. Thus the
check does not merely recover one planted hidden order: some cases allow many
histories, but every surviving history agrees on the required label and
post-query state. This is the benchmark's stated equivalence criterion.

Sample construction statistics:

- 18 logged events per item in three six-event phases, plus one four-way
  disputed record;
- 4 to 6 counterfactual operations per item (mean 4.97);
- 3 to 11 explicit precedence edges per phase (mean 7.2);
- all eight operation types occur repeatedly in the published sample;
- correct candidate labels are distributed A=9, B=3, C=10, D=8.

## External solvability and identifiability argument

The isolated bundle is sufficient for a qualified external solver. For every
case it publishes the complete initial state, all known operations, all four
candidate operations, every precedence edge, all checkpoint audit formulas
and observed values, all counterfactual query operations, and the canonical
answer format. `solver_packet.md` gives exact atomic transition semantics,
modulo conventions, simultaneous-update behavior, audit equations, phase
boundaries, and a complete enumeration algorithm. There is no appeal to a
seed, generator choice, private ordering, or domain convention.

An external solver can determine the answer by evidence visible in the bundle:
enumerate the four labels and each phase's DAG linearizations (at most 120 in
this sample), replay from surviving full states, retain states whose published
audit projections match, then run the published query list. A human specialist
can audit the same computation with a spreadsheet or a short script. The
verifier demonstrates that this public procedure yields one answer for each
item. The hidden gold is therefore a convenience for grading, not a private
key needed to solve the task.

## Scoring checks

The scorer enforces exactly two string fields (`id`, `answer`), rejects
duplicate and unknown ids, treats missing ids as wrong, and reports the
required schema-v2 totals.

Gold self-score (`gold_score_report.json`):

```json
{"schema_version":2,"total":30,"correct":30,"accuracy":1.0,"missing":0}
```

Weak shortcut baseline (`predictions.jsonl`, `score_report.json`): choose
candidate A, replay events in their JSON array order, ignore audits and
precedence, then apply the query. Result:

```json
{"schema_version":2,"total":30,"correct":0,"accuracy":0.0,"missing":0}
```

This baseline attacks both obvious positional shortcuts. It is not evidence
of calibrated frontier-model difficulty; a future pilot should measure that
separately and add results to the shared model score matrix.

## Solver-bundle leakage inspection

The bundle contains exactly three files: manifest, item JSONL, and solver
packet. Recursive searches found none of the private seed, gold filename,
generation audit name, planted-label variable names, private-solution terms,
or any complete gold answer string. The manifest exposes item count and answer
schema only. Sequential ids contain no answer signal. Generator, verifier,
scorer, weak baseline, private generation audit, hashes, and reports remain
outside the bundle.

## Runtime environment note

All functional checks passed with the available system Python 3.14.6. The
requested pinned Python 3.12 command was also invoked verbatim, but this hosted
shell denied access to its runtime before Python started:
`dyld: Library not loaded ... libpython3.12.dylib (blocked by sandbox)`.
Direct `ls` of that interpreter path likewise returned `Operation not
permitted`. The scripts use only the Python standard library and Python-3.12-
compatible syntax; the failure occurred in the host loader, before benchmark
argument parsing or imports.

## Residual limitations

The benchmark is synthetic and has not yet received human timing or a
multi-model difficulty calibration. Exact match gives no partial credit.
Fresh releases should keep seed metadata private from solvers and should record
release hashes to prevent accidental cross-release comparisons.
