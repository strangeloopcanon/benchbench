# Running BenchBench

This page keeps the commands and backend details out of the README.

## Fresh Sweep

Run the default three-model sweep:

```bash
python run_broad_three_model_sweep.py
```

The creator prompt reads `benchmark_landscape/creator_prompt_landscape_pack.md`
when present, plus the Experiment 001 pilot summary.

Each completed sweep writes:

- `summary.md`: run metadata, benchmark cards, solver grid, and call table.
- `feedback_for_next_sweep.md`: a creator-ready feedback packet with the solver
  grid, benchmark cards, and next-run lessons.

## Five-Model GPT/Gemini Sweep

```bash
python run_broad_three_model_sweep.py \
  --models gpt-5.2 gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high
```

## Feedback Sweep

Pass a prior failure report as creator context:

```bash
python run_broad_three_model_sweep.py \
  --feedback-context experiments/003_five_model_sweep_20260522_195526/feedback_for_next_sweep.md \
  --models gpt-5.2 gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high
```

For the next full all-model run, use the current 6x6 feedback packet:

```bash
BENCHBENCH_CLAUDE_MAX_BUDGET_USD=25 python run_broad_three_model_sweep.py \
  --feedback-context experiments/feedback_for_next_full_6x6_sweep_20260523.md \
  --models gpt-5.2 gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high claude:opus
```

## Adding Solvers To Existing Runs

Keep existing benchmark packages fixed and add a new solver column:

```bash
python run_existing_solver_extension.py --solver agy:gemini-3.5-flash-high
```

Gemini 3.1 Pro:

```bash
python run_existing_solver_extension.py --solver agy:gemini-3.1-pro
```

Claude Sonnet on the feedback sweep:

```bash
BENCHBENCH_CLAUDE_MAX_BUDGET_USD=25 python run_existing_solver_extension.py \
  --run-root experiments/004_feedback_sweep_20260522_225208 \
  --solver claude:sonnet
```

## Claude Code Backend

BenchBench uses native Claude Code calls for `claude:` specs.

- `claude:sonnet`, `claude:opus`, and `claude:haiku` map to
  `claude -p --model ... --output-format json`.
- The runner writes the JSON `result` field to the normal output file and
  keeps the full Claude JSON in the `.stdout.txt` sidecar.
- Claude JSON reports `total_cost_usd`, `modelUsage`, cache creation tokens,
  and cache read tokens. BenchBench records those fields in manifests and
  summary tables.
- `BENCHBENCH_CLAUDE_MAX_BUDGET_USD` caps each Claude Code call. The default is
  `$25` per call unless overridden.
- Native Claude Code prompt caching is preserved by using normal print-mode
  calls and stdin prompts.
- The creator prompt keeps large stable context before volatile artifact paths
  so repeated Claude creator calls can reuse more of the prefix cache.

## Antigravity Backend

`agy --print` works for non-interactive creator and solver calls.

BenchBench makes specific Antigravity calls by temporarily setting
`~/.gemini/antigravity-cli/settings.json` for one `agy --print` call, then
restoring the original settings file. The runner verifies the selected model
label in the Antigravity log before accepting the result.

Supported labels in the current runner:

- `agy:gemini-3.1-pro` selects `Gemini 3.1 Pro (High)`.
- `agy:gemini-3.5-flash-high` selects `Gemini 3.5 Flash (High)`.
- `agy:claude-sonnet-4.6-thinking` selects `Claude Sonnet 4.6 (Thinking)`.
- `agy:claude-opus-4.6-thinking` selects `Claude Opus 4.6 (Thinking)`.

Antigravity Claude is usable for grid parity, but the current Antigravity path
does not report Claude `total_cost_usd` or cache-read tokens. Native Claude
Code is the better path when cost and caching telemetry matter.

Antigravity terminal tools open in a global scratch directory by default, so
creator and solver prompts include the exact artifact or isolated bundle path
and instruct the model to use that path for all file and shell work.

## Similarity / Novelty Smoke Check

```bash
python scripts/score_benchmark_similarity.py \
  --target-benchmark benchbench_ignoresense \
  --out benchmark_landscape/similarity_ignoresense_smoke.md
```

The method is ready, but the current local solver set is too small for serious
regression novelty claims.
