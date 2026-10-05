## Reimbursement Forensics (ReiFor) v1

This BenchBench package defines a **document-based audit** benchmark.

Each item contains a small bundle of travel reimbursement evidence (policy excerpt, exchange-rate table, receipts, and a short email thread). Your job as a solver is to compute the **final reimbursable amount** in **USD cents** under the stated policy.

The benchmark is designed to be:
- **Externally solvable**: every answer is implied by the solver-visible documents.
- **Human-auditable**: each total can be recomputed by hand with care.
- **Hard for tool-enabled models**: success requires consistently applying many interacting rules across messy-but-finite evidence, with adversarial edge cases and cross-document consistency checks.

### What the solver must output

For each item `id`, output a JSONL line:

`{"id": "...", "answer": "<integer USD cents>"}`

Example: `{"id":"reifor_0007","answer":"18423"}`

### How to generate / verify / score (local)

All commands are run from this directory:

- Generate a 30-item private sample + solver bundle:
  - `<local-home>/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .`
- Verify gold is consistent with the solver-visible bundle:
  - `<local-home>/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`
- Score predictions:
  - `<local-home>/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

### Closest existing benchmarks (and why this is not a duplicate)

Closest families are **document understanding** (DocVQA-style), **tool-agent reasoning** (GAIA-style), and **audit/reconciliation** tasks.

This benchmark is not a near-duplicate because it emphasizes:
- cross-document rule application with explicit numerical outputs (not free-form QA),
- adversarially chosen policy edge cases (caps, exceptions, approvals, duplicates, missing fields),
- deterministic grading via an exact numeric total.
