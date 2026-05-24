# Experiments

This folder keeps two things separate: canonical presentation and raw run
history.

Current headline:

- Experiment 004 produced the frozen incumbent, Reimbursement Forensics.
- The canonical Round 3 grid carries that incumbent forward into the Experiment
  007 challenger comparison.
- No Experiment 007 challenger produced a better candidate.

Experiments 001 and 002 are provenance. They explain prompt evolution, but they
are not the main result.

## Current Files

- `canonical/README.md`: the clean three-round result story.
- `benchmark_bank.md`: status of current targets, diagnostic rows, and rejected
  candidates.
- `review_queue.md`: checks to run before a new low-scoring result becomes
  evidence.
- `result_grids_6x6_20260523.md`: stable pointer to the canonical result
  story.
- `feedback_for_next_challenger_sweep_20260523.md`: feedback packet for the
  next challenger sweep.

## Current Read

Reimbursement Forensics is the strongest benchmark seen so far. It scored in
the low nonzero band across all six tested solvers: 10/30 to 14/30.

That is the best shape we have seen: all solvers made some progress, and no
solver broke it open. The model-level read is that GPT-5.2 has been the best
benchmark creator so far, while Gemini 3.1 Pro and Gemini 3.5 Flash produced
the most interesting Round 3 challengers.

The experiment is mainly tracking which models can learn from prior failures
and design better tests. Stable reuse lives in `benchmark_bank.md`; the run
story is about creator judgment.

The canonical Round 3 comparison shows GPT-5.2 with its frozen incumbent and
the other Experiment 007 creators as challengers:

| creator | benchmark | read |
|---|---|---|
| GPT-5.2 | Reimbursement Forensics | frozen incumbent; still unbeaten |
| GPT-5.4 | Catalog Royalty Forensics | too easy |
| GPT-5.5 | Prior Authorization Forensics | too easy |
| Gemini 3.1 Pro | Commercial Lease CAM Reconciliation | diagnostic spread, too easy at the top end |
| Gemini 3.5 Flash | Maritime Freight & Customs Audit | diagnostic spread, too easy at the top end |
| Claude Opus | Construction Progress Payment Certification | saturated |

Raw Experiment 007's GPT-5.2 row is Service Credit Forensics. It scored 0/30
for every solver and remains a scorer/solvability problem case; it is not used
as the canonical GPT-5.2 row because frozen incumbents carry forward until
beaten.

## Canonical Runs

The canonical output lives in [`canonical/README.md`](canonical/README.md).
It presents:

- Round 1: Experiment 003 plus Claude Opus extension.
- Round 2: Experiment 004 plus Claude Opus extension.
- Round 3: Experiment 007 challengers plus GPT-5.2 incumbent carry-forward.

## Raw Run Folders

### `007_full_feedback_6x6_20260523_172919`

Direct six-creator, six-solver feedback sweep. All creators saw the current
failure report. Claude Opus ran through Cursor. The raw GPT-5.2 output was
Service Credit Forensics, which is a scorer/solvability problem case rather
than the canonical GPT-5.2 row.

Two contract interventions were made before interpreting the grid:

- Gemini 3.1 Pro's creator package was repaired from `{id, gold}` /
  `prediction` to the required `{id, answer}` contract and validated before its
  row was scored.
- Gemini 3.5 Flash's scorer was made robust to malformed non-object solver
  answers so those answers scored wrong instead of crashing.

No raw challenger row beat the frozen incumbent.

### `004_feedback_sweep_20260522_225208`

Feedback-driven five-model run. Creator models saw the Experiment 003 failure
report and were asked to build a benchmark that survived the observed solver
strategies.

Headline:

| creator | benchmark | result |
|---|---|---|
| GPT-5.2 | Reimbursement Forensics | current target to beat |
| GPT-5.4 | release_packet_arbitration | mostly too easy |
| GPT-5.5 | Cross-Document Obligation Resolution | scoring-contract failure |
| Gemini 3.1 Pro | Corrupted LZ77 Recovery | narrow and operationally brittle |
| Gemini 3.5 Flash | MFN-Cascade | too easy |

### `003_five_model_sweep_20260522_195526`

First full 5x5 run across GPT-5.2, GPT-5.4, GPT-5.5, Gemini 3.1 Pro, and
Gemini 3.5 Flash. It proved the Codex plus Antigravity creator/solver harness,
but every fresh candidate was solved 30/30 by at least one strong solver.

## Claude Opus Extensions

Claude Opus was added after Experiments 003 and 004.

| run | benchmark | result |
|---|---|---|
| `005_claude_opus_exp003_style_20260523_125019` | String Rewriting Distance | scorer type artifact; otherwise saturated |
| `006_claude_opus_feedback_style_20260523_125611` | Conlang Rosetta | saturated |

Claude Opus also strengthened the Reimbursement Forensics result by scoring
11/30 on it.

## Historical Support

### `001_three_model_grid_pilot`

First complete 3-model grid. It showed the visual/topology attractor in early
prompts.

### `002_broad_sweep_20260515_220653`

First broad prompt 3-model sweep. It produced three qualitatively different
benchmark families and became the first fixed reference set for adding Gemini
solver columns.

## Development Archive

`000_development_archive` keeps notes from earlier prompt iterations. Generated
run payloads from that phase are not canonical.

## Cleanup Policy

For canonical runs, keep summaries, manifests, creator prompts and outputs,
candidate benchmark packages, score JSONs, and solver predictions.

Generated isolated solver working directories may be deleted after the
corresponding predictions and score files are preserved.
