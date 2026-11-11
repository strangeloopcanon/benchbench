# Counterfactual Firewall Policy Synthesis (CFPS)

CFPS measures whether a solver can translate compact, compositional access-policy semantics into a correct discrete optimization model.  Each instance asks for the least-cost set of permissions to revoke that preserves a set of legitimate services while blocking every listed multi-channel attack.  Answers are exact canonical policies, not free-form security advice.

The public solver packet is [solver_bundle/README.md](solver_bundle/README.md).  Generate the fixed 30-item private sample from this directory with:

```sh
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .
```

Then validate it with:

```sh
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
```

Score candidate JSONL predictions with:

```sh
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

The `gold_private_sample.jsonl` is deliberately outside the solver bundle.  Every public item contains 18 permissions and two kinds of monotone Boolean objects: a service needs every channel open; an attack is stopped by closing any one required channel.  Minimum cost, then cardinality, then lexicographic tie-breaking removes judgment calls.

## Positioning

CFPS is closest to constraint-satisfaction/program-reasoning portions of BIG-bench and to small operations-research tasks in coding benchmarks.  It is not a duplicate: the task combines asymmetric AND/OR policy semantics, safety constraints, cost optimization, and a canonical exact policy output in independently generated finite instances.  It tests faithful executable modeling of an operational policy language rather than factual recall, ordinary code completion, or a textbook one-line graph problem.

## Package layout

- `generator.py`: deterministic instance and gold generator using only Python's standard library.
- `solver_bundle/`: the only material available to a solver.
- `verifier.py`: validates public structure and independently recomputes each gold optimum.
- `scorer.py`: exact-match scorer with the required schema-v2 report.
- `validation_report.md`: generation, validation, baseline, solvability, and leakage evidence.
- `failure_modes.md`: intended challenge boundaries and known misuse cases.
