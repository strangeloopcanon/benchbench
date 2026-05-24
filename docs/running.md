# Running BenchBench

This page keeps commands and backend notes out of the README.

## Challenger Sweep

Use a challenger sweep when a good candidate has been frozen and the next run
should search for something better.

Current incumbent: Reimbursement Forensics from Experiment 004.

Before using any new all-zero or low-scoring row as evidence, run the checks in
`experiments/audit_queue.md`.

The next challenger sweep gives creators the current feedback packet, skips
GPT-5.2 as a creator because its incumbent is frozen, and keeps the full
six-model solver panel:

```bash
BENCHBENCH_CLAUDE_MAX_BUDGET_USD=25 python run_broad_three_model_sweep.py \
  --feedback-context experiments/feedback_for_next_challenger_sweep_20260523.md \
  --creator-models gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high cursor:claude-opus \
  --solver-models gpt-5.2 gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high cursor:claude-opus
```

## Symmetric Sweep

Use `--models` when the creator and solver panels are the same:

```bash
python run_broad_three_model_sweep.py \
  --models gpt-5.2 gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high
```

For the default three-model sweep:

```bash
python run_broad_three_model_sweep.py
```

Each completed sweep writes:

- `summary.md`: run metadata, benchmark cards, solver grid, and call table.
- `feedback_for_next_sweep.md`: creator-ready grid, cards, and lessons.

## Historical Feedback Sweep

Experiment 004 was run by passing the Experiment 003 failure report as creator
context:

```bash
python run_broad_three_model_sweep.py \
  --feedback-context experiments/003_five_model_sweep_20260522_195526/feedback_for_next_sweep.md \
  --models gpt-5.2 gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high
```

Experiment 007 used the reconstructed 6x6 context:

```bash
BENCHBENCH_CLAUDE_MAX_BUDGET_USD=25 python run_broad_three_model_sweep.py \
  --feedback-context experiments/feedback_for_next_full_6x6_sweep_20260523.md \
  --models gpt-5.2 gpt-5.4 gpt-5.5 agy:gemini-3.1-pro agy:gemini-3.5-flash-high cursor:claude-opus
```

## Adding Solvers To Existing Runs

Keep existing benchmark packages fixed and add a solver column:

```bash
python run_existing_solver_extension.py --solver agy:gemini-3.5-flash-high
```

Gemini 3.1 Pro:

```bash
python run_existing_solver_extension.py --solver agy:gemini-3.1-pro
```

Claude Opus through Cursor:

```bash
python run_existing_solver_extension.py \
  --run-root experiments/004_feedback_sweep_20260522_225208 \
  --solver cursor:claude-opus
```

## Rebuild Published Result Artifacts

Regenerate the canonical grids, compatibility pointer, and SVG heatmaps from
saved score JSONs:

```bash
python scripts/build_6x6_result_artifacts.py
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
- Native Claude Code prompt caching is preserved by using print-mode calls and
  stdin prompts.

## Cursor Backend

BenchBench can use Cursor Agent for `cursor:` specs.

- `cursor:claude-opus` maps to Cursor model
  `claude-4.6-opus-high-thinking`, preserving comparability with the current
  Claude Opus 4.6 runs.
- `cursor:claude-opus-4.7-thinking-high` maps to Cursor model
  `claude-opus-4-7-thinking-high` if a newer Opus row is desired.
- Calls use `cursor-agent --print --output-format json --force --trust
  --sandbox disabled --workspace <run-dir>` and pass the prompt on stdin.
- Cursor JSON reports `usage.inputTokens`, `usage.outputTokens`,
  `usage.cacheReadTokens`, and `usage.cacheWriteTokens`; BenchBench records
  those fields in the manifest.

If Cursor is unavailable, the closest fallback for Claude Opus is
`agy:claude-opus-4.6-thinking`.

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
does not report Claude cost or cache-read tokens. Native Claude Code or Cursor
is better when telemetry matters.

## Similarity / Novelty Smoke Check

```bash
python scripts/score_benchmark_similarity.py \
  --target-benchmark benchbench_ignoresense \
  --out benchmark_landscape/similarity_ignoresense_smoke.md
```

The method is ready, but the current local solver set is still too small for a
serious regression novelty claim.
