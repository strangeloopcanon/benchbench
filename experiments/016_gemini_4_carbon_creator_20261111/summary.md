# Broad BenchBench Sweep

This run used the broad creator prompt plus a prior-run failure report: creators saw benchmark landscape notes, prior pilot outcomes, and feedback on how the previous candidates broke.

Run root: `./experiments/016_gemini_4_carbon_creator_20261111`
Creator models: `gemini-4-carbon-high`
Solver models: `gemini-4-carbon-high, gemini-4-argon-high, gpt-6-sol, claude-opus-5-5-high, glm-5-2-high`
Creator effort: `high`
Solver effort: `high`
Creator feedback context: `./experiments/feedback_for_next_sweep_20261110.md`

Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.

## Benchmark Cards

### Gemini 4 Carbon (High): HolonomyWeave

- What it asks: Parametric discrete gauge theory benchmark evaluating exact multi-sector parallel-transport shortest walks over finite abelian and non-abelian generalized dihedral fiber bundles D_M = Z_2 \|x Z_M on gauge-scrambled and potential-twisted directed weaves.
- Creator-anticipated failure modes: **HolonomyWeave** is engineered so that common heuristic shortcuts, algebraic misconceptions, and shallow graph-search approximations produce systematically wrong integer answers on specific holonomy queries. Every item packs three distinct holonomy-sector op...
- Validation: `True`; bundle files: `4`; leak scan matches: `0`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Solver results: Gemini 4 Carbon (High): NA, Gemini 4 Argon (High): NA, gpt-6-sol: 30/30, Claude Opus 5.5 (High): 30/30, GLM 5.2 (High): 30/30
- Current read: `incomplete_panel`; max score `30/30`

## Solver Grid

| creator | benchmark | solver Gemini 4 Carbon (High) | solver Gemini 4 Argon (High) | solver gpt-6-sol | solver Claude Opus 5.5 (High) | solver GLM 5.2 (High) | max score | status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Gemini 4 Carbon (High) | HolonomyWeave | NA | NA | 30/30 | 30/30 | 30/30 | 30/30 | incomplete_panel |

## Calls

| phase | creator | solver/model | rows | score | tokens | cost | cache read | cache write | returncode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| creator | gemini-4-carbon-high | Gemini 4 Carbon (High) |  | NA | 253465 |  |  |  | 3 |
| repair | gemini-4-carbon-high | Gemini 4 Carbon (High) |  | NA | 441161 |  |  |  | 0 |
| solver | gemini-4-carbon-high | Gemini 4 Carbon (High) | None | NA | 20583 |  |  |  | 3 |
| solver | gemini-4-carbon-high | Gemini 4 Argon (High) | None | NA | 281565 |  |  |  | 78 |
| solver | gemini-4-carbon-high | gpt-6-sol | 30 | 30/30 | 23739 |  |  |  | 0 |
| solver | gemini-4-carbon-high | Claude Opus 5.5 (High) | 30 | 30/30 | 151656 |  | 118350 | 30617 | 0 |
| solver | gemini-4-carbon-high | GLM 5.2 (High) | 30 | 30/30 | 194357 |  | 167328 | 0 | 0 |

Total reported tokens: `1366526`

