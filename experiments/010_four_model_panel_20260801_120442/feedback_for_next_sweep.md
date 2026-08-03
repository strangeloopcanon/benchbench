# Feedback For Next BenchBench Sweep

This file is generated from the current creator/solver sweep state. After the final solver finishes, give it to the next creator models with `--feedback-context`.

BenchBench is evaluating benchmark invention. The goal is a complete benchmark package that is valid, reproducible, externally solvable in principle, and still hard after strong tool-enabled solvers attack the public solver bundle.

## Result Grid

| creator | benchmark | solver gpt-5.6-sol | solver gpt-5.6-terra | solver Gemini 3.6 Flash (High) | solver Claude Opus 5 Thinking (High) | max score | status |
|---|---|---:|---:|---:|---:|---:|---|
| gpt-5.6-sol | AuditWeave | 30/30 | 30/30 | NA | NA | 30/30 | incomplete_panel |
| gpt-5.6-terra | Counterfactual Firewall Policy Synthesis | NA | NA | NA | NA | NA | incomplete_panel |
| Gemini 3.6 Flash (High) | artifact | NA | NA | NA | NA | NA | incomplete_panel |
| Claude Opus 5 Thinking (High) | Consolidation Point | NA | NA | NA | NA | NA | incomplete_panel |

## Benchmark Cards

These cards summarize what each prior benchmark actually asked, not just its name and score.

### gpt-5.6-sol: AuditWeave

- What it asks: AuditWeave measures whether a solver can reconstruct a corrupted event in a partially ordered log from lossy checkpoint audits, then execute a counterfactual query on every feasible reconstruction. It targets a useful hybrid capability: exact specification fo...
- Intended capability: Measures exact abductive reconstruction and counterfactual execution of a formally specified state machine under partial-order and lossy-audit evidence.
- Answer/scoring: exact item-level match
- Creator-anticipated failure modes: The language is synthetic and tests formal reconstruction rather than domain knowledge. Exact-match scoring gives no partial credit. The included sample has not yet been calibrated across a broad model panel, so difficulty claims are based on structural basel...
- Validation: `True`; bundle files: `3`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: gpt-5.6-sol: 30/30, gpt-5.6-terra: 30/30, Gemini 3.6 Flash (High): NA, Claude Opus 5 Thinking (High): NA
- Current read: `incomplete_panel`; max score `30/30`

### gpt-5.6-terra: Counterfactual Firewall Policy Synthesis

- What it asks: Choose a minimum-cost permission-revocation set that keeps all services operational and blocks all attacks.
- Intended capability: Faithful executable modeling and exact optimization of compositional access-policy constraints.
- Answer/scoring: {"kind": "deterministic exact item-level match", "primary_metric": "accuracy", "report_schema_version": 2}
- Creator-anticipated failure modes: The instances are finite, static, monotone Boolean policy models. They do not claim to simulate real authorization systems, network topology, temporal access, probabilistic risk, or adversarial adaptation. CFPS measures formal policy synthesis under its state...
- Validation: `True`; bundle files: `3`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`

### Gemini 3.6 Flash (High): artifact

- Validation: `False`; bundle files: `0`; leak scan matches: `0`

### Claude Opus 5 Thinking (High): Consolidation Point

- What it asks: A benchmark for **time-indexed normative reasoning**: can a solver work out what a rule actually said *for a particular event*, when the rule has been amended eleven times and the amendments do not agree about when they bite?
- Intended capability: Time-indexed normative reasoning: given a base enactment plus a chronological stack of textual amending instruments, each with its own commencement rule and its own separate application rule, reconstruct the operative rule set for a specified event and apply...
- Answer/scoring: a single whole number of marks, digits only - integer
- Closest existing benchmarks: {"benchmark": "IFEval / tau-bench", "difference": "those supply one static policy; here the rule set is a stack of dated diffs and the central difficulty is deciding which version of the rule governs a given event, which neither benchmark exercises", "similarity": "both measure adherence to an explicitly supplied rule set"}; {"benchmark": "MuSR", "differenc...
- Creator-anticipated failure modes: Three sections: ways the benchmark itself could be wrong, ways a solver is expected to fail, and ways the package could break operationally.
- Validation: `True`; bundle files: `5`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`

## Lessons For The Next Creator

- Do not make a clean puzzle where the public packet exposes one obvious parser, simulator, BFS, or brute-force strategy.
- Do not rely on type strictness, hidden labels, private vocabulary, malformed output expectations, or missing public evidence to create low scores.
- Treat all-zero rows as audit warnings, not as automatic benchmark wins.
- Prefer complete but messy public evidence, closed answer contracts, adversarial edge cases, cross-document consistency, and partial recoverability.
- A candidate should be rejected if any strong solver gets 30/30, or if all strong solvers get 0/30 and the public bundle cannot prove external solvability.
