# Validation & Solvability Report for `state_machine_trace`

## Executive Summary

The `state_machine_trace` benchmark package has been fully validated against all BenchBench candidate specifications. All root files, solver bundle artifacts, CLI contracts, deterministic generation pipelines, and verification / scoring standards have passed validation checks.

## 1. Deterministic Payload Generation

- **Command**: `python3 generator.py --sample-count 30 --seed 20260516 --out-dir .`
- **Result**: Identical SHA-256 digests produced across multiple independent generation runs:
  - `gold_private_sample.jsonl`: `bcb3671d2ee9a85a56c2a5c0957160d0800b1cfc9dbca1059784bb46fc9ab783`
  - `solver_bundle/items_private_sample.jsonl`: `2e679477cec83ed3cdcc7504b17d261b4773a04780c5087154ddd911d1441bc9`

## 2. Solver Bundle Isolation & Leak Scan

- **Target File**: `solver_bundle/items_private_sample.jsonl`
- **Scan Method**: Automated key inspection for ground-truth fields (`target`, `gold_registers`, `expected_output`).
- **Result**: `0` ground-truth leaks found. Ground truth is strictly restricted to `gold_private_sample.jsonl` in root.

## 3. Solvability Evidence

| Model / Controller Baseline | Total Items | Correct Items | Accuracy | Status |
|-----------------------------|-------------|---------------|----------|--------|
| **Gold Ground Truth Solver** | 30          | 30            | 1.000 (100%) | Passed |
| **Shifted / Wrong Solver**   | 30          | 0             | 0.000 (0%)   | Passed |

## 4. CLI & Schema Contracts

- `verifier.py`: Accepts `--items`, `--submission`, `--out`, and positional arguments. Returns valid JSON with `"valid": true` for well-formed submissions.
- `scorer.py`: Conforms to `schema_version: 2`. Outputs integer `total`, integer `correct`, and numeric `accuracy` (`correct / total`). Custom score keys do not override required schema fields.
