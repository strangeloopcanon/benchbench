# Broad BenchBench Sweep

This run used the broad creator prompt plus a prior-run failure report: creators saw benchmark landscape notes, prior pilot outcomes, and feedback on how the previous candidates broke.

Run root: `./experiments/014_halcyon_creator_20261003`
Creator models: `halcyon`
Solver models: `halcyon, gemini-3.7-flash-high, gemini-3.6-flash-high`
Creator effort: `high`
Solver effort: `high`
Creator feedback context: `./experiments/feedback_for_next_full_6x6_sweep_20260523.md`

Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.

## Benchmark Cards

### Halcyon: maritime_general_average_forensics

- What it asks: Forensic maritime average adjusting benchmark requiring cross-document reconciliation of bills of lading, port-of-refuge survey logs, master/adjuster expense vouchers, multi-currency FX schedules, and contemporaneous telex/email amendments under a self-contai...
- Intended capability: Measures whether tool-enabled frontier models can perform multi-hop forensic accounting and cross-document contradiction resolution over messy operational dossiers where every item has distinct narrative overrides, causal damage classifications (Sacrifice vs....
- Answer/scoring: Exact total final assessment (General Average contribution + Salvage contribution + Special Charges directly allocated to Lot-A, in integer USD cents) payable by Cargo Interest Lot-A at the termination of the adventure. - integer
- Closest existing benchmarks: Reimbursement Forensics (BenchBench historical #1 candidate); MuSR (multistep soft reasoning over narratives); GAIA / OSWorld document-grounded accounting tasks
- Creator-anticipated failure modes: *(Note: In `mgaf_01`, `mgaf_02`, `mgaf_14`, and `mgaf_17`, a baseline script that filters basic voucher tags scores `4/30 = 13.33%`, confirming the task is well-calibrated without being trivially solvable.)*
- Validation: `True`; bundle files: `9`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`

## Solver Grid

| creator | benchmark | solver Halcyon | solver Gemini 3.7 Flash (High) | solver Gemini 3.6 Flash (High) | max score | status |
|---|---|---:|---:|---:|---:|---|
| Halcyon | maritime_general_average_forensics | NA | NA | NA | NA | incomplete_panel |

## Calls

| phase | creator | solver/model | rows | score | tokens | cost | cache read | cache write | returncode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| creator | halcyon | Halcyon |  | NA | 534274 |  |  |  | -124 |
| repair | halcyon | Halcyon |  | NA | 545296 |  |  |  | 0 |

Total reported tokens: `1079570`

