# Feedback For Next BenchBench Sweep

This file is generated from the current creator/solver sweep state. After the final solver finishes, give it to the next creator models with `--feedback-context`.

BenchBench is evaluating benchmark invention. The goal is a complete benchmark package that is valid, reproducible, externally solvable in principle, and still hard after strong tool-enabled solvers attack the public solver bundle.

## Result Grid

| creator | benchmark | solver gpt-5.2 | solver gpt-5.4 | solver gpt-5.5 | solver Gemini 3.1 Pro (High) | solver Gemini 3.5 Flash (High) | solver Claude Opus 4.6 Thinking | max score | status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.2 | Service Credit Forensics (SCF) v1 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | solvability_audit |
| gpt-5.4 | Catalog Royalty Forensics (CRF) v1 | 27/30 | 30/30 | 27/30 | 25/30 | 27/30 | 25/30 | 30/30 | reject |
| gpt-5.5 | Prior Authorization Forensics (PAF) v1 | 25/30 | 24/30 | 24/30 | 23/30 | 24/30 | 24/30 | 25/30 | reject |
| Gemini 3.1 Pro (High) | Commercial Lease CAM Reconciliation | 1/30 | 26/30 | 26/30 | 16/30 | 18/30 | 26/30 | 26/30 | reject |
| Gemini 3.5 Flash (High) | Maritime Freight & Customs Audit (MFCA) | 4/30 | 23/30 | 15/30 | 21/30 | 25/30 | 25/30 | 25/30 | reject |
| Claude Opus 4.6 Thinking | Construction Progress Payment Certification | 30/30 | 30/30 | 30/30 | 30/30 | 29/30 | 30/30 | 30/30 | reject |

## Benchmark Cards

These cards summarize what each prior benchmark actually asked, not just its name and score.

### gpt-5.2: Service Credit Forensics (SCF) v1

- What it asks: Cross-document SLA/service-credit forensics: determine eligible downtime and owed service credits from messy incident evidence (logs, email, status updates) under a public SLA policy and customer-specific contract riders.
- Answer/scoring: json
- Validation: `True`; bundle files: `184`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: gpt-5.2: 0/30, gpt-5.4: 0/30, gpt-5.5: 0/30, Gemini 3.1 Pro (High): 0/30, Gemini 3.5 Flash (High): 0/30, Claude Opus 4.6 Thinking: 0/30
- Current read: `solvability_audit`; max score `0/30`

### gpt-5.4: Catalog Royalty Forensics (CRF) v1

- What it asks: Cross-document royalty statement reconstruction from license riders, amendments, finance memos, and sales ledgers. Solvers must compute exact quarter-end royalty outputs under public recoupment and reserve rules.
- Answer/scoring: json
- Validation: `True`; bundle files: `124`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: gpt-5.2: 27/30, gpt-5.4: 30/30, gpt-5.5: 27/30, Gemini 3.1 Pro (High): 25/30, Gemini 3.5 Flash (High): 27/30, Claude Opus 4.6 Thinking: 25/30
- Current read: `reject`; max score `30/30`

### gpt-5.5: Prior Authorization Forensics (PAF) v1

- What it asks: Adjudicate fictional health-insurance claim dossiers by reconciling plan rules, service schedules, riders, provider-network notes, prior authorization/referral correspondence, date windows, and accumulators.
- Answer/scoring: json
- Creator-anticipated failure modes: prior authorization. Silver has plan-level referral requirements. in-network schedule, rounded to cents by the dossier amounts. and correspondence. infusion claims.
- Validation: `True`; bundle files: `33`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: gpt-5.2: 25/30, gpt-5.4: 24/30, gpt-5.5: 24/30, Gemini 3.1 Pro (High): 23/30, Gemini 3.5 Flash (High): 24/30, Claude Opus 4.6 Thinking: 24/30
- Current read: `reject`; max score `25/30`

### Gemini 3.1 Pro (High): Commercial Lease CAM Reconciliation

- What it asks: A benchmark that tests a solver's ability to extract specific clauses, timeline events, and expense reclassifications from unstructured text (emails, lease manuals) and structured data (CSV, JSON), and perfectly apply integer math rules to calculate Commercia...
- Creator-anticipated failure modes: This benchmark is designed to defeat both pure-LLM zero-shot solvers and pure-scripting heuristic solvers.
- Validation: `True`; bundle files: `153`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: gpt-5.2: 1/30, gpt-5.4: 26/30, gpt-5.5: 26/30, Gemini 3.1 Pro (High): 16/30, Gemini 3.5 Flash (High): 18/30, Claude Opus 4.6 Thinking: 26/30
- Current read: `reject`; max score `26/30`

### Gemini 3.5 Flash (High): Maritime Freight & Customs Audit (MFCA)

- What it asks: A complex, multi-document financial audit and reconciliation benchmark that requires solver models to act as trade compliance auditors. Solvers must read raw bills of lading, commercial invoices, vessel operation logs, exchange rate lists, and operational ema...
- Intended capability: text
- Closest existing benchmarks: Reimbursement Forensics
- Creator-anticipated failure modes: The **Maritime Freight & Customs Audit (MFCA)** benchmark is designed to expose deep reasoning and math vulnerabilities in frontier LLMs. Below are the specific cognitive, mathematical, and logical failure modes we anticipate solvers will exhibit.
- Validation: `True`; bundle files: `154`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: gpt-5.2: 4/30, gpt-5.4: 23/30, gpt-5.5: 15/30, Gemini 3.1 Pro (High): 21/30, Gemini 3.5 Flash (High): 25/30, Claude Opus 4.6 Thinking: 25/30
- Current read: `reject`; max score `25/30`

### Claude Opus 4.6 Thinking: Construction Progress Payment Certification

- What it asks: A benchmark for evaluating the ability to translate multi-article contract provisions into precise numerical computations. Each item presents a construction subcontract payment application that requires cross-referencing structured data with procedural rules,...
- Intended capability: Measures ability to correctly translate complex multi-article contract provisions into precise numerical computations, requiring cross-referencing of structured data with procedural rules, handling of boundary conditions, and multi-step arithmetic with interm...
- Closest existing benchmarks: Reimbursement Forensics (BenchBench internal); GAIA (agent reasoning)
- Creator-anticipated failure modes: Expected patterns of solver failure on the CPPC benchmark, organized by the rule they misinterpret or the implementation mistake they make.
- Validation: `True`; bundle files: `4`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: gpt-5.2: 30/30, gpt-5.4: 30/30, gpt-5.5: 30/30, Gemini 3.1 Pro (High): 30/30, Gemini 3.5 Flash (High): 29/30, Claude Opus 4.6 Thinking: 30/30
- Current read: `reject`; max score `30/30`

## Lessons For The Next Creator

- Do not make a clean puzzle where the public packet exposes one obvious parser, simulator, BFS, or brute-force strategy.
- Do not rely on type strictness, hidden labels, private vocabulary, malformed output expectations, or missing public evidence to create low scores.
- Treat all-zero rows as audit warnings, not as automatic benchmark wins.
- Prefer complete but messy public evidence, closed answer contracts, adversarial edge cases, cross-document consistency, and partial recoverability.
- A candidate should be rejected if any strong solver gets 30/30, or if all strong solvers get 0/30 and the public bundle cannot prove external solvability.
