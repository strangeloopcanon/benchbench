# Feedback For Next Challenger Sweep

Use this as `--feedback-context` after the audit queue has been checked.

BenchBench evaluates benchmark invention. The next creator should try to beat
the frozen incumbent, not recreate it.

## Target To Beat

Current frozen incumbent: **Reimbursement Forensics**, created by GPT-5.2 in
Experiment 004.

Solver scores:

| GPT-5.2 | GPT-5.4 | GPT-5.5 | Gemini 3.1 Pro | Gemini 3.5 Flash | Claude Opus |
|---:|---:|---:|---:|---:|---:|
| 10/30 | 14/30 | 11/30 | 12/30 | 11/30 | 11/30 |

This is the desired shape: every strong solver finds some answers, and none
solves the task.

It is frozen, not accepted. It still needs human audit for leakage, answer
evidence, scorer fairness, and external solvability.

## Latest Challenger Sweep

Experiment 007 gave all six creators the prior failure report, then ran all six
solvers on the new candidates. The canonical comparison carries GPT-5.2's
frozen incumbent forward and treats the other rows as challengers.

| creator | benchmark | GPT-5.2 | GPT-5.4 | GPT-5.5 | Gemini 3.1 Pro | Gemini 3.5 Flash | Claude Opus | read |
|---|---|---:|---:|---:|---:|---:|---:|---|
| GPT-5.2 (frozen) | Reimbursement Forensics | 10/30 | 14/30 | 11/30 | 12/30 | 11/30 | 11/30 | incumbent |
| GPT-5.4 | Catalog Royalty Forensics | 27/30 | 30/30 | 27/30 | 25/30 | 27/30 | 25/30 | too easy |
| GPT-5.5 | Prior Authorization Forensics | 25/30 | 24/30 | 24/30 | 23/30 | 24/30 | 24/30 | too easy |
| Gemini 3.1 Pro | Commercial Lease CAM Reconciliation | 1/30 | 26/30 | 26/30 | 16/30 | 18/30 | 26/30 | diagnostic spread, too easy |
| Gemini 3.5 Flash | Maritime Freight & Customs Audit | 4/30 | 23/30 | 15/30 | 21/30 | 25/30 | 25/30 | diagnostic spread, too easy |
| Claude Opus | Construction Progress Payment Certification | 30/30 | 30/30 | 30/30 | 30/30 | 29/30 | 30/30 | saturated |

Two notes matter:

- Raw Experiment 007's GPT-5.2 row was Service Credit Forensics. It scored
  0/30 for all six solvers and needs a solvability/scorer audit before it can
  count as hard.
- A large solver spread is not enough. Maritime Freight and CAM exposed
  differences between solvers, but at least one strong solver scored high.

## What The Prior Benchmarks Asked

Reimbursement Forensics asked solvers to reconcile messy reimbursement evidence
against policy rules and compute owed amounts. It worked because the public
evidence was rich, the answer contract was closed, and partial recovery was
possible.

Service Credit Forensics asked solvers to determine eligible downtime and owed
service credits from SLA policies, incident evidence, and customer riders. The
all-zero result is suspicious because the exact downtime field appears to have
zeroed otherwise plausible answers.

Catalog Royalty Forensics asked solvers to reconstruct quarter-end royalty
outputs from licenses, amendments, memos, and sales ledgers. It was too
scriptable or too directly recoverable.

Prior Authorization Forensics asked solvers to adjudicate health-insurance
claim dossiers against plan rules and correspondence. It looked messy but was
still mostly solved.

Commercial Lease CAM Reconciliation asked solvers to extract lease clauses,
timeline events, and expense reclassifications, then calculate maintenance
allocations. It produced uneven solver results but required a contract repair
and topped out too high.

Maritime Freight & Customs Audit asked solvers to reconcile bills of lading,
commercial invoices, vessel logs, exchange rates, and operational emails. It
created useful spread but did not resist the best solvers.

Construction Progress Payment Certification asked solvers to apply construction
contract payment rules. It saturated almost completely.

## Design Lessons

Do:

- Make the public evidence complete but messy.
- Use a closed answer contract with enough structure to score fairly.
- Include adversarial edge cases that require cross-document reconciliation.
- Let solvers recover partial credit if they understand part of the task.
- Explain external solvability in the package itself.

Avoid:

- Clean puzzles with one obvious parser, simulator, search, or brute-force path.
- Hidden labels, private vocabulary, unstated rounding rules, or type traps.
- Tasks that become impossible unless the solver guesses generator internals.
- Rows that are only hard because the scorer rejects reasonable answers.
- Reusing Reimbursement Forensics with a new surface story.

## Goal For The Next Creator

Create a complete package that is externally solvable and auditable, but scores
in the low nonzero band across the full solver panel.

The target is not 0/30. The target is a fair task where strong solvers can make
progress and still fail to solve it.
