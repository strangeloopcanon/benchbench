# Feedback For Next BenchBench Sweep

This file is generated from the current creator/solver sweep state. After the final solver finishes, give it to the next creator models with `--feedback-context`.

BenchBench is evaluating benchmark invention. The goal is a complete benchmark package that is valid, reproducible, externally solvable in principle, and still hard after strong tool-enabled solvers attack the public solver bundle.

## Result Grid

| creator | benchmark | solver Gemini 3.7 Flash (High) | max score | status |
|---|---|---:|---:|---|
| Gemini 3.7 Flash (High) | CloudSLA-Forensics | 30/30 | 30/30 | reject |

## Benchmark Cards

These cards summarize what each prior benchmark actually asked, not just its name and score.

### Gemini 3.7 Flash (High): CloudSLA-Forensics

- What it asks: Forensic multi-document arbitration of enterprise cloud Service Level Agreement (SLA) breach claims. Solvers must analyze contracts, SLA schedules, incident telemetry logs, support tickets, RCA reports, maintenance notices, and billing statements to determine...
- Closest existing benchmarks: Reimbursement Forensics; GAIA; SWE-bench; Berkeley Function Calling Leaderboard
- Creator-anticipated failure modes: This document outlines the systematic failure modes and trap layers that punish one-pass heuristics, naive prompt-only LLM reasoning, and superficial scripting on CloudSLA-Forensics.
- Validation: `True`; bundle files: `259`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: Gemini 3.7 Flash (High): 30/30
- Current read: `reject`; max score `30/30`

## Lessons For The Next Creator

- Do not make a clean puzzle where the public packet exposes one obvious parser, simulator, BFS, or brute-force strategy.
- Do not rely on type strictness, hidden labels, private vocabulary, malformed output expectations, or missing public evidence to create low scores.
- Treat all-zero rows as audit warnings, not as automatic benchmark wins.
- Prefer complete but messy public evidence, closed answer contracts, adversarial edge cases, cross-document consistency, and partial recoverability.
- A candidate should be rejected if any strong solver gets 30/30, or if all strong solvers get 0/30 and the public bundle cannot prove external solvability.
