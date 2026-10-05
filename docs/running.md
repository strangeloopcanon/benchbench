# Running BenchBench

The current registry has no validated incumbent. Reimbursement Forensics is the
#1 corrected historical candidate and the target to beat, but its original
gold is invalid and the package is not a reusable incumbent. New comparisons
must be written to a new run root and must complete the current validation and
adjudication gates.

## Install The Locked Environment

BenchBench supports Python 3.11 and 3.12. Install exactly the versions in
`uv.lock`:

```bash
python -m pip install uv==0.8.15
uv sync --frozen --all-groups
uv run pytest -q
```

CI runs the same locked install, compile check, and test suite on macOS because
the execution boundary depends on macOS Seatbelt.

## Frontier Panel Preflight

The default panel uses the exact locally advertised provider IDs below. The
`@effort` suffix is BenchBench's per-model override; it is removed before the
model ID is passed to the provider CLI. (`agy:halcyon` maps to the
local Antigravity CLI target `halcyon`, which does not accept an `--effort`
flag.)

| requested panel member | BenchBench spec | provider catalog ID | effective effort |
|---|---|---|---|
| Codex GPT-5.6 Sol high | `gpt-5.6-sol@high` | `gpt-5.6-sol` | `high` |
| Codex GPT-5.6 Terra extra high | `gpt-5.6-terra@xhigh` | `gpt-5.6-terra` | `xhigh` |
| Gemini 3.6 Flash | `agy:gemini-3.6-flash-high@high` | `gemini-3.6-flash-high` | `high` |
| Gemini 3.7 Flash | `agy:gemini-3.7-flash-high@high` | `gemini-3.7-flash-high` | `high` |
| Halcyon | `agy:halcyon@high` | `halcyon` | `high` (CLI flag omitted) |
| Claude Opus 5 | `cursor:claude-opus-5@high` | `claude-opus-5-thinking-high` | `high` |

Run this setup-only check before any experiment. It inspects CLI help and model
catalogs without submitting an inference prompt or creating a run directory:

```bash
uv run python run_broad_three_model_sweep.py \
  --preflight-only
```

The preflight uses each provider's non-inference catalog. A fully ready result
reports `model_available: true` for all six exact IDs. It never submits a creator or
solver prompt and never creates a run root. Codex catalog lookup uses its live
boundary; Antigravity and Cursor catalog checks are explicitly recorded as
`ambient_catalog_only` and do not prove live credential containment. Contained
live canaries established Antigravity's runtime labels as
`Gemini 3.6 Flash (High)`, `Gemini 3.7 Flash (High)`, and `Halcyon`; live
calls must match the label for the exact requested ID.

## Live Run Boundary

Antigravity has an audited live boundary. The Codex path fails closed whenever
the parent-environment isolation probe is unavailable; that probe currently
fails on this macOS runtime, so no Codex call is dispatched here. Cursor remains
available for non-inference catalog preflight, but live Cursor execution is
disabled because its native authentication token is inherited by model-created
terminal tools. A full frontier sweep must restore the Codex boundary and
use a token-free Cursor tool environment or another audited Opus provider.

The currently runnable audited panel is Antigravity-only. After choosing an
explicit total-token ceiling, run:

```bash
TOKEN_CEILING=20000000 \
uv run python run_broad_three_model_sweep.py \
  --run-root experiments/custom_audited_panel_YYYYMMDD_HHMMSS \
  --models agy:gemini-3.6-flash-high@high agy:gemini-3.7-flash-high@high agy:halcyon@high \
  --max-total-tokens "$TOKEN_CEILING" \
  --zero-telemetry-reservation 5000000 \
  --allow-dispatch-ceiling-overshoot \
  --allow-unmetered-cost
```

`--max-total-tokens` stops the controller before starting another call once
reported usage plus zero-telemetry reservations reaches the ceiling. Provider CLIs do not offer a uniform hard
per-call token limit, so the ceiling cannot interrupt an already-running call.
`--allow-dispatch-ceiling-overshoot` makes that operator approval explicit and
is required for every live run.
The 20,000,000 example is grounded in the historical runs: a 5,000,000
whole-run cap is too small because one successful Opus creator call reported
6,011,630 tokens, and an earlier sweep reported more than 11 million tokens in
total. The operator must still approve the ceiling explicitly.
If an attempted call reports zero token telemetry, the controller charges the
configured reservation instead of treating the unknown usage as free. The
default reservation is 5,000,000 tokens. New calls continue only while the
reported-plus-reserved total remains below the dispatch ceiling.
Creator and solver timeouts bound wall time. Codex does not report a
harness-enforced dollar cap, which is why its live run requires the explicit
`--allow-unmetered-cost` acknowledgement.

Each run records the model/effort identities, harness and prompt-input digests,
timeouts, token ceiling, call evidence, candidate attempt lineage, typed cell
states, and normalized score records. A failed creator repair becomes a second
immutable attempt; a failed solver never becomes a numeric zero.

