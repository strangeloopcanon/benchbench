# Methodology

BenchBench evaluates benchmark invention.

A creator model writes a benchmark package. Solver models attack only the
public bundle. A candidate is useful only if it is externally solvable,
reproducible, auditable, and still hard after that attack.

## Sweep Lifecycle

1. Choose creator and solver panels.
2. Give creators the landscape pack, pilot notes, package contract, and any
   `--feedback-context`.
3. Ask each creator to write a complete candidate package.
4. Validate package mechanics locally.
5. Give each invalid package one repair call from the same creator.
6. Copy only `solver_bundle/` into isolated solver directories.
7. Run each solver blind against each valid candidate.
8. Score solver JSONL against private gold answers.
9. Interpret the creator-by-solver grid.
10. Write benchmark cards and feedback for the next sweep.

Rows are creators. Columns are solvers. Cells are exact-match scores out of 30.

## Candidate Contract

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

Required public bundle:

- `solver_bundle/SOLVER_MANIFEST.json`
- `solver_bundle/items_private_sample.jsonl`
- `solver_bundle/README.md` or `solver_bundle/solver_packet.md`
- any solver-visible assets needed for the task

Private gold rows and solver predictions both use:

```json
{"id":"...","answer":"..."}
```

## Validation

The controller checks whether a package can be generated, verified, and scored
before solvers spend time on it. It:

- regenerates the 30-item sample from the required CLI;
- runs the verifier against public items and private gold;
- self-scores the gold answers;
- runs a shifted-wrong control;
- checks that the public item ids match private gold ids;
- scans the public bundle for obvious leakage.

Repairs are for validity only: fixing generation, scoring, contracts, or bundle
isolation. They are not a second chance to invent a new benchmark.

## Who Sees What

Creators see the landscape pack, Experiment 001 pilot summary, artifact path,
package contract, and any feedback file supplied with `--feedback-context`.
Feedback files include prior grids, benchmark cards, and failure lessons.

Solvers see only the isolated `solver_bundle/` for the candidate they are
solving. They may use tools, code, OCR, local packages, and internet access.
They may not inspect parent directories, private gold, generators, scorers,
private traces, or answer keys.

## Scoring

Solvers return JSONL rows with exactly `id` and `answer`. The controller
extracts matching rows, preserves item order, and runs the candidate's
`scorer.py` against private gold.

Missing rows, malformed rows, wrong item ids, timeouts, parser failures, and
scorer crashes all count against the solver. Manifests also record return
codes, token counts, and backend-specific cache or cost fields when available.

## Interpreting A Candidate

The gate is conservative.

- High scores from strong solvers mean the candidate is too easy.
- All-zero rows go to audit. They are not wins by default.
- Low scores caused by hidden labels, private vocabulary, strict types,
  malformed output expectations, or missing public evidence fail the candidate.
- Tool stalls and narrow recovery puzzles can be diagnostic without becoming
  broad benchmarks.
- A keeper should be externally solvable, well specified, reproducible,
  auditable, hard under strong solver attempts, and meaningfully different from
  existing evals.

## Frozen Incumbents

When a candidate reaches the desired low-nonzero shape, it can be frozen as an
incumbent. Frozen means "current target to beat." It does not mean accepted.

Rerun a frozen incumbent only when:

- a new solver family is added;
- the package or scorer is audited and repaired;
- calibration against the incumbent is needed;
- the model panel changes enough to break comparability.

Otherwise, run challenger sweeps: keep the incumbent in the benchmark bank,
give creators its result and failure lessons, and ask them to produce better
candidates. The runner supports this with separate `--creator-models` and
`--solver-models`.

## Canonical Presentation

Raw run folders stay literal. They record what each model produced in that
run, including failed candidates and audit items.

Presentation grids can carry a frozen incumbent forward. In a challenger
sweep, the carried-forward row is marked as frozen and compared against new
challenger rows. That keeps the leaderboard honest: raw history is not edited,
but the current comparison asks whether any new candidate beat the incumbent.

The current canonical result set is in
[`experiments/canonical/README.md`](../experiments/canonical/README.md).

## Audit Gate

Audit-required candidates should be checked before they become feedback anchors
or frozen incumbents.

The audit asks:

- Does the public bundle contain enough evidence to solve each item?
- Are answer fields identifiable without private vocabulary?
- Does the scorer accept the stated answer format?
- Did solvers fail because the benchmark is hard, or because the contract is
  unfair, brittle, or ambiguous?
- Is there leakage from gold answers, generator logic, hidden seeds, or private
  traces?

Current queue: [`experiments/audit_queue.md`](../experiments/audit_queue.md)

## Benchmark States

- **Frozen incumbent:** best current candidate to beat, pending audit.
- **Stable bank:** audited packages ready for fixed solver tests. Empty for
  now.
- **Fresh sweep:** a new creator run searching for better candidates.

Reimbursement Forensics is the current frozen incumbent. It is not yet a stable
bank benchmark.

## Limits

BenchBench does not yet prove that one model is generally the best benchmark
designer. It shows which model produced the best candidate in these runs.

It also does not prove novelty against the whole eval landscape. The similarity
path exists, but the current evidence is still a smoke check.
