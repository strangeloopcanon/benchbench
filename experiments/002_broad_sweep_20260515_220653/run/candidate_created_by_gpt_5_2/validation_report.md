# Validation report (IgnoreSense v1.0.0)

Date: 2026-05-15 (America/Los_Angeles)

## Completion checklist

- Generated 30 private sample items (seed `20260516`).
- Verified solver-visible items reproduce gold under the reference matcher.
- Ran gold self-score (perfect accuracy).
- Ran a weak/obvious-shortcut baseline (low accuracy).
- Inspected solver bundle for leakage (no gold, no generator/verifier/scorer code).

## Determinism and grading

The benchmark is deterministically graded:

- Each item’s gold answer is a JSON array of ignored paths, serialized as a compact string.
- `scorer.py` parses and normalizes answers (sorts arrays) and does exact equality.

Verifier result:

- `verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl` → **OK**

## Self-score

Using `predictions.jsonl = gold_private_sample.jsonl`:

- Accuracy: **30/30 = 1.0**
- Output written to `score_report.json`

## Weak baseline

Baseline: a naive matcher that:

- ignores `!` negation rules entirely
- strips `*` and does substring matches
- ignores directory-only semantics and anchoring subtleties

Result on this 30-item sample:

- Accuracy: **9/30 = 0.30**
- Evidence: `baseline_naive_predictions.jsonl`, `baseline_naive_score_report.json`

This gap is consistent with the intended construct: correctness depends on rule precedence and edge cases, not just “spotting obvious ignores”.

## Solver bundle leakage check

The solver-visible bundle is limited to:

- `solver_bundle/items_private_sample.jsonl` (items only; no answers)
- `solver_bundle/SOLVER_MANIFEST.json`
- `solver_bundle/README.md`

No gold answers or grading code are present in `solver_bundle/`.

## Known limitations / scope

- This benchmark intentionally implements a **subset** of full gitignore semantics. The subset is the contract.
- No nested `.gitignore` files or per-directory rule stacks.
- No filesystem probing: everything is string-based and normalized to `/`.

If you extend the semantics, update the solver packet and keep `verifier.py` as the source of truth for reproducibility.

