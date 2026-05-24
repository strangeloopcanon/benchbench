# Experiments

This folder keeps the BenchBench run history.

The current headline evidence is:

1. Experiment 004 produced the frozen incumbent, Reimbursement Forensics.
2. Experiment 007 tested the next full-feedback 6x6 challenger sweep and did
   not produce a better candidate.

Experiments 001 and 002 are historical support. They are useful for provenance
and prompt evolution, but they are not the main result.

## Current Files

- `benchmark_bank.md`: status of frozen, audit-required, and rejected
  candidates.
- `audit_queue.md`: checks to run before the next experiment is used as
  evidence.
- `result_grids_6x6_20260523.md`: current 6x6 result grids and heatmaps.
- `feedback_for_next_challenger_sweep_20260523.md`: feedback packet for the
  next challenger sweep.

## Current Read

Reimbursement Forensics is frozen as the incumbent. It scored in the low
nonzero band across all six tested solvers: 10/30 to 14/30.

That is the best shape seen so far, but it is not accepted yet. It still needs
a human audit for leakage, answer evidence, and external solvability.

Experiment 007 did not displace it:

| creator | benchmark | read |
|---|---|---|
| GPT-5.2 | Service Credit Forensics | all-zero; audit required |
| GPT-5.4 | Catalog Royalty Forensics | too easy |
| GPT-5.5 | Prior Authorization Forensics | too easy |
| Gemini 3.1 Pro | Commercial Lease CAM Reconciliation | interesting spread, too easy at the top end |
| Gemini 3.5 Flash | Maritime Freight & Customs Audit | interesting spread, too easy at the top end |
| Claude Opus | Construction Progress Payment Certification | saturated |

## Canonical Runs

### `007_full_feedback_6x6_20260523_172919`

Direct six-creator, six-solver feedback sweep. All creators saw the current
failure report. Claude Opus ran through Cursor.

Two narrow contract interventions were made before interpreting the grid:

- Gemini 3.1 Pro's creator package was repaired from `{id, gold}` /
  `prediction` to the required `{id, answer}` contract and validated before its
  row was scored.
- Gemini 3.5 Flash's scorer was made robust to malformed non-object solver
  answers so those answers scored wrong instead of crashing.

No row beat the frozen incumbent.

### `004_feedback_sweep_20260522_225208`

Feedback-driven five-model run. Creator models saw the Experiment 003 failure
report and were asked to build a benchmark that survived those solver
strategies.

Headline:

| creator | benchmark | result |
|---|---|---|
| GPT-5.2 | Reimbursement Forensics | frozen incumbent; audit next |
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
