# IgnoreSense (BenchBench candidate)

IgnoreSense is a self-contained benchmark for **spec-implementation correctness**: given a `.gitignore`-like rules file and a set of query paths, determine which paths are ignored under a precise, documented subset of gitignore semantics.

This is intended to be:

- **Human-auditable**: each item shows the full `.gitignore` text and query paths.
- **Reliably graded**: deterministic exact-match grading against a reference implementation.
- **Hard in a “real engineering” way**: the ruleset has precedence and edge cases (negation, anchoring, escaping, directory-only patterns, `**`), so naive solutions fail.

## What it measures

Ability to correctly implement and apply a tricky real-world pattern language under a tight spec, including:

- precedence / last-match-wins
- negation (`!`)
- basename-vs-path matching (patterns with and without `/`)
- directory-only patterns (`.../`)
- escaping of leading `#` and `!`
- glob semantics (`*`, `?`, `**`, character classes)

## Closest existing benchmarks (and why this isn’t a duplicate)

Closest adjacent benchmarks are code/execution ones like **LiveCodeBench** / **SWE-bench** (adjacent construct: implement and debug real software behavior), but IgnoreSense is not a general coding benchmark:

- it targets a specific, commonly misimplemented ruleset (`.gitignore`)
- it is fully self-contained with a deterministic gold grader (no external repos, no tests to “overfit”)

## Files

- `benchmark_spec.json`: benchmark description and contract
- `generator.py`: creates `solver_bundle/items_private_sample.jsonl` and `gold_private_sample.jsonl`
- `verifier.py`: checks that items deterministically reproduce gold under the reference matcher
- `scorer.py`: exact-match scorer for solver predictions
- `solver_bundle/`: the isolated packet visible to solvers

## CLI contract (required)

Generate a 30-item private sample:

`/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .`

Verify gold consistency:

`/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`

Score solver predictions:

`/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

