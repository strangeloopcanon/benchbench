# Methodology And Process

BenchBench treats benchmark creation as the thing being evaluated. A model is
not asked to answer a fixed benchmark. It is asked to invent one.

The benchmark then has to survive a controlled solver grid. A task only matters
if it is externally solvable in principle, well specified, reproducible, and
hard after strong tool-enabled models attack the public evidence.

## Sweep Lifecycle

1. Pick creator and solver models.
2. Ask each creator model to build a complete benchmark package.
3. Validate each package locally.
4. Repair invalid packages once, using the same creator model.
5. Copy only the public `solver_bundle/` into an isolated solver directory.
6. Run each solver model blind against that bundle.
7. Score solver JSONL predictions against private gold answers.
8. Interpret the creator-by-solver matrix.
9. Write benchmark cards and a failure report for the next creator sweep.

A sweep is a matrix. Rows are benchmark creators. Columns are solvers. Cells
are exact-match scores out of 30.

## Candidate Package Contract

Each creator produces a self-contained candidate directory.

Required root files:

- `README.md`
- `benchmark_spec.json`
- `generator.py`
- `verifier.py`
- `scorer.py`
- `gold_private_sample.jsonl`
- `validation_report.md`
- `failure_modes.md`

Required public solver bundle:

- `solver_bundle/SOLVER_MANIFEST.json`
- `solver_bundle/items_private_sample.jsonl`
- `solver_bundle/README.md` or `solver_bundle/solver_packet.md`
- any solver-visible assets needed for the task

The private gold rows use exactly:

```json
{"id":"...","answer":"..."}
```

Solver predictions use the same contract.

## Validation

The controller checks package mechanics before scoring solvers. It:

- regenerates the 30-item sample from the required CLI;
- runs the verifier against public items and private gold answers;
- self-scores the private gold answers;
- runs a shifted-wrong control;
- checks that the solver bundle exists;
- checks that the public bundle has the item contract expected by the solver;
- scans the public bundle for obvious leakage, such as answer keys, private
  file names, or private traces.

Invalid candidates get one repair attempt from the same creator model. If the
package still fails validation, it is not a valid benchmark result.

## What Creators And Solvers See

Creator models see:

- the benchmark landscape pack;
- the Experiment 001 pilot summary;
- the exact artifact directory they must write into;
- the required package contract;
- optional prior-run feedback when `--feedback-context` is passed.

For the next full sweep, the intended feedback file is:

```text
experiments/feedback_for_next_full_6x6_sweep_20260523.md
```

That file includes the reconstructed 6x6 grids and the main failure lessons
from GPT, Gemini, and Claude runs through 2026-05-23.

Solver models do not see prior results. They receive only the isolated
`solver_bundle/` for the candidate they are solving. They may use tools, code,
OCR, local packages, and internet access if useful, but they may not inspect
parent directories, private gold answers, generators, scorers, private traces,
or answer keys.

Repair calls see the local validation failure report. They are meant to fix
package validity, not redesign the benchmark from scratch.

## Scoring

Solvers return JSONL rows with exactly `id` and `answer`. The controller
extracts matching rows, preserves item order, and runs the candidate's
`scorer.py` against private gold answers.

Missing rows, malformed rows, wrong item ids, timeouts, and parser failures all
count against the solver. BenchBench also records call metadata such as return
code, token counts, and Claude Code cost/cache fields when available.

## Feedback Loop

After a sweep, BenchBench can pass a failure report into the next creator run.
The runner now writes `feedback_for_next_sweep.md` next to the run summary. The
report includes the solver grid plus benchmark cards, so the next creators see
what each prior task actually asked instead of learning only from benchmark
names and scores.

The report names what broke:

- near-perfect solver scores;
- all-zero rows that need solvability audit;
- model-specific collapses;
- timeouts;
- parse failures;
- shortcut strategies;
- scorer-contract problems.

This turns benchmark invention into an iterative task. The question becomes:
can the next model design something still externally solvable, but less
breakable than the last attempt?

## Acceptance Logic

The gate is conservative.

- If many strong solvers get high scores, the candidate is too easy.
- If every solver gets zero, the candidate is not automatically good. It needs
  a solvability and identifiability audit.
- If low scores come from hidden labels, private vocabulary, type strictness,
  malformed output expectations, or missing public evidence, the candidate
  fails.
- If a task is mostly a tool-running stall or a narrow recovery puzzle, it may
  be diagnostically useful without being a clean broad benchmark.
- A useful candidate should be externally solvable, well specified,
  reproducible, hard under strong solver attempts, auditable, and meaningfully
  different from existing evals.

## Stable Bank Vs Fresh Sweeps

BenchBench has two run modes.

**Stable bank:** keep saved benchmark packages fixed and add new solver models
against the same public bundles. This is the cheapest way to compare a new
solver family against prior results.

**Fresh creator sweep:** ask current models to create new benchmark packages,
validate them, and run the full solver grid. Strong candidates can later be
promoted into the stable bank.

Current status: there is not yet a final promoted stable bank. Experiment 002
is a historical fixed-reference set. Experiment 004's Reimbursement Forensics
is the strongest current candidate for audit.

## What BenchBench Does Not Prove Yet

BenchBench does not yet prove that one model is generally the best benchmark
designer. It shows which model produced the best candidate in these runs.

It also does not yet prove novelty against the full benchmark landscape. The
similarity path exists, but the local solver set is still too small for serious
regression novelty claims.
