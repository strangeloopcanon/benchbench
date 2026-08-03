# Broad BenchBench Sweep

This run used the broad creator prompt: creators saw benchmark landscape notes and prior pilot outcomes, but were not directed toward any specific domain or modality.

Run root: `./experiments/011_gemini_provider_recovery_20260802`
Creator models: `gemini-3.6-flash-high`
Solver models: `gemini-3.6-flash-high`
Creator effort: `high`
Solver effort: `high`

Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.

## Benchmark Cards

### Gemini 3.6 Flash (High): state_machine_trace

- What it asks: A benchmark evaluating multi-step state machine execution, register tracking, and conditional flow logic.
- Answer/scoring: JSONL
- Creator-anticipated failure modes: This document outlines common failure modes exhibited by Large Language Models when attempting the `state_machine_trace` benchmark.
- Validation: `False`; bundle files: `0`; leak scan matches: `0`

## Solver Grid

| creator | benchmark | solver Gemini 3.6 Flash (High) | max score | status |
|---|---|---:|---:|---|
| Gemini 3.6 Flash (High) | state_machine_trace | NA | NA | incomplete_panel |

## Calls

| phase | creator | solver/model | rows | score | tokens | cost | cache read | cache write | returncode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| creator | gemini-3.6-flash-high | Gemini 3.6 Flash (High) |  | NA | 43368 |  |  |  | 77 |
| repair | gemini-3.6-flash-high | Gemini 3.6 Flash (High) |  | NA | 172310 |  |  |  | 0 |

Total reported tokens: `215678`
