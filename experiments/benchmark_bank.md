# Benchmark Bank

BenchBench separates frozen incumbents from accepted stable benchmarks.

Frozen means "best current candidate to beat." Accepted means "audited and
ready to reuse as a stable benchmark." Nothing has reached accepted status yet.

## Frozen Incumbent

| benchmark | creator | source | solver scores | status |
|---|---|---|---|---|
| Reimbursement Forensics | GPT-5.2 | `004_feedback_sweep_20260522_225208` plus Claude extension | 10/30, 14/30, 11/30, 12/30, 11/30, 11/30 | frozen; audit next |

Why it is frozen: every tested solver landed in the low nonzero band. That is
the best shape so far.

Why it is not accepted: it still needs human review for leakage, answer
evidence, scorer fairness, and external solvability.

## Audit Required

| benchmark | creator | source | observed result | audit question |
|---|---|---|---|---|
| Service Credit Forensics | GPT-5.2 | `007_full_feedback_6x6_20260523_172919` | 0/30 for all six solvers | Did solvers fail because the benchmark is hard, or because eligible downtime is under-specified/scored unfairly? |

Service Credit is a raw Experiment 007 audit item. It is not used as GPT-5.2's
canonical Round 3 row because the frozen Reimbursement Forensics incumbent
carries forward until beaten. The field-level read is suspicious: solvers often
got other fields close, but all failed the exact eligible-downtime field.

## Diagnostic But Rejected

| benchmark | creator | source | solver scores | read |
|---|---|---|---|---|
| Maritime Freight & Customs Audit | Gemini 3.5 Flash | Experiment 007 | 4/30, 23/30, 15/30, 21/30, 25/30, 25/30 | diagnostic spread, too easy at the top end |
| Commercial Lease CAM Reconciliation | Gemini 3.1 Pro | Experiment 007 | 1/30, 26/30, 26/30, 16/30, 18/30, 26/30 | diagnostic spread, too easy at the top end; required contract repair |
| Corrupted LZ77 Recovery | Gemini 3.1 Pro | Experiment 004 plus Claude extension | 0/30, 22/30, 17/30, 0/30, 0/30, 0/30 | narrow and operationally brittle |

These rows are useful diagnostics. They should not be promoted as stable
benchmarks.

## Rejected As Too Easy Or Brittle

| benchmark | creator | source | read |
|---|---|---|---|
| Catalog Royalty Forensics | GPT-5.4 | Experiment 007 | too easy; max 30/30 |
| Prior Authorization Forensics | GPT-5.5 | Experiment 007 | too easy; max 25/30 |
| Construction Progress Payment Certification | Claude Opus | Experiment 007 | saturated |
| release_packet_arbitration | GPT-5.4 | Experiment 004 | mostly too easy |
| Cross-Document Obligation Resolution | GPT-5.5 | Experiment 004 | scoring-contract failure |
| MFN-Cascade | Gemini 3.5 Flash | Experiment 004 | saturated |
| Conlang Rosetta | Claude Opus | Experiment 006 | saturated |
| String Rewriting Distance | Claude Opus | Experiment 005 | scorer type artifact; otherwise saturated |
