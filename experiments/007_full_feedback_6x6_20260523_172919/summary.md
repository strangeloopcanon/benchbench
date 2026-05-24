# Broad BenchBench Sweep

This run used the broad creator prompt plus a prior-run failure report: creators saw benchmark landscape notes, prior pilot outcomes, and feedback on how the previous candidates broke.

Run root: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/007_full_feedback_6x6_20260523_172919`
Creator models: `gpt-5.2, gpt-5.4, gpt-5.5, gemini-3.1-pro, gemini-3.5-flash-high, claude-opus`
Solver models: `gpt-5.2, gpt-5.4, gpt-5.5, gemini-3.1-pro, gemini-3.5-flash-high, claude-opus`
Creator effort: `low`
Solver effort: `low`
Creator feedback context: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/feedback_for_next_full_6x6_sweep_20260523.md`

Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.

## Benchmark Cards

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

## Solver Grid

| creator | benchmark | solver gpt-5.2 | solver gpt-5.4 | solver gpt-5.5 | solver Gemini 3.1 Pro (High) | solver Gemini 3.5 Flash (High) | solver Claude Opus 4.6 Thinking | max score | status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.2 | Service Credit Forensics (SCF) v1 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | solvability_audit |
| gpt-5.4 | Catalog Royalty Forensics (CRF) v1 | 27/30 | 30/30 | 27/30 | 25/30 | 27/30 | 25/30 | 30/30 | reject |
| gpt-5.5 | Prior Authorization Forensics (PAF) v1 | 25/30 | 24/30 | 24/30 | 23/30 | 24/30 | 24/30 | 25/30 | reject |
| Gemini 3.1 Pro (High) | Commercial Lease CAM Reconciliation | 1/30 | 26/30 | 26/30 | 16/30 | 18/30 | 26/30 | 26/30 | reject |
| Gemini 3.5 Flash (High) | Maritime Freight & Customs Audit (MFCA) | 4/30 | 23/30 | 15/30 | 21/30 | 25/30 | 25/30 | 25/30 | reject |
| Claude Opus 4.6 Thinking | Construction Progress Payment Certification | 30/30 | 30/30 | 30/30 | 30/30 | 29/30 | 30/30 | 30/30 | reject |

## Calls

