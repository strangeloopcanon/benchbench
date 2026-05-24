# Construction Progress Payment Certification (CPPC)

A benchmark for evaluating the ability to translate multi-article contract
provisions into precise numerical computations. Each item presents a
construction subcontract payment application that requires cross-referencing
structured data with procedural rules, handling boundary conditions, and
performing multi-step arithmetic with intermediate per-line rounding.

## Capability Claim

CPPC measures whether a model can:
1. Parse a detailed rules document (General Conditions) with interacting articles
2. Apply conditional logic (retention thresholds, excusable delays, approval statuses)
3. Perform multi-step cumulative arithmetic with per-line rounding
4. Handle "all conditions must be met" gates (stored materials)
5. Correctly scope deductions and additions (insurance to work only, tax to materials only)

## Task Summary

For each of 30 items, compute the **certified payment amount in cents** for a
construction subcontract progress payment application by following the General
Conditions computation sequence (Article 13).

The answer is a single integer representing the payment amount in US cents.

## Package Structure

```
├── README.md                  (this file)
├── benchmark_spec.json        (metadata and design rationale)
├── generator.py               (deterministic item generation)
├── verifier.py                (recomputes answers from items)
├── scorer.py                  (scores predictions against gold)
├── gold_private_sample.jsonl  (30 gold answers — PRIVATE)
├── validation_report.md       (fairness and solvability proof)
├── failure_modes.md           (expected failure patterns)
├── baseline_naive.py          (weak baseline — 6/30)
├── baseline_almost.py         (nearly-correct baseline — 16/30)
└── solver_bundle/             (isolated solver package)
    ├── SOLVER_MANIFEST.json
    ├── solver_packet.md       (task instructions for solver)
    ├── general_conditions.md  (contract rules document)
    └── items_private_sample.jsonl (30 items)
```

## CLI Contract

```bash
# Generate items
python generator.py --sample-count 30 --seed 20260516 --out-dir .

# Verify consistency
python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl

# Score predictions
python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

## Closest Existing Benchmarks

- **Reimbursement Forensics** (BenchBench internal): Both compute exact amounts
  from policy + evidence. CPPC differs by using cumulative AIA G702 methodology,
  per-line rounding, multi-tier retention, and change order status hierarchies.
- **GAIA**: Both require multi-step tool-assisted reasoning. CPPC is narrower
  (single domain, deterministic rules) but deeper (15-step computation with
  interacting conditions).

## Difficulty Calibration

| Baseline | Score | Description |
|----------|-------|-------------|
| Gold (perfect) | 30/30 | All rules implemented correctly |
| Almost-correct | 16/30 | Misses only the retention threshold rule |
| Naive | 6/30 | Ignores CO status, stored conditions, retention, insurance, tax |

The benchmark targets the 10–20/30 range for strong tool-enabled models, where
partial scores come from getting easy items correct while failing on items with
active edge cases.
