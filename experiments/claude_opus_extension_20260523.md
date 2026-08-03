# Claude Opus Extension - 2026-05-23

> **Historical report.** Its final interpretation predates the Decimal
> re-audit. Reimbursement Forensics remains the #1 corrected historical
> candidate and a win over the challengers, while its original gold is invalid
> and noncanonical. The original calls and scores remain below as provenance;
> `registry.v1.json` is authoritative.

This note summarizes the Claude Opus extension runs.

## Model Path

Antigravity Claude Opus was smoke-tested successfully, but the full creator
attempt through Antigravity produced no files after an extended wait. The full
creator and solver extension used native Claude Code Opus so BenchBench could
record cost and cache telemetry.

## Creator Runs

| run | prompt mode | benchmark | validation | full solver result | status |
|---|---|---|---|---|---|
| `005_claude_opus_exp003_style_20260523_125019` | Exp003-style starting prompt | String Rewriting Distance | valid | 0/30, 0/30, 30/30, 30/30, 30/30, 30/30 | reject; scorer type artifact plus saturation |
| `006_claude_opus_feedback_style_20260523_125611` | feedback-style prompt | Conlang Rosetta | valid | 30/30, 30/30, 30/30, 30/30, 30/30, 30/30 | reject; saturated |

The full solver result order is GPT-5.2, GPT-5.4, GPT-5.5, Gemini 3.1 Pro,
Gemini 3.5 Flash, Claude Opus. In the String Rewriting Distance row, GPT-5.2
and GPT-5.4 returned the right integer values as JSON strings, and the scorer
rejected those type-mismatched answers. The row is therefore not evidence of a
hard benchmark.

The feedback run initially appeared as 0/30 because Claude wrote
`predictions.jsonl` inside the isolated solver bundle and returned prose on
stdout. The harness was fixed to harvest solver-written prediction files before
deleting temp bundles. The corrected solver extension result is 30/30.

Claude's second creator run received the Experiment 003 failure report,
Experiment 004 result summary, solvability audit lessons, and the failure of
Claude's first String Rewriting Distance run. It did not receive the full 6x6
grids because they had not been reconstructed yet. The later Experiment 007
sweep used `feedback_for_next_full_6x6_sweep_20260523.md`; the next live packet
is `feedback_for_next_challenger_sweep_20260523.md`.

## Solver Extension Results

Experiment 003:

| creator | benchmark | Claude Opus |
|---|---|---:|
| GPT-5.2 | Ledger Canonical Reconciliation | 11/30 |
| GPT-5.4 | Patchwork Ordinance Adjudication | 30/30 |
| GPT-5.5 | Amendment Ledger Reconciliation | 30/30 |
| Gemini 3.1 Pro | Polyhedral Surface Traversal | 30/30 |
| Gemini 3.5 Flash | Mutative Assembly Inversion | 30/30 |

Experiment 004:

| creator | benchmark | Claude Opus |
|---|---|---:|
| GPT-5.2 | Reimbursement Forensics | 11/30 |
| GPT-5.4 | release_packet_arbitration | 25/30 |
| GPT-5.5 | Cross-Document Obligation Resolution | skipped; scoring-contract failure |
| Gemini 3.1 Pro | Corrupted LZ77 Recovery | 0/30; stopped after extended operational stall |
| Gemini 3.5 Flash | MFN-Cascade | 30/30 |

## Cost And Cache

Native Claude successful-call telemetry reported:

| group | reported cost | reported tokens |
|---|---:|---:|
| Claude creator run 005, including self-solve | $1.2836 | 854,160 |
| Claude creator run 006, creator plus final corrected self-solve | $1.4822 | 993,087 |
| Experiment 003 solver extension | $2.4310 | 1,417,962 |
| Experiment 004 solver extension, excluding killed LZ77 call | $1.9079 | 1,006,920 |

The killed LZ77 call and the abandoned Antigravity full-creator attempt do not
have usable cost telemetry.

## Interpretation

Claude Opus did not create a durable new benchmark in these two attempts. Both
packages were valid, but neither survived the full solver set.

As a solver, Claude Opus strengthens the case that Reimbursement Forensics is
the best corrected historical candidate: its retained prediction remains in
the low nonzero band at 11/30 after the Decimal correction. Across all six
retained predictions, the corrected profile is `12, 16, 11, 13, 11, 11`.
That is a win over the challengers, not a validation of the original gold. It
also confirms that MFN-Cascade and most Experiment 003 candidates are too easy.
The LZ77 row remains operationally brittle rather than a clean broad reasoning
measurement.

The canonical reconstructed 6x6 tables and heatmaps are in
`canonical/README.md`.
