# Validation Report

Date: 2026-05-15  
Directory: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_4`

## What was validated

1. The required package files exist.
2. `generator.py` emits 30 solver-visible items and 30 gold answers under the required CLI.
3. Every generated item has exactly one solution under the reference search, capped and checked by `verifier.py`.
4. The gold file self-scores to 30/30 under `scorer.py`.
5. An obvious shortcut baseline fails badly.
6. The solver bundle does not contain raw gold answers.

## Commands run

Generation:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
```

Verification:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
```

Gold self-score:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

Weak baseline score:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions baseline_predictions.jsonl --out baseline_score_report.json
```

## Results

- Verifier result: 30/30 items passed; each item had exactly one discovered solution.
- Gold self-score: 30/30, accuracy `1.0`.
- Weak baseline: 0/30, accuracy `0.0`.
- Leakage check: no gold answer string appeared verbatim inside `solver_bundle/items_private_sample.jsonl`.
- Solver-bundle shape: contains only `SOLVER_MANIFEST.json`, `README.md`, and `items_private_sample.jsonl`.

## Notes on difficulty

- The first draft of the generator produced items that a greedy 4-gram stitcher could solve too often.
- The final generator rejects those items and only keeps instances where the exact solver succeeds but that shortcut fails.
- This does not prove frontier resistance, but it does show the package is testing more than trivial local assembly.

## Remaining limitations

1. No empirical human baseline has been measured yet.
2. No live frontier-model evaluation has been run from this package alone.
3. The benchmark currently uses one procedural family rather than a mixed family portfolio.
