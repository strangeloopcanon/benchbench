Built a complete benchmark package here around a new task family: reconstructing a unique hidden string from a shuffled multiset of overlapping 4-grams plus global side constraints. The package is deterministic, exactly graded, and solver-auditable.

Current state:
- `generator.py` produces 30 private-sample items and matching gold under the required CLI.
- `verifier.py` confirms all 30 items are uniquely solvable and that the gold answers satisfy the visible constraints.
- `scorer.py` exact-matches `id` and `answer` under the required contract.
- `README.md`, `benchmark_spec.json`, `validation_report.md`, and `failure_modes.md` are all in place.
- The isolated `solver_bundle/` contains only solver-visible material and no leaked answers.

What I verified:
- Required file contract: passed.
- `verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`: 30/30 items passed, each with a unique solution.
- Gold self-score: 30/30, accuracy `1.0`.
- Weak shortcut baseline: 0/30, accuracy `0.0`.
- Leakage check: no gold answer string appears verbatim in the solver bundle.

The main package files are [README.md](/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_4/README.md), [benchmark_spec.json](/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_4/benchmark_spec.json), [generator.py](/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_4/generator.py), [verifier.py](/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_4/verifier.py), [scorer.py](/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_4/scorer.py), and [validation_report.md](/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_4/validation_report.md).

Remaining constraint: this package argues human solvability and benchmark novelty well, but it does not yet include a measured human baseline or live frontier-model run.