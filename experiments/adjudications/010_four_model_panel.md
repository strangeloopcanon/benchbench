# Adjudication: Four-Model Panel (Experiment 010)

Outcome: **infrastructure incomplete; no validated incumbent**.

The run used the exact frontier-four policy:

- Codex `gpt-5.6-sol` at high
- Codex `gpt-5.6-terra` at extra high
- Antigravity `gemini-3.6-flash-high` at high, verified at runtime as `Gemini 3.6 Flash (High)`
- Cursor `claude-opus-5-thinking-high` at high

Codex reported its actual runtime model and effort. Antigravity reported its
selected runtime label. Cursor's response format does not report the selected
model, and this run did not freeze a catalog result or a successful credential-
safe live canary. Its Opus identity is therefore the exact requested CLI model
ID, not provider-reported runtime attestation: **requested/unverified**. The
later recovery adjudication preserves this qualification.

The immutable source run is
`experiments/010_four_model_panel_20260801_120442`; its manifest digest is
`8c3ab2c7db5e00f5da948e722d943f9ee6813af4c8e00a697f8b1c765da1e326`.
After one zero-telemetry Cursor timeout stopped new dispatches, four immutable
solver overlays completed only the eight missing CFPS and Consolidation Point
cells. They did not rerun any creator or alter the source run. The combined
machine-readable result is `combined_result.v1.json` in the source run.
Each overlay carries a verified source-evidence index whose copied source
manifest hashes to the immutable source manifest digest above.

## Combined solver grid

| creator | benchmark | Sol high | Terra extra high | Gemini 3.6 Flash high | Claude Opus 5 high |
|---|---|---:|---:|---:|---:|
| Sol | AuditWeave | 30/30 | 30/30 | invalid output | timeout |
| Terra | Counterfactual Firewall Policy Synthesis | 30/30 | 30/30 | invalid output | timeout |
| Gemini | no candidate artifact | NA | NA | NA | NA |
| Opus | Consolidation Point | 30/30 | 30/30 | invalid output | 30/30 |

Every numeric result is 30/30. These benchmarks are therefore too easy for the
models that returned valid predictions. `invalid output` and `timeout` remain
typed failures and are never converted to numeric scores.

## Candidate validity

AuditWeave, Counterfactual Firewall Policy Synthesis, and Consolidation Point
passed the mechanical candidate gate on their first attempts: deterministic
regeneration, frozen-package matching, gold and shifted-wrong controls,
external-solvability evidence, and leakage checks.

Gemini's creator call returned successfully but left its artifact directory
empty. One repair call also returned successfully and left it empty. This is a
candidate-generation failure, not a model-routing failure: the exact Gemini
runtime label was present for both calls.

None of the mechanically valid candidates can be promoted. Their declared
four-model panels contain invalid outputs or timeouts, and their successful
cells do not demonstrate useful difficulty.

## Token accounting

The source run reported 6,344,511 tokens. The four completion overlays reported
692,362, for a combined reported total of **7,036,873 tokens**.

Two Opus solver calls timed out with no token telemetry. For budget safety, the
adjudication reserves 5,000,000 tokens for each unknown call. This produces a
**17,036,873 charged-equivalent** total under the 20,000,000 dispatch ceiling.
That charged-equivalent figure is conservative controller accounting, not a
claim about provider consumption. No provider supplied normalized dollar cost.

A 5,000,000 whole-run cap would have been too small: the successful Opus
creator call alone reported 6,011,630 tokens. Future frontier-four sweeps should
retain a much larger dispatch ceiling and separately reserve for unknown
telemetry.

## Relative ranking

**Reimbursement Forensics remains #1 and this counts as a win over the
challengers.** Its corrected retained-prediction profile is `12/30, 16/30,
11/30, 13/30, 11/30, 11/30`. Every numeric Experiment 010 challenger cell is
30/30, while the other cells are invalid output or timeout.

This is still a corrected historical comparison, not a canonical promotion.
Reimbursement Forensics remains invalid because Experiment 004 emitted wrong
gold; no model was rerun for its Decimal re-audit.
