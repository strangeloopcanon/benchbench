# HolonomyWeave Solver Bundle

This directory contains the self-contained solver inputs for **HolonomyWeave** (`holonomy_weave`).

## Contents

- `SOLVER_MANIFEST.json` - Bundle manifest and submission schema contract.
- `items_private_sample.jsonl` - 30 problem instances in JSON Lines format.
- `solver_packet.md` - Complete mathematical specification and worked toy example.

## Submission Format

Produce a UTF-8 JSON Lines file (e.g. `predictions.jsonl`) with one JSON object per item:

```json
{"id": "hw_001", "answer": 1200270035}
```

Rules:
1. Every `"id"` from `items_private_sample.jsonl` must appear once.
2. Each `"answer"` must be an exact base-10 integer (JSON integer, not float or boolean).
3. See `solver_packet.md` for the exact dihedral parallel-transport recurrence and packing formula.
