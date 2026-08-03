# Solver Bundle for state_machine_trace

This bundle contains the public solver packet for the `state_machine_trace` benchmark.

## Files
- `items_private_sample.jsonl`: Contains the problem prompts and metadata without ground-truth solutions.
- `SOLVER_MANIFEST.json`: Manifest metadata describing the solver bundle contents.

## Output Contract
Solvers must output predictions in JSONL format, where each line contains:
```json
{"item_id": "item_001", "prediction": "{\"R0\": 10, \"R1\": -5, \"R2\": 0, \"R3\": 12}"}
```
or with integer register dict as `prediction`.
