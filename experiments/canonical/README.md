# Canonical BenchBench Status

Generated from `experiments/registry.v1.json`. Raw run folders remain preserved as evidence; this page does not turn a historical score into a current claim.

## Current State

**No validated incumbent.** No benchmark can be promoted until its public evidence, gold generation, scorer, complete solver panel, and execution state pass the registry gates.

![Canonical status](figures/canonical_status.svg)

## Corrected Historical Result

**#1: Reimbursement Forensics is the best corrected historical candidate and counts as a win over the challengers.**

Against independently recomputed Decimal half-up gold, the six retained solver predictions score 12/30, 16/30, 11/30, 13/30, 11/30, and 11/30. This remains the only complete six-solver row with every score low and nonzero; later challenger rows reach 25/30 or higher, are invalid, or are incomplete. Every completed Experiment 010 solver cell is 30/30; Opus did not complete two cells and Gemini produced no valid candidate.

This is a corrected historical comparison, not a canonical promotion. Experiment 004 remains invalid because its original emitted gold was wrong, and no model was rerun.

## Historical Results Excluded From Canonical Ranking

| experiment | benchmark | creator | outcome | preserved historical evidence | required next step |
|---|---|---|---|---|---|
| 004 | Reimbursement Forensics | GPT-5.2 | invalid | recorded: 10/30, 14/30, 11/30, 12/30, 11/30, 11/30, re-audit rescore of retained predictions: 12/30, 16/30, 11/30, 13/30, 11/30, 11/30 | Repair generation and verification with Decimal-only half-up rounding, then generate a new version and run a complete fresh solver panel. |
| 007 | Service Credit Forensics | GPT-5.2 | invalid | recorded historical row: 0/30, 0/30, 0/30, 0/30, 0/30, 0/30 | Regenerate gold from the same public precedence rule, validate the packet, and run a complete fresh solver panel. |
| 008 | Rosetta Fieldwork | Claude Fable 5 Thinking | infrastructure_incomplete | successful historical cells only: GPT-5.4 14/30, GPT-5.5 11/30, Gemini 3.1 Pro 24/30, Gemini 3.5 Flash 27/30; GPT-5.2: provider_error, Claude Opus: did not complete (timeout) | Use typed cell states, fix provider preflight, and rerun the missing cells under the repaired execution contract. |
| 009 | Counterfeit Clock v1 | Codex GPT-5.6 Sol high | invalid | No canonical numeric score | Create a new candidate version whose scorer emits schema_version 2 with total, correct, and accuracy, pass the full mechanical gate, then run a complete fresh solver panel. |
| 009 | Patchwork Access Logic (PAL) | Codex GPT-5.6 Terra extra high | invalid | No canonical numeric score | Create a new candidate version whose scorer emits schema_version 2 with total, correct, and accuracy, pass the full mechanical gate, then run a complete fresh solver panel. |
| 010 | AuditWeave | Codex GPT-5.6 Sol high | infrastructure_incomplete | successful cells only: Sol 30/30, Terra 30/30, Gemini 3.6 Flash high 30/30 (recovery); Claude Opus 5 high: did not complete (timeout) | Increase task difficulty, generate a new version, and run a complete fresh solver panel. |
| 010 | Counterfactual Firewall Policy Synthesis | Codex GPT-5.6 Terra extra high | infrastructure_incomplete | successful cells only: Sol 30/30, Terra 30/30, Gemini 3.6 Flash high 30/30 (recovery); Claude Opus 5 high: did not complete (timeout) | Increase task difficulty, generate a new version, and run a complete fresh solver panel. |
| 010 | Gemini creator recovery (no valid candidate) | Antigravity Gemini 3.6 Flash high | invalid | No canonical numeric score | Create a fresh candidate version that passes the complete mechanical package gate. |
| 010 | Consolidation Point | Cursor Claude Opus 5 high | infrastructure_incomplete | completed cells: Sol 30/30, Terra 30/30, Gemini 3.6 Flash high 30/30 (recovery), Opus 30/30 | Increase task difficulty, generate a new version, and run a complete fresh solver panel. |

The figures above are historical evidence only. In particular, `0/30` is never used for a provider error, timeout, malformed output, or incomplete panel.

## Adjudications

- [Reimbursement Forensics](../adjudications/004_reimbursement_forensics.md): Decimal half-up re-audit changed three gold answers and rescored the retained predictions to `12, 16, 11, 13, 11, 11`. It remains the #1 corrected historical candidate and a win over the challengers, while the original run remains invalid and noncanonical.
- [Service Credit Forensics](../adjudications/007_service_credit_forensics.md): a higher-precedence public timeline contradicts gold computed from lower-precedence monitoring states.
- [Fable creator sweep](../adjudications/008_fable_creator_sweep.md): GPT-5.2 was a provider error and Claude Opus timed out; neither is a `0/30` result.
- [Four-model panel](../adjudications/009_four_model_panel.md): both created candidates failed the mechanical score-report contract, Antigravity then failed before inference, and no solver cell ran.
- [Frontier-four panel](../adjudications/010_four_model_panel.md): original sealed result; three candidates passed the mechanical gate and every completed cell was `30/30`.
- [Experiment 010 provider recovery](../adjudications/010_provider_recovery_20260802.md): Gemini recovered all three missing solver cells at `30/30`; Opus still did not complete two cells, and Gemini produced no valid candidate.

## Registry Coverage

| experiment | raw run | outcome | registry read |
|---|---|---|---|
| 001 | experiments/001_three_model_grid_pilot | historical_noncanonical | Pilot provenance; not an adjudicated benchmark bank. |
| 002 | experiments/002_broad_sweep_20260515_220653 | historical_noncanonical | Prompt-evolution provenance; not an adjudicated benchmark bank. |
| 003 | experiments/003_five_model_sweep_20260522_195526 | historical_noncanonical | Historical full-grid evidence; no candidate is promoted by this registry. |
| 004 | experiments/004_feedback_sweep_20260522_225208 | invalid | Reimbursement Forensics remains the #1 corrected historical candidate and a win over the challengers, but its original emitted gold fails Decimal half-up semantics and the run remains invalid. |
| 005 | experiments/005_claude_opus_exp003_style_20260523_125019 | historical_noncanonical | Claude extension retained as provenance, not a validated benchmark. |
| 006 | experiments/006_claude_opus_feedback_style_20260523_125611 | historical_noncanonical | Claude extension retained as provenance, not a validated benchmark. |
| 007 | experiments/007_full_feedback_6x6_20260523_172919 | invalid | Service Credit Forensics gold conflicts with higher-precedence public evidence. |
| 008 | experiments/008_fable_creator_sweep_20260610_085405 | infrastructure_incomplete | The Fable sweep has a GPT-5.2 provider error and a Claude Opus timeout. |
| 009 | experiments/009_four_model_panel_20260801_103006 | infrastructure_incomplete | Both completed Codex candidates failed the mechanical score-report contract; Antigravity then failed before inference with zero token telemetry, and the fail-closed budget gate did not start Cursor or any solver cells. |
| 010 | experiments/010_four_model_panel_20260801_120442 | infrastructure_incomplete | Three candidates passed the mechanical gate. Gemini's recovered solver cells all scored 30/30, leaving every completed cell at 30/30; Opus did not complete two cells. Gemini recovery creator work produced no valid candidate. |

A future incumbent must be introduced by a new `validated` candidate entry with digest-verified evidence. The canonical builder rejects a candidate marked eligible with any other outcome.
