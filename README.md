# BenchBench

BenchBench asks whether models can invent good benchmarks.

A creator model writes a complete benchmark package. Other strong, tool-using
models then solve only the public bundle. A candidate only matters if it is
valid, auditable, externally solvable, and still hard.

## Current Answer

The best candidate so far is **Reimbursement Forensics**, created by GPT-5.2 in
Experiment 004.

It scored **10/30, 14/30, 11/30, 12/30, 11/30, and 11/30** across GPT-5.2,
GPT-5.4, GPT-5.5, Gemini 3.1 Pro, Gemini 3.5 Flash, and Claude Opus. That is
the target shape: every solver makes progress, and no solver solves it.

Reimbursement Forensics is frozen as the incumbent. It is not accepted yet. A
human still needs to audit leakage, answer evidence, scorer fairness, and
external solvability before it can move into a stable benchmark bank.

Experiment 007 was the latest full-feedback challenger sweep. It did not beat
the incumbent. Service Credit Forensics went all-zero and needs audit; Maritime
Freight and Commercial Lease CAM separated solvers but were too easy at the top
end; the other challengers saturated.

The canonical presentation carries GPT-5.2's frozen incumbent forward into the
latest challenger grid. Raw experiment folders remain unchanged.

![Canonical Round 3 6x6 heatmap](experiments/canonical/figures/canonical_round3_6x6_heatmap.svg)

## Why This Matters

Most benchmarks ask models to answer questions. BenchBench asks models to
invent the questions, package the evidence, define the scorer, and survive
attacks from other models.

That tests experimental judgment. Can a model learn from prior failures, avoid
cheap difficulty, and make a task that is neither trivial nor unknowable?

So far: sometimes. The models produce plausible benchmark packages quickly, but
most are too easy, brittle, or under-specified. Feedback helps. Freezing the
best result lets the next sweeps search for challengers instead of spending
tokens re-proving the same incumbent.

## Reading The Grids

Rows are benchmark creators. Columns are solvers. Cells are exact-match scores
out of 30.

- High scores mean the benchmark was too easy.
- Low nonzero scores are the useful band.
- All-zero rows need audit before they count as hard.
- No candidate is accepted until a human can verify that the public packet
  contains enough evidence and the scorer is fair.

Canonical grids and notes:
[`experiments/canonical/README.md`](experiments/canonical/README.md)

## Next Challenger Sweep

First resolve the audit queue:
[`experiments/audit_queue.md`](experiments/audit_queue.md)

Then run challengers against the full solver panel. GPT-5.2's Reimbursement
Forensics result stays frozen; the next run asks the other creators to beat it.

```bash
BENCHBENCH_CLAUDE_MAX_BUDGET_USD=25 python run_broad_three_model_sweep.py \
  --feedback-context experiments/feedback_for_next_challenger_sweep_20260523.md \
  --creator-models gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high cursor:claude-opus \
  --solver-models gpt-5.2 gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high cursor:claude-opus
```

Use `--models` for a symmetric sweep where creator and solver panels are the
same.

## Evidence

- [`experiments/benchmark_bank.md`](experiments/benchmark_bank.md): frozen,
  audit-required, and rejected candidates.
- [`experiments/canonical/README.md`](experiments/canonical/README.md):
  current presentation-layer 6x6 grids and heatmaps.
- [`experiments/007_full_feedback_6x6_20260523_172919/`](experiments/007_full_feedback_6x6_20260523_172919/):
  raw latest direct six-creator, six-solver challenger sweep.
- [`experiments/004_feedback_sweep_20260522_225208/`](experiments/004_feedback_sweep_20260522_225208/):
  source run for the frozen incumbent.
- [`benchmark_landscape/`](benchmark_landscape/): eval catalog and similarity
  notes used as creator context.

## Method

Full process: [`docs/methodology.md`](docs/methodology.md)

Commands and backend notes: [`docs/running.md`](docs/running.md)

In short:

1. Creators build complete benchmark packages.
2. The controller validates generation, scoring, public/private isolation, and
   obvious leakage.
3. Solvers receive only the public `solver_bundle/`.
4. Scores are computed against private gold answers.
5. Candidates are rejected, audited, or frozen as incumbents.

## Repo Map

- `run_broad_three_model_sweep.py`: creator/solver sweep harness.
- `run_existing_solver_extension.py`: add solver columns to saved runs.
- `benchbench_model_backends.py`: model backend dispatch.
- `benchbench_results.py`: shared score and prediction parsing helpers.
- `scripts/build_6x6_result_artifacts.py`: result grids and SVG heatmaps.
- `scripts/score_benchmark_similarity.py`: similarity/novelty smoke check.
