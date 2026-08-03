# Feedback For Next BenchBench Sweep

This file is generated from the current creator/solver sweep state. After the final solver finishes, give it to the next creator models with `--feedback-context`.

BenchBench is evaluating benchmark invention. The goal is a complete benchmark package that is valid, reproducible, externally solvable in principle, and still hard after strong tool-enabled solvers attack the public solver bundle.

## Result Grid

| creator | benchmark | solver Gemini 3.6 Flash (High) | max score | status |
|---|---|---:|---:|---|
| Gemini 3.6 Flash (High) | state_machine_trace | NA | NA | incomplete_panel |

## Benchmark Cards

These cards summarize what each prior benchmark actually asked, not just its name and score.

### Gemini 3.6 Flash (High): state_machine_trace

- What it asks: A benchmark evaluating multi-step state machine execution, register tracking, and conditional flow logic.
- Answer/scoring: JSONL
- Creator-anticipated failure modes: This document outlines common failure modes exhibited by Large Language Models when attempting the `state_machine_trace` benchmark.
- Validation: `False`; bundle files: `0`; leak scan matches: `0`

## Lessons For The Next Creator

- Do not make a clean puzzle where the public packet exposes one obvious parser, simulator, BFS, or brute-force strategy.
- Do not rely on type strictness, hidden labels, private vocabulary, malformed output expectations, or missing public evidence to create low scores.
- Treat all-zero rows as audit warnings, not as automatic benchmark wins.
- Prefer complete but messy public evidence, closed answer contracts, adversarial edge cases, cross-document consistency, and partial recoverability.
- A candidate should be rejected if any strong solver gets 30/30, or if all strong solvers get 0/30 and the public bundle cannot prove external solvability.
