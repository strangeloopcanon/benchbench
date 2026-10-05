# Feedback For Next BenchBench Sweep

This file is generated from the current creator/solver sweep state. After the final solver finishes, give it to the next creator models with `--feedback-context`.

BenchBench is evaluating benchmark invention. The goal is a complete benchmark package that is valid, reproducible, externally solvable in principle, and still hard after strong tool-enabled solvers attack the public solver bundle.

## Result Grid

| creator | benchmark | solver Halcyon | solver Gemini 3.7 Flash (High) | solver Gemini 3.6 Flash (High) | max score | status |
|---|---|---:|---:|---:|---:|---|
| Halcyon | maritime_general_average_forensics | NA | NA | NA | NA | incomplete_panel |

## Benchmark Cards

These cards summarize what each prior benchmark actually asked, not just its name and score.

### Halcyon: maritime_general_average_forensics

- What it asks: Forensic maritime average adjusting benchmark requiring cross-document reconciliation of bills of lading, port-of-refuge survey logs, master/adjuster expense vouchers, multi-currency FX schedules, and contemporaneous telex/email amendments under a self-contai...
- Intended capability: Measures whether tool-enabled frontier models can perform multi-hop forensic accounting and cross-document contradiction resolution over messy operational dossiers where every item has distinct narrative overrides, causal damage classifications (Sacrifice vs....
- Answer/scoring: Exact total final assessment (General Average contribution + Salvage contribution + Special Charges directly allocated to Lot-A, in integer USD cents) payable by Cargo Interest Lot-A at the termination of the adventure. - integer
- Closest existing benchmarks: Reimbursement Forensics (BenchBench historical #1 candidate); MuSR (multistep soft reasoning over narratives); GAIA / OSWorld document-grounded accounting tasks
- Creator-anticipated failure modes: *(Note: In `mgaf_01`, `mgaf_02`, `mgaf_14`, and `mgaf_17`, a baseline script that filters basic voucher tags scores `4/30 = 13.33%`, confirming the task is well-calibrated without being trivially solvable.)*
- Validation: `False`; bundle files: `9`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`

## Lessons For The Next Creator

- Do not make a clean puzzle where the public packet exposes one obvious parser, simulator, BFS, or brute-force strategy.
- Do not rely on type strictness, hidden labels, private vocabulary, malformed output expectations, or missing public evidence to create low scores.
- Treat all-zero rows as audit warnings, not as automatic benchmark wins.
- Prefer complete but messy public evidence, closed answer contracts, adversarial edge cases, cross-document consistency, and partial recoverability.
- A candidate should be rejected if any strong solver gets 30/30, or if all strong solvers get 0/30 and the public bundle cannot prove external solvability.