| phase | creator | solver/model | rows | score | tokens | cost | cache read | cache write | returncode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| creator | gpt-5.2 | gpt-5.2 |  | NA | 177413 |  |  |  | 0 |
| creator | gpt-5.4 | gpt-5.4 |  | NA | 83488 |  |  |  | 0 |
| creator | gpt-5.5 | gpt-5.5 |  | NA | 114914 |  |  |  | 0 |
| creator | gemini-3.1-pro | Gemini 3.1 Pro (High) |  | NA | 0 |  |  |  | 0 |
| repair | gemini-3.1-pro | Gemini 3.1 Pro (High) |  | NA | 0 |  |  |  | 0 |
| creator | gemini-3.5-flash-high | Gemini 3.5 Flash (High) |  | NA | 0 |  |  |  | 0 |
| repair | gemini-3.5-flash-high | Gemini 3.5 Flash (High) |  | NA | 0 |  |  |  | 0 |
| creator | claude-opus | Claude Opus 4.6 Thinking |  | NA | 3535950 |  | 3324895 | 161955 | 0 |
| solver | gpt-5.2 | gpt-5.2 | 30 | 0/30 | 46870 |  |  |  | 0 |
| solver | gpt-5.2 | gpt-5.4 | 30 | 0/30 | 43440 |  |  |  | 0 |
| solver | gpt-5.2 | gpt-5.5 | 30 | 0/30 | 123532 |  |  |  | 0 |
| solver | gpt-5.2 | Gemini 3.1 Pro (High) | 30 | 0/30 | 0 |  |  |  | 0 |
| solver | gpt-5.2 | Gemini 3.5 Flash (High) | 30 | 0/30 | 0 |  |  |  | 0 |
| solver | gpt-5.2 | Claude Opus 4.6 Thinking | 30 | 0/30 | 735902 |  | 623200 | 79933 | 0 |
| solver | gpt-5.4 | gpt-5.2 | 30 | 27/30 | 46538 |  |  |  | 0 |
| solver | gpt-5.4 | gpt-5.4 | 30 | 30/30 | 179746 |  |  |  | 0 |
| solver | gpt-5.4 | gpt-5.5 | 30 | 27/30 | 71760 |  |  |  | 0 |
| solver | gpt-5.4 | Gemini 3.1 Pro (High) | 30 | 25/30 | 0 |  |  |  | 0 |
| solver | gpt-5.4 | Gemini 3.5 Flash (High) | 30 | 27/30 | 0 |  |  |  | 0 |
| solver | gpt-5.4 | Claude Opus 4.6 Thinking | 30 | 25/30 | 835891 |  | 624589 | 163954 | 0 |
| solver | gpt-5.5 | gpt-5.2 | 30 | 25/30 | 106889 |  |  |  | 0 |
| solver | gpt-5.5 | gpt-5.4 | 30 | 24/30 | 105193 |  |  |  | 0 |
| solver | gpt-5.5 | gpt-5.5 | 30 | 24/30 | 63937 |  |  |  | 0 |
| solver | gpt-5.5 | Gemini 3.1 Pro (High) | 30 | 23/30 | 0 |  |  |  | 0 |
| solver | gpt-5.5 | Gemini 3.5 Flash (High) | 30 | 24/30 | 0 |  |  |  | 0 |
| solver | gpt-5.5 | Claude Opus 4.6 Thinking | 30 | 24/30 | 543375 |  | 357264 | 149219 | 0 |
| solver | gemini-3.5-flash-high | gpt-5.2 | 30 | 4/30 | 47657 |  |  |  | 0 |
| solver | gemini-3.5-flash-high | gpt-5.4 | 30 | 23/30 | 217323 |  |  |  | 0 |
| solver | gemini-3.5-flash-high | gpt-5.5 | 30 | 15/30 | 63718 |  |  |  | 0 |
| solver | gemini-3.5-flash-high | Gemini 3.1 Pro (High) | 30 | 21/30 | 0 |  |  |  | 0 |
| solver | gemini-3.5-flash-high | Gemini 3.5 Flash (High) | 30 | 25/30 | 0 |  |  |  | 0 |
| solver | gemini-3.5-flash-high | Claude Opus 4.6 Thinking | 30 | 25/30 | 2682604 |  | 2340155 | 267121 | 0 |
| solver | claude-opus | gpt-5.2 | 30 | 30/30 | 26339 |  |  |  | 0 |
| solver | claude-opus | gpt-5.4 | 30 | 30/30 | 36387 |  |  |  | 0 |
| solver | claude-opus | gpt-5.5 | 30 | 30/30 | 73321 |  |  |  | 0 |
| solver | claude-opus | Gemini 3.1 Pro (High) | 30 | 30/30 | 0 |  |  |  | 0 |
| solver | claude-opus | Gemini 3.5 Flash (High) | 30 | 29/30 | 0 |  |  |  | 0 |
| solver | claude-opus | Claude Opus 4.6 Thinking | 30 | 30/30 | 320441 |  | 222385 | 88660 | 0 |
| solver | gemini-3.1-pro | gpt-5.2 | 30 | 1/30 | 28452 |  |  |  | 0 |
| solver | gemini-3.1-pro | gpt-5.4 | 30 | 26/30 | 60706 |  |  |  | 0 |
| solver | gemini-3.1-pro | gpt-5.5 | 30 | 26/30 | 47702 |  |  |  | 0 |
| solver | gemini-3.1-pro | Gemini 3.1 Pro (High) | 30 | 16/30 | 0 |  |  |  | 0 |
| solver | gemini-3.1-pro | Gemini 3.5 Flash (High) | 30 | 18/30 | 0 |  |  |  | 0 |
| solver | gemini-3.1-pro | Claude Opus 4.6 Thinking | 30 | 26/30 | 627730 |  | 551021 | 60551 | 0 |

Total reported tokens: `11047218`
