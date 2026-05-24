# Methodology And Process

BenchBench evaluates benchmark invention.

A creator model writes a complete benchmark package. Solver models then attack
the public solver bundle. The benchmark only matters if it is externally
solvable in principle, reproducible, auditable, and still hard after strong
tool-enabled solvers try it.

## Sweep Lifecycle

1. Pick creator and solver panels.
2. Give creators the benchmark landscape, prior pilot notes, and any feedback
   packet supplied with `--feedback-context`.
3. Ask each creator to write a complete candidate package.
4. Validate package mechanics locally.
5. Give each invalid package one repair call from the same creator.
6. Copy only the public `solver_bundle/` into isolated solver directories.
7. Run each solver blind against each valid candidate.
8. Score solver JSONL predictions against private gold answers.
9. Interpret the grid.
10. Write benchmark cards and feedback for the next sweep.

Rows in the grid are benchmark creators. Columns are solvers. Cells are
exact-match scores out of 30.

## Candidate Package Contract

Each creator produces a self-contained directory.

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

Private gold rows use exactly:

```json
{"id":"...","answer":"..."}
```

Solver predictions use the same `id` and `answer` contract.

## Validation

The controller checks whether the package can be run and scored before it lets
solvers spend time on it. It:

- regenerates the 30-item sample from the required CLI;
- runs the verifier against public items and private gold answers;
- self-scores the private gold answers;
- runs a shifted-wrong control;
- checks that the solver bundle exists;
- checks that public item ids match private gold ids;
- scans the public bundle for obvious leakage.

Invalid candidates get one repair attempt from the same creator model. Repairs
are for package validity, not a new benchmark design.

## What Creators And Solvers See

Creator models see the broad benchmark landscape pack, the Experiment 001 pilot
summary, the artifact directory they must write into, and the package contract.
When `--feedback-context` is supplied, they also see prior run results,
benchmark cards, and failure lessons.

Solver models do not see prior results. They receive only the isolated
`solver_bundle/` for the candidate they are solving. They may use tools, code,
OCR, local packages, and internet access if useful. They may not inspect parent
directories, private gold answers, generators, scorers, private traces, or
answer keys.

## Scoring

Solvers return JSONL rows with exactly `id` and `answer`. The controller
extracts matching rows, preserves item order, and runs the candidate's
`scorer.py` against private gold answers.

Missing rows, malformed rows, wrong item ids, timeouts, parser failures, and
scorer crashes all count against the solver. The manifest also records return
codes, token counts, and backend-specific cache or cost fields when available.

## Interpreting Results

The gate is conservative.

- If many strong solvers get high scores, the candidate is too easy.
- If every solver gets zero, the candidate goes to audit. It is not a win yet.
- If low scores come from hidden labels, private vocabulary, type strictness,
  malformed output expectations, or missing public evidence, the candidate
  fails.
- If a task is mainly a tool-running stall or a narrow recovery puzzle, it may
  be diagnostically useful without becoming a broad benchmark.
- A useful candidate should be externally solvable, well specified,
  reproducible, hard under strong solver attempts, auditable, and meaningfully
  different from existing evals.

## Frozen Incumbents And Challenger Sweeps

Once a candidate reaches the desired low-nonzero shape, it can be frozen as an
incumbent. Freezing means the saved package and score grid become the current
target to beat.

Frozen does not mean accepted. It means "do not rerun this creator result in
every fresh sweep unless something material changes." Rerun it only when:

- a new solver family is added;
- the package or scorer is audited and repaired;
- calibration against the incumbent is needed;
- the model panel changes enough that the old result is no longer comparable.

The next sweep should usually be a challenger sweep: keep the incumbent in the
benchmark bank, give its result and failure lessons to the creators, and ask
the remaining creators to produce better candidates. The runner supports this
with separate `--creator-models` and `--solver-models` panels.

## Audit Gate Between Experiments

Audit-required candidates should be checked before they become feedback anchors
or frozen incumbents.

The audit asks:

- Does the public bundle contain enough evidence to solve each item?
- Are the answer fields identifiable without private vocabulary?
- Does the scorer accept semantically correct answers in the stated format?
- Did solvers fail because the benchmark is hard, or because the contract is
  unfair, brittle, or ambiguous?
- Is there leakage from gold answers, generator logic, hidden seeds, or private
  traces?

The current audit queue is tracked in
[`experiments/audit_queue.md`](../experiments/audit_queue.md).

## Stable Bank Vs Fresh Sweeps

BenchBench now separates three states:

- **Frozen incumbent:** the best current candidate to beat, pending audit.
- **Stable bank:** audited benchmark packages that can be reused as fixed
  solver tests. This is not populated yet.
- **Fresh sweep:** a new creator run that searches for better candidates.

Experiment 004's Reimbursement Forensics is the current frozen incumbent. It is
not yet a promoted stable-bank benchmark.

## What BenchBench Does Not Prove Yet

BenchBench does not prove that one model is generally the best benchmark
designer. It shows which model produced the best candidate in these runs.

It also does not prove novelty against the whole benchmark landscape. The
similarity path exists, but the local evidence is still a smoke check rather
than a full novelty claim.
