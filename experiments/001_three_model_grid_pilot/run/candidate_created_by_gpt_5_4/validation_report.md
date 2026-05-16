# Validation Report

## Scope

This package was generated in-place with:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
```

The generator produced:

- `gold_private_sample.jsonl`
- `solver_bundle/items_private_sample.jsonl`
- `solver_bundle/SOLVER_MANIFEST.json`
- `solver_bundle/images/item_000.ppm` through `solver_bundle/images/item_029.ppm`

## Contract validation

Verifier command:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
```

Observed result:

```text
Verification passed for 30 items.
```

Checks performed by `verifier.py`:

- every gold row contains exactly `id` and `answer`
- every item row contains exactly `id`, `image`, and `prompt`
- item ids and gold ids match exactly
- image paths are relative to `solver_bundle`
- referenced images exist inside `solver_bundle`

## Scoring validation

Gold-on-gold scorer command:

```bash
cp gold_private_sample.jsonl predictions.jsonl
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

Observed result:

```text
Scored 30/30 correct.
```

This confirms the scorer reaches perfect accuracy when predictions exactly match the gold file.

## Weak baseline

Weak baseline used: constant prediction `C` for every item.

Scorer command:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions_weak_constant_c.jsonl --out weak_score_report.json
```

Observed result:

```text
Scored 9/30 correct.
```

Baseline accuracy: `0.30`

Gold answer distribution in the 30-item sample:

- `A`: 8
- `B`: 6
- `C`: 9
- `D`: 7

## Leakage inspection

Public bundle file inventory:

- `solver_bundle/items_private_sample.jsonl`
- `solver_bundle/SOLVER_MANIFEST.json`
- `solver_bundle/README.md`
- `solver_bundle/images/*.ppm`

Leakage sweep performed with a keyword search for answers, seeds, and private implementation references. No gold rows, hidden coordinates, source geometry, generator code, verifier code, scorer code, or actual solution labels were found in solver inputs.

The only keyword hits in the solver bundle were benign schema text:

- the manifest's prohibited-content description
- the README output-format example

## Notes

- The `/Users/rohit/.pyenv/shims isn't writable` warning appeared before Python runs in this environment, but all commands completed successfully.
- The benchmark is deterministic for the required invocation because item construction is seeded from the provided seed and item index.
