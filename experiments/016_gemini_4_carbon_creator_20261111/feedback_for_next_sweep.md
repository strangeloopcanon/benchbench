# Feedback For Next BenchBench Sweep

This file is generated from the current creator/solver sweep state. After the final solver finishes, give it to the next creator models with `--feedback-context`.

BenchBench is evaluating benchmark invention. The goal is a complete benchmark package that is valid, reproducible, externally solvable in principle, and still hard after strong tool-enabled solvers attack the public solver bundle.

## Result Grid

| creator | benchmark | solver Gemini 4 Carbon (High) | solver Gemini 4 Argon (High) | solver gpt-6-sol | solver Claude Opus 5.5 (High) | solver GLM 5.2 (High) | max score | status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Gemini 4 Carbon (High) | HolonomyWeave | NA | NA | 30/30 | 30/30 | 30/30 | 30/30 | incomplete_panel |

## Benchmark Cards

These cards summarize what each prior benchmark actually asked, not just its name and score.

### Gemini 4 Carbon (High): HolonomyWeave

- What it asks: Parametric discrete gauge theory benchmark evaluating exact multi-sector parallel-transport shortest walks over finite abelian and non-abelian generalized dihedral fiber bundles D_M = Z_2 \|x Z_M on gauge-scrambled and potential-twisted directed weaves.
- Creator-anticipated failure modes: **HolonomyWeave** is engineered so that common heuristic shortcuts, algebraic misconceptions, and shallow graph-search approximations produce systematically wrong integer answers on specific holonomy queries. Every item packs three distinct holonomy-sector op...
- Validation: `True`; bundle files: `4`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: Gemini 4 Carbon (High): NA, Gemini 4 Argon (High): NA, gpt-6-sol: 30/30, Claude Opus 5.5 (High): 30/30, GLM 5.2 (High): 30/30
- Current read: `incomplete_panel`; max score `30/30`

## Lessons For The Next Creator

- Do not make a clean puzzle where the public packet exposes one obvious parser, simulator, BFS, or brute-force strategy.
- Do not rely on type strictness, hidden labels, private vocabulary, malformed output expectations, or missing public evidence to create low scores.
- Treat all-zero rows as audit warnings, not as automatic benchmark wins.
- Prefer complete but messy public evidence, closed answer contracts, adversarial edge cases, cross-document consistency, and partial recoverability.
- A candidate should be rejected if any strong solver gets 30/30, or if all strong solvers get 0/30 and the public bundle cannot prove external solvability.
