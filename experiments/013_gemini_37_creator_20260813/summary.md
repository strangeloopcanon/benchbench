# Broad BenchBench Sweep

This run used the broad creator prompt plus a prior-run failure report: creators saw benchmark landscape notes, prior pilot outcomes, and feedback on how the previous candidates broke.

Run root: `./experiments/013_gemini_37_creator_20260813`
Creator models: `gemini-3.7-flash-high`
Solver models: `gemini-3.7-flash-high`
Creator effort: `high`
Solver effort: `high`
Creator feedback context: `./experiments/feedback_for_next_full_6x6_sweep_20260523.md`

Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.

## Benchmark Cards

### Gemini 3.7 Flash (High): CloudSLA-Forensics

- What it asks: Forensic multi-document arbitration of enterprise cloud Service Level Agreement (SLA) breach claims. Solvers must analyze contracts, SLA schedules, incident telemetry logs, support tickets, RCA reports, maintenance notices, and billing statements to determine...
- Closest existing benchmarks: Reimbursement Forensics; GAIA; SWE-bench; Berkeley Function Calling Leaderboard
- Creator-anticipated failure modes: This document outlines the systematic failure modes and trap layers that punish one-pass heuristics, naive prompt-only LLM reasoning, and superficial scripting on CloudSLA-Forensics.
- Validation: `True`; bundle files: `259`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: Gemini 3.7 Flash (High): 30/30
- Current read: `reject`; max score `30/30`

## Solver Grid

| creator | benchmark | solver Gemini 3.7 Flash (High) | max score | status |
|---|---|---:|---:|---|
| Gemini 3.7 Flash (High) | CloudSLA-Forensics | 30/30 | 30/30 | reject |

## Calls

| phase | creator | solver/model | rows | score | tokens | cost | cache read | cache write | returncode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| creator | gemini-3.7-flash-high | Gemini 3.7 Flash (High) |  | NA | 209534 |  |  |  | 0 |
| solver | gemini-3.7-flash-high | Gemini 3.7 Flash (High) | 30 | 30/30 | 335375 |  |  |  | 0 |

Total reported tokens: `544909`

