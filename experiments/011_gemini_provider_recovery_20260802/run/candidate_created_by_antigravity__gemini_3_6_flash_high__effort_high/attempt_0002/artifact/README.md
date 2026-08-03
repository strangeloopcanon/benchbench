# State Machine Trace Benchmark (`state_machine_trace`)

## Overview

The `state_machine_trace` benchmark evaluates the ability of language models and autonomous agents to accurately execute multi-step deterministic register state machines. Each task provides an initial state vector for registers `(R0, R1, R2, R3)` and a series of sequential assembly-like instructions (e.g., `SET`, `ADD`, `SUB`, `MUL`, `MOD`, and conditional `IF...THEN...ELSE`). The model must track register states accurately across all steps and output the final register map in JSON format.

## Benchmark Structure

- `generator.py`: Generates the private evaluation dataset (`gold_private_sample.jsonl`) and solver bundle (`solver_bundle/`).
- `verifier.py`: Validates the structure and compliance of solver submission JSONL files.
- `scorer.py`: Evaluates solver predictions against gold ground truth, outputting `schema_version: 2`, `total`, `correct`, and `accuracy`.
- `gold_private_sample.jsonl`: Private dataset containing initial prompts and ground truth register values.
- `solver_bundle/`: Isolated packet for solvers containing `items_private_sample.jsonl` (prompts without ground truth answers), `SOLVER_MANIFEST.json`, and `README.md`.

## Solvability Evidence & Baseline Performance

- **Gold Ground-Truth Reference Solver**: Executes exact simulator state machine logic step-by-step. Achieves **30/30 (100.0% Accuracy)**.
- **Shifted / Incorrect Baseline**: Returns mismatched predictions. Achieves **0/30 (0.0% Accuracy)**.

## Usage Commands

### 1. Dataset Generation
```bash
python3 generator.py --sample-count 30 --seed 20260516 --out-dir .
```

### 2. Submission Verification
```bash
python3 verifier.py --items solver_bundle/items_private_sample.jsonl --submission submission.jsonl --out verification.json
```

### 3. Submission Scoring
```bash
python3 scorer.py --gold gold_private_sample.jsonl --submission submission.jsonl --out score.json
```
