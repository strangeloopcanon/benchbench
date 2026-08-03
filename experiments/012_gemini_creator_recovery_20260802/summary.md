# Broad BenchBench Sweep

This run used the broad creator prompt: creators saw benchmark landscape notes and prior pilot outcomes, but were not directed toward any specific domain or modality.

Run root: `./experiments/012_gemini_creator_recovery_20260802`
Creator models: `gemini-3.6-flash-high`
Solver models: `gemini-3.6-flash-high`
Creator effort: `high`
Solver effort: `high`

Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.

## Benchmark Cards

### Gemini 3.6 Flash (High): RADN-Sim

- What it asks: **Creator**: Gemini 3.6 Flash (High) + Antigravity **Domain**: Cycle-Accurate Microarchitecture & Dataflow State Machine Simulation **Modality**: Code / Algorithmic Verification **Scoring**: Deterministic Exact Match on SHA-256 Digest of Canonical Simulation....
- Intended capability: Structured Code & Algorithmic Trace Logic
- Creator-anticipated failure modes: This document outlines the primary failure modes, algorithmic traps, and specification edge cases that cause AI models, LLM agents, and naive software baseline solvers to fail on the **RADN-Sim** benchmark.
- Validation: `False`; bundle files: `0`; leak scan matches: `0`

## Solver Grid

| creator | benchmark | solver Gemini 3.6 Flash (High) | max score | status |
|---|---|---:|---:|---|
| Gemini 3.6 Flash (High) | RADN-Sim | NA | NA | incomplete_panel |

## Calls

| phase | creator | solver/model | rows | score | tokens | cost | cache read | cache write | returncode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| creator | gemini-3.6-flash-high | Gemini 3.6 Flash (High) |  | NA | 356353 |  |  |  | 0 |
| repair | gemini-3.6-flash-high | Gemini 3.6 Flash (High) |  | NA | 200760 |  |  |  | 0 |

Total reported tokens: `557113`
