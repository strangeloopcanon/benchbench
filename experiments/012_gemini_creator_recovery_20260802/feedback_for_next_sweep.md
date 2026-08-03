# Feedback For Next BenchBench Sweep

This file is generated from the current creator/solver sweep state. After the final solver finishes, give it to the next creator models with `--feedback-context`.

BenchBench is evaluating benchmark invention. The goal is a complete benchmark package that is valid, reproducible, externally solvable in principle, and still hard after strong tool-enabled solvers attack the public solver bundle.

## Result Grid

| creator | benchmark | solver Gemini 3.6 Flash (High) | max score | status |
|---|---|---:|---:|---|
| Gemini 3.6 Flash (High) | RADN-Sim | NA | NA | incomplete_panel |

## Benchmark Cards

These cards summarize what each prior benchmark actually asked, not just its name and score.

### Gemini 3.6 Flash (High): RADN-Sim

- What it asks: **Creator**: Gemini 3.6 Flash (High) + Antigravity **Domain**: Cycle-Accurate Microarchitecture & Dataflow State Machine Simulation **Modality**: Code / Algorithmic Verification **Scoring**: Deterministic Exact Match on SHA-256 Digest of Canonical Simulation....
- Intended capability: Structured Code & Algorithmic Trace Logic
- Creator-anticipated failure modes: This document outlines the primary failure modes, algorithmic traps, and specification edge cases that cause AI models, LLM agents, and naive software baseline solvers to fail on the **RADN-Sim** benchmark.
- Validation: `False`; bundle files: `0`; leak scan matches: `0`

## Lessons For The Next Creator

- Do not make a clean puzzle where the public packet exposes one obvious parser, simulator, BFS, or brute-force strategy.
- Do not rely on type strictness, hidden labels, private vocabulary, malformed output expectations, or missing public evidence to create low scores.
- Treat all-zero rows as audit warnings, not as automatic benchmark wins.
- Prefer complete but messy public evidence, closed answer contracts, adversarial edge cases, cross-document consistency, and partial recoverability.
- A candidate should be rejected if any strong solver gets 30/30, or if all strong solvers get 0/30 and the public bundle cannot prove external solvability.
