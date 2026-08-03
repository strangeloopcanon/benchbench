# CFPS validation report

## Result

The package generated, structurally validated, and semantically verified a 30-item private sample.  CFPS is a deterministic exact-optimization benchmark: every item has 18 public permissions, six public service requirements, and eight public attack requirements.  The gold answer for each item is a canonical minimum-cost revocation tuple.

## Executed checks

All successful local checks used the workspace's available `python3` (Python 3.14.6); the implementation uses only standard-library features compatible with Python 3.12.  The exact mandated Python 3.12 executable was invoked once but could not start in this environment because its dynamic loader reported that its own `libpython3.12.dylib` path was sandbox-blocked.  This was an environment loader failure before benchmark code ran, not a package error.

| Check | Command / result |
|---|---|
| Generate | `python3 generator.py --sample-count 30 --seed 20260516 --out-dir .` completed in 0.45 s. |
| Item/gold counts | `wc -l` reported 30 rows in each JSONL file. |
| Structural + semantic validation | `python3 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl` returned `{"ok": true, "items": 30, "semantic_gold_checked": 30}`. |
| Independent verifier check | The verifier has its own evaluator and branch-and-bound search; it does not import generator code or use generation-only planted data. A full check completed in 0.77 s. |
| Compilation | `python3 -m py_compile generator.py verifier.py scorer.py` passed. |
| Gold self-score | Scoring `gold_private_sample.jsonl` as predictions yielded 30/30, accuracy 1.0 in `score_report_gold_self.json`. |
| Weak baseline | `predictions.jsonl` predicts `NONE` for every ID; exact scoring yielded 0/30, accuracy 0.0 in `score_report.json`. |

The requested execution-target command is retained verbatim in [README.md](README.md) and `benchmark_spec.json`:

```sh
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .
```

## Determinism

The generator was run twice with the required arguments.  SHA-256 values were identical before and after regeneration:

| File | SHA-256 |
|---|---|
| `gold_private_sample.jsonl` | `147edfafa58336da7870e332c0ec2e17be8f51207a35b721d66a9afe56859c7c` |
| `solver_bundle/items_private_sample.jsonl` | `35f23d62040f0820ae86fea4f495267bdd72dc9fa16405fe24b20069acab47eb` |
| `solver_bundle/SOLVER_MANIFEST.json` | `0253bacdee0e29a2a8df456e7721b406fb7e0f1bc439b7d66979c995549d75b9` |
| `solver_bundle/README.md` | `f725178fe55c49374c5a93295acd77b65a018a37c1f475f29fb571ecf8970a55` |

`generator.py` creates `solver_bundle/`, its manifest, its instructions, the 30 item rows, and the root gold JSONL without relying on preexisting generated output.

## Solvability and identifiability

An external solver receives every permission name and cost and every recipe in every channel.  The packet defines exactly when a recipe, channel, service, and attack is active.  Thus for any candidate revocation set, its feasibility and objective tuple are mechanically decidable from public data.  There are only 2^18 finite candidate sets.  A qualified specialist can enumerate them, or encode the same Boolean rules in SAT/MaxSAT/ILP; comparing `(total cost, cardinality, sorted-name tuple)` identifies a unique required answer.  No generator seed, private provenance, human judgment, network query, cryptographic secret, or unresolved research result is required.

The independent verifier provides concrete evidence: it reconstructs recipe bitmasks from only the item JSON, searches the public finite space, and agrees exactly with all 30 private-gold rows.

## Solver-bundle leakage audit

`solver_bundle/` contains exactly three files: `SOLVER_MANIFEST.json`, `README.md`, and `items_private_sample.jsonl`.  A content scan for `gold`, `seed`, `planted`, `generator.py`, `verifier.py`, `scorer.py`, and `answer key` returned no matches.  The public item rows contain no `answer` field and no private asset reference.  Gold rows, generator/verifier/scorer code, score reports, and this validation report are all outside the isolated bundle.

## Scope and novelty

CFPS is closest to program-reasoning and constraint-optimization tasks, but differs from generic code completion and standard single-constraint logic puzzles by requiring exact synthesis across asymmetric layered policy semantics: preserve every service channel while interrupting any one required channel per attack, under coupled costs and canonical tie-breaking.  The weak all-`NONE` shortcut fails on every item; the remaining intended route is faithful executable modeling rather than answer recall.
