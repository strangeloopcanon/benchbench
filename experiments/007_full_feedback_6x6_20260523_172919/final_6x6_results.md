# Experiment 007 Final 6x6 Results

Run root: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/007_full_feedback_6x6_20260523_172919`

This is the completed feedback-driven 6x6 after two narrow contract interventions:

- Gemini 3.1 Pro creator package was repaired from `{id, gold}` / `prediction` to the required `{id, answer}` contract and item-level 30-point scoring, then validated before solvers ran.
- Gemini 3.5 Flash scorer was made robust to string/non-object solver answers so malformed answers score wrong instead of crashing; the GPT-5.2 cell was rescored as 4/30.

| creator | benchmark | GPT-5.2 | GPT-5.4 | GPT-5.5 | Gemini 3.1 Pro | Gemini 3.5 Flash | Claude Opus | max | read |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| GPT-5.2 | Service Credit Forensics (SCF) v1 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | solvability audit |
| GPT-5.4 | Catalog Royalty Forensics (CRF) v1 | 27/30 | 30/30 | 27/30 | 25/30 | 27/30 | 25/30 | 30/30 | reject/saturated or too easy |
| GPT-5.5 | Prior Authorization Forensics (PAF) v1 | 25/30 | 24/30 | 24/30 | 23/30 | 24/30 | 24/30 | 25/30 | reject/saturated or too easy |
| Gemini 3.1 Pro | Commercial Lease CAM Reconciliation | 1/30 | 26/30 | 26/30 | 16/30 | 18/30 | 26/30 | 26/30 | reject/saturated or too easy |
| Gemini 3.5 Flash | Maritime Freight & Customs Audit (MFCA) | 4/30 | 23/30 | 15/30 | 21/30 | 25/30 | 25/30 | 25/30 | reject/saturated or too easy |
| Claude Opus | Construction Progress Payment Certification | 30/30 | 30/30 | 30/30 | 30/30 | 29/30 | 30/30 | 30/30 | reject/saturated or too easy |

## Notes

- Service Credit Forensics is all-zero and needs solvability/scorer audit before it can be interpreted as hard.
- Catalog Royalty, Prior Authorization, Maritime Freight, CAM, and Construction Progress all have at least one high-scoring solver and should not be treated as keeper benchmarks.
- Maritime Freight and CAM are diagnostically interesting because they create large solver spreads, but both are still too solvable at the top end.
