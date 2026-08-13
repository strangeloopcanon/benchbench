# Experiment 013 — Gemini 3.7 Flash

Gemini 3.7 Flash (High) was tested as both a solver and a benchmark creator.
Antigravity reported the exact selected runtime label on every completed call.

## Results

| creator | candidate | Gemini 3.6 Flash high | Gemini 3.7 Flash high | verdict |
|---|---|---:|---:|---|
| Sol | AuditWeave | 30/30 | 30/30 | too easy |
| Terra | Counterfactual Firewall Policy Synthesis | 30/30 | 30/30 | too easy |
| Opus | Consolidation Point | 30/30 | 30/30 | too easy |
| Gemini 3.7 Flash | CloudSLA-Forensics | 30/30 | 30/30 | valid package, too easy |

CloudSLA-Forensics passed the mechanical package gate on its first creator
attempt: deterministic regeneration, frozen-package matching, complete public
solver evidence, valid scoring controls, and no detected leakage. It asks the
solver to reconcile cloud SLA contracts, incident telemetry, maintenance
notices, fault attribution, billing, and credit caps.

The benchmark is not a successful BenchBench candidate. Both tested frontier
Flash models solved all 30 items, and Gemini 3.7 also solved every valid
Experiment 010 candidate perfectly. No candidate is promoted.

Reimbursement Forensics remains the corrected historical #1 with retained
scores `12/30, 16/30, 11/30, 13/30, 11/30, 11/30`. Its original emitted gold
remains invalid, so this is still a historical comparison rather than a
canonical incumbent.