Every new run root also contains `source_snapshot/`: an allowlisted copy of the
controller Python modules, package configuration, requirements, and `uv.lock`
used to start that run. `source_snapshot/manifest.json` records each file hash
and the bundle digest; `run_state.json` binds that digest to the run. The
snapshot deliberately excludes credentials, provider state, experiment trees,
and other external/private state.

## Provider Boundary

Live creator and solver calls are enabled for Codex and Antigravity. Cursor
Agent and the direct Claude Code adapter remain preflight-only until they have
audited credential boundaries.

Codex runs inside one outer macOS Seatbelt boundary. A second provider-native
Seatbelt profile cannot be nested on macOS, so the CLI is told
`danger-full-access` inside that already-restricted process. This is not host
access: the outer profile permits reads from the disposable workspace and a
randomized empty provider home, denies the repository and process-table
inspection, explicitly blocks the `KERN_PROCARGS2` parent-environment channel,
explicitly blocks legacy `KERN_PROCARGS` as well, and strips the controller
environment. No `auth.json` is copied.
The trusted Codex parent receives only a current bearer token and account ID;
its command-backed provider reads that token from the parent environment.
Model-created shells inherit none of the provider environment, so running the
same broker command returns no credential. Refresh tokens, Codex history,
memories, configuration, hooks, plugins, and sessions never enter the boundary.
If brokering or containment fails, the call fails closed.

Cursor 2026.07.23 cannot start its shell sandbox reliably under the outer macOS
Seatbelt profile. Disabling the inner sandbox makes shell tools work but exposes
`CURSOR_AUTH_TOKEN` to model-created commands. The harness therefore rejects
all live Cursor calls before loading a credential. Treat the two affected
Experiment 010 cells as did-not-complete.

Antigravity receives its existing OAuth session through a one-shot FIFO at the
path expected under its disposable home. The pathname is removed immediately
after the provider opens it, and the outer profile denies recreating or
refreshing that credential path. A disposable `settings.json` grants file
access only to the run workspace and pre-approves headless commands. Terminal
commands may bypass Antigravity's conflicting inner macOS sandbox, but they
remain inside the mandatory outer Seatbelt profile. The global Antigravity
settings are never copied or changed. Its JSON result supplies exact token usage,
and its runtime log must confirm the selected friendly model label when one is
known. Neither provider can read the repository, private gold, broad home
state, or ambient controller secrets.

## Extend A Historical Benchmark Safely

An extension is a new experiment overlay. The source package remains
byte-for-byte unchanged:

```bash
uv run python run_existing_solver_extension.py \
  --source-run-root experiments/008_fable_creator_sweep_20260610_085405 \
  --output-root experiments/extensions/009_fable_sol_high_YYYYMMDD_HHMMSS \
  --solver gpt-5.6-sol \
  --effort high \
  --max-total-tokens 150000 \
  --allow-dispatch-ceiling-overshoot \
  --zero-telemetry-reservation 5000000 \
  --allow-unmetered-cost
```

To retry a source cell already typed as `invalid_output`, `timeout`, or another
failed state, add `--retry-failed-source-cells`. The retry is still published
only to a new overlay and is rejected if successful source evidence already
exists.

To add a newly released solver that was not in the source run's declared
panel, add `--allow-panel-expansion`. The new solver identity and the explicit
panel expansion are recorded in the overlay configuration; source artifacts
and existing cells remain unchanged.

Versioned frontier-four and frontier-five source runs are accepted by default.
To extend a mechanically validated custom source run, also pass
`--allow-custom-source-panel`; that acknowledgement and the source policy are
recorded in the overlay.

Extensions charge a zero-telemetry timeout or provider failure against the
declared reservation instead of treating it as free or blocking unrelated
remaining cells. Each overlay freezes its controller source and copies source
candidates without mutating the original experiment.

Use `--preflight-only` first. The live command copies each selected benchmark
package into the new output root, excludes old predictions and scores, and
publishes new evidence only in the overlay.

## Prepare Evidence For A Public Commit

Raw provider transcripts stay local and are ignored by Git. Before publishing
new frontier-panel evidence, sanitize machine-specific paths, replace private
transcript references, and rebind the dependent integrity graph:

```bash
uv run python scripts/prepare_public_evidence.py
uv run pytest -q
```

The sanitizer is idempotent. It keeps benchmark packages, validation records,
predictions, scores, manifests, and run-state evidence, while the raw prompts,
stdout, stderr, and provider logs remain unpublished.

## Rebuild Canonical Status

Canonical artifacts derive from `experiments/registry.v1.json`:

```bash
uv run python scripts/build_6x6_result_artifacts.py
```

The builder verifies registry evidence digests and refuses to promote a
candidate unless it is marked `validated`, is explicitly eligible, passes its
mechanical gate, and has a complete all-success solver panel.

## Similarity Check

```bash
uv run python scripts/score_benchmark_similarity.py \
  --target-benchmark benchbench_ignoresense \
  --out benchmark_landscape/similarity_ignoresense_smoke.md
```

Historical experiments 001 and 002 are explicitly allowed into the landscape
as noncanonical diagnostic data. Their small solver overlap supports smoke
checks only, not a serious novelty claim.
