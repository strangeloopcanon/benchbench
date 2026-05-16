# BenchBench

BenchBench is an experiment in evaluating models as benchmark inventors.

The object is not simply to make a task that frontier models fail. The object
is to make a benchmark package that is valid, reproducible, human-auditable,
hard under strong solver attempts, and useful as a measurement axis.

## Core Loop

1. A creator model builds a complete benchmark package.
2. The package is validated for generation, solver-bundle isolation, scoring,
   and leakage.
3. Solver models attack the public solver bundle with tools.
4. Easy benchmarks are rejected.
5. Benchmarks must be externally solvable in principle from the public solver
   bundle; impossible, under-specified, or private-keyed tasks do not count.
6. Benchmarks that nobody can solve are flagged for solvability audit, not
   automatically accepted.
7. Surviving candidates are compared against existing evals using rank
   correlations and regression predictability.

BenchBench itself is the system. Individual generated benchmarks are candidate
artifacts inside that system; there is no single "current live candidate."

## Current Useful Artifacts

- `benchmark_landscape/`: researched eval catalog, public score tables, model
  score matrix, and similarity method.
- `run_broad_three_model_sweep.py`: creator/solver sweep harness.
- `run_broad_xhigh_sanity.py`: extra high-effort solver sanity harness.
- `experiments/001_three_model_grid_pilot/`: first 3-model grid pilot.
- `experiments/002_broad_sweep_20260515_220653/`: broad prompt 3-model sweep.

## Main Findings So Far

- Broad creator prompts worked better than visually nudged prompts.
- `Spectrum Assembly` showed that formal-looking tasks can be trivial for
  tool-using solvers.
- `Protocol Archaeology` showed the opposite risk: all-zero model scores can
  reflect under-specification rather than a deep missing capability. Its final
  status is unresolved pending a separate audit run.
- `IgnoreSense` is a useful-looking generated benchmark candidate, but it still
  needs broader solver coverage and a real similarity check before any novelty
  claim.

## Running A Sweep

```bash
python run_broad_three_model_sweep.py
```

The creator prompt reads `benchmark_landscape/creator_prompt_landscape_pack.md`
when present, plus the Experiment 001 pilot summary.

## Similarity / Novelty Check

```bash
python scripts/score_benchmark_similarity.py \
  --target-benchmark benchbench_ignoresense \
  --out benchmark_landscape/similarity_ignoresense_smoke.md
```

The current local solver set is too small for serious regression novelty
claims. The method is ready; the data is not yet broad enough.
