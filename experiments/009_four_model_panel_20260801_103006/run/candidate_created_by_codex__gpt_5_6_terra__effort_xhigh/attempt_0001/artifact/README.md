# Patchwork Access Logic (PAL) v1

PAL evaluates whether a solver can execute an explicitly supplied
counterfactual access-policy semantics with exact provenance. Each item supplies
a base policy, an ordered patch list, and ten requests. The solver must give
the winning decision and winning rule for every request both before and after
the patch.

The intended capability is reliable formal-semantic execution under
non-monotonic changes: hierarchical resource scope, time/device gates,
transitive group membership, rule precedence, and a patch can all alter an
outcome indirectly. It is deliberately hostile to surface heuristics: a stable
allow can have a changed source, and apparent denials can be overturned by a
later/deeper/higher-priority match.

The solver-facing rules and all evidence are in
[`solver_bundle/README.md`](solver_bundle/README.md). Generate the supplied
sample with:

```sh
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .
```

Then validate and score:

```sh
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

Primary score is exact item accuracy (0–30); the scorer also reports a
per-query provenance diagnostic (0–300). Gold and solver rows each contain
exactly `id` and `answer`.

PAL is closest to configuration/program reasoning and tool-agent reliability
evaluations, but is not a duplicate of coding completion or API agent tests.
It uses fresh, generated formal-policy instances and scores counterfactual
winning-rule provenance, not merely a final authorization bit.
