# Validation report — PAL v1

## Result

The package contains a deterministic 30-item private sample. Every item has 10
requests, so the diagnostic score covers 300 decision-and-provenance outcomes.
The generator owns and recreates the entire public solver packet
(`SOLVER_MANIFEST.json`, `README.md`, and the item JSONL) as well as the
root-side gold JSONL. The generator deliberately selects, per item, four
decision flips, two same-decision provenance changes, two stable allows, and
two stable denials. This prevents a final-decision-only or all-deny heuristic
from appearing strong.

## Executed checks

| Check | Result |
|---|---|
| Generate 30 items with seed `20260516` into an empty output directory | Completed with the stdlib-only generator; it created gold plus exactly the solver manifest, README, and item JSONL. |
| Independent semantic verification | `OK: 30 items, 30 gold rows, semantic recomputation matched` |
| Regenerate the same empty output directory with the same seed and compare SHA-256 | Identical before/after: gold `4e0c402cc0e36d5b60074cf9121cb9483b36379a4d1e00007ba267a8432478e8`; items `8a3e89d1fdfe57cb263a9c928a4a06ea463c33a6dae8c14a96a7d9ea4d24d42b`; README `4a0698e697f3e51dbcc474abd67c89db0637564f2b0aa78ead2e1ae7e6aeba08`; manifest `330685cc4851d3d2165e248dbcf069ab15a98e84100c90b95eebc756f44b0425`. |
| Gold self-score | `30/30` strict; `300/300` query-provenance components. See `score_report.json`. |
| Obvious weak shortcut | All `D@DEFAULT>D@DEFAULT`: `0/30` strict; `58/300` components (19.33%). See `weak_baseline_score_report.json`. |
| Solver-bundle leakage scan | It contains exactly the manifest, public README, and item JSONL. A scan found no gold filename, generator/verifier/scorer code, seed, validation report, or private-solution phrase. |

The verifier intentionally has a separate compact evaluator; it does not import
the generator's semantic functions. It structurally checks IDs, patch targets,
and query ordering, then recomputes every gold answer from the visible policy
data.

### Execution-target note

The documented `python3` commands were executed with the available
`/opt/homebrew/bin/python3` (CPython 3.14.6). The package uses only the Python
standard library and no version-specific features; its root scripts implement
the documented command lines and arguments verbatim.

## Solvability and identifiability

PAL is externally solvable without any private information. The solver packet
states the full operational semantics: closed time intervals, device matching,
the transitive direction of group links, scope/tree meaning, tag conditions,
the exact precedence tuple, default behavior, and ordered patch behavior. Each
item publicly supplies every membership, link, resource parent/tag, rule,
patch, and query needed by that semantics.

A qualified human can audit a query by (1) deriving usable effective groups,
(2) crossing out nonmatching rules, (3) ranking the remaining rules by the
shown tuple, then (4) repeating after the visible edits. A qualified external
solver can equivalently implement those four operations in a short script.
The answer's rule ID makes every final result inspectable against the item;
there is no latent convention, hidden seed, oracle call, or open problem.

## Difficulty rationale and scope

The benchmark is deliberately not intended to block an exact implementation;
tool access should enable a careful solver to build one. Its challenge is
whether the solver faithfully translates all supplied semantics and preserves
provenance across a non-monotonic second world. The sample has 25 resources,
52 time/device-gated memberships, 18 transitive group links, 66 ordered rules,
15 ordered changes, and ten contextual requests per item. Common partial
implementations fail on a directionally reversed link, an inclusive endpoint,
a tag patch, an inactive record, tie order, or a winning-rule change that does
not change allow/deny.

PAL is closest to program/configuration reasoning and agent reliability rather
than an existing access-control QA set. Fresh procedural instances and the
two-world exact-provenance score make it a distinct measurement from code
completion, web/API execution, or ordinary factual/cybersecurity questions.
