# Experiment 014 — Gemini 4 Argon

Gemini 4 Argon (`agy:gemini-4-argon-high`, evaluated in October 2026 under its pre-release Antigravity CLI alias `agy:halcyon`) was evaluated as both a blind solver against the validated packages from Experiments `010` and `013` and as a benchmark creator in Experiment `014`. Following a 1-line fix to replace a leaked format-example value in `solver_bundle/README.md`, its created benchmark (`maritime_general_average_forensics`) was also evaluated across all six Gemini and Claude models available via Antigravity (`Gemini 4 Argon`, `Gemini 3.8 Flash`, `Gemini 3.7 Flash`, `Gemini 3.6 Flash`, `Claude Opus 5.5`, and `Claude Sonnet 5.5`), as well as `GPT-6-Sol` via Codex and `GLM 5.2` via Cursor.

## Results

| creator | candidate | Gemini 3.6 Flash | Gemini 3.7 Flash | Gemini 3.8 Flash | Gemini 4 Argon | Claude Sonnet 5.5 | Claude Opus 5.5 | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Sol | AuditWeave | 30/30 | 30/30 | — | did not complete (timeout) | — | — | too easy on completed cells |
| Terra | Counterfactual Firewall Policy Synthesis | 30/30 | 30/30 | — | invalid_output (async subagent turn exit) | — | — | too easy on completed cells |
| Opus | Consolidation Point | 30/30 | 30/30 | — | 30/30 | — | — | too easy |
| Gemini 3.7 Flash | CloudSLA-Forensics | 30/30 | 30/30 | — | 30/30 | — | — | valid package, too easy |
| Gemini 4 Argon | maritime_general_average_forensics | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | repaired 1-line README leak; all 6 tested Antigravity solvers scored 30/30 |

## Solver Extensions (`010` and `013`)

- **CloudSLA-Forensics (`experiments/extensions/013_halcyon_solver_20261003`)**:
  Gemini 4 Argon solved all 30 items (`30/30`, `507,530` tokens) in a single synchronous turn, confirming that `CloudSLA-Forensics` saturates across `Gemini 3.6 Flash`, `Gemini 3.7 Flash`, and `Gemini 4 Argon`.
- **Consolidation Point (`experiments/extensions/010_halcyon_solver_20261003`)**:
  Gemini 4 Argon solved all 30 items (`30/30`, `116,231` tokens) in a single synchronous turn.
- **AuditWeave (`experiments/extensions/010_halcyon_solver_20261003`)**:
  Gemini 4 Argon spawned subagents inside `agy --print` and hit the 25-minute print timeout (`[agy] print timeout after 25m0s with turn in progress; returning partial output`, `478,796` tokens) with 0 prediction rows written. Because `agy` exits zero with `status="SUCCESS"` when `--print-timeout` interrupts an in-progress turn, `benchbench_model_backends.py` was updated so `--print-timeout` interruptions map to `returncode=-124` (`timeout`).
- **Counterfactual Firewall Policy Synthesis (`experiments/extensions/010_halcyon_solver_20261003`)**:
  Gemini 4 Argon spawned 6 parallel solver subagents via `invoke_subagent` and ended its parent turn (`num_turns=1`, `202,842` tokens) to wait for async subagent wakeups. In headless single-turn `agy --print` mode, ending the parent turn terminated the conversation stream before the subagents could return, leaving 0 prediction rows (`invalid_output`). Neither incomplete solver cell is treated as `0/30`.

## Creator Run & Solver Sweep (`014_halcyon_creator_20261003`)

In Experiment `014`, Gemini 4 Argon authored **`maritime_general_average_forensics` (MGAF)**, a 30-item forensic maritime average adjusting benchmark under the York-Antwerp Rules with multi-document manifests, survey logs, disbursement vouchers, FX/tariff schedules, and telex/email amendments.

- **Attempt 1 (`attempt_0001`)**: Timed out at the 40-minute creator print timeout (`returncode=-124`, `534,274` tokens) while writing the 30 case dossiers inside `generator.py`.
- **Attempt 2 (`attempt_0002`, automatic repair)**: Completed `generator.py`, `verifier.py`, `scorer.py`, `README.md`, `failure_modes.md`, and `validation_report.md` (`returncode=0`, `545,296` tokens). The package passed deterministic regeneration, frozen-package digest matching, controller positive gold control (`30/30`), controller shifted-wrong negative control (`0/30`), and the controller's string-based leak scan (`0` matches).
- **Initial Verifier Self-Rejection & 1-Line Placeholder Fix**: In the raw repair output, `solver_bundle/README.md` used `mgaf_01`'s real gold answer (`{"id": "mgaf_01", "answer": 1324550}`) in the output-format example, which the candidate's own 5-digit integer leak scanner in `verifier.py` flagged (`README.md:mgaf_01:1324550`, `returncode=1`). Replacing that single formatting example number with the synthetic placeholder `999999` in `generator.py` and `solver_bundle/README.md` left all 30 items and gold answers unchanged and passed `local_validate()` (`valid=true`, `deterministic=true`, `frozen_package_match=true`, `leak_match_count=0`).
- **Six-Model Antigravity Solver Sweep (`30/30` across all 6 models)**:
  - `experiments/extensions/014_halcyon_solver_20261003` (`Gemini 4 Argon`): **`30/30`** (`147,397` tokens)
  - `experiments/extensions/014_gemini_38_solver_20261003` (`Gemini 3.8 Flash (High)`): **`30/30`** (`312,719` tokens)
  - `experiments/extensions/014_gemini_37_solver_20261003` (`Gemini 3.7 Flash (High)`): **`30/30`** (`286,263` tokens)
  - `experiments/extensions/014_gemini_36_solver_20261003` (`Gemini 3.6 Flash (High)`): **`30/30`** (`291,777` tokens)
  - `experiments/extensions/014_claude_opus_55_solver_20261003` (`Claude Opus 5.5 (High)`): **`30/30`** (`136,982` tokens)
  - `experiments/extensions/014_claude_sonnet_55_solver_20261003` (`Claude Sonnet 5.5 (High)`): **`30/30`** (`110,991` tokens)
- **Cross-Provider Modern Frontier Sweep (`Codex` & `Cursor`, Python Enabled)**:
  - `experiments/extensions/014_codex_gpt_6_sol_solver_20261004` (`GPT-6-Sol (High)` via Codex): **`30/30`** (`67,947` tokens)
  - `experiments/extensions/014_cursor_opus_55_solver_20261004` (`Claude Opus 5.5 (High)` via Cursor): **`30/30`** (`216,684` reported tokens / `6,745` non-cache `in+out` tokens)
  - `experiments/extensions/014_cursor_glm_52_solver_20261004` (`GLM 5.2 (High)` via Cursor): **`30/30`** (`905,092` reported tokens / `67,652` non-cache `in+out` tokens; scored `24/30` when Python was disabled)
