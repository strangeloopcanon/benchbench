# CloudSLA-Forensics

**Cloud Infrastructure SLA Breach & Service Credit Forensic Arbitration Benchmark**

## Overview
**CloudSLA-Forensics** is a benchmark designed to evaluate frontier AI agents and tool-enabled reasoning systems on complex, realistic, multi-document forensic contract arbitration. 

In real-world enterprise cloud operations, resolving SLA credit claims requires cross-referencing legal agreements, incident telemetry, ticket correspondence, maintenance notices, root cause analysis (RCA) fault allocations, and monthly billing statements. 

Solvers act as independent forensic arbitration engines to adjudicate dispute portfolios and calculate the exact **Net Approved Service Credit (in integer USD cents)** payable to the customer.

---

## Capability Claim
Solving CloudSLA-Forensics requires:
1. **Cross-Document Synthesis:** Integrating unstructured support ticket correspondence, Root Cause Analysis (RCA) timeline breakdowns, and email maintenance notices with structured JSON telemetry logs and billing sheets.
2. **Strict Legal Precedence & Hierarchy:** Applying master contract tiers, overriding addenda (e.g. Mission Critical VIP multipliers), and verifying conditional architectural eligibility requirements (e.g. Multi-AZ deployment prerequisites).
3. **Temporal Forensic Verification:** Checking maintenance advance notice timestamps against strict 72-hour contractual notice deadlines, isolating unscheduled maintenance overruns, and applying Force Majeure RTO grace periods.
4. **Interval Union Math:** Computing exact outage durations over unions of overlapping multi-service incidents without double-counting.
5. **Multi-Stage Financial Reconciliation:** Applying tier schedules, base charges (MRC vs variable spend), maximum monthly credit caps, and deducting prior interim credits.

---

## Comparison with Existing Benchmarks

| Benchmark Family / Eval | What it Tests | Why CloudSLA-Forensics is Distinct |
| :--- | :--- | :--- |
| **Synthetic Puzzles (e.g. Mutative Assembly, MFN-Cascade)** | Clean state-space search or graph traversal. | Can be solved with a 15-line script once the pattern is noticed. CloudSLA-Forensics requires authentic forensic cross-document investigation. |
| **Reimbursement Forensics** | Travel expense audits from emails and receipts. | CloudSLA-Forensics extends forensic arbitration into enterprise infrastructure contracts with complex telemetry, SLA tier curves, interval deduplication, and architectural prerequisites. |
| **GAIA / BrowseComp** | General multi-modal web search and tool use. | Often suffers from web drift, broken links, or under-specified answers. CloudSLA-Forensics is 100% deterministic, hermetic, and verifiable. |
| **SWE-bench / LiveCodeBench** | Python software engineering & coding. | Tests code modification rather than multimodal forensic audit and legal/financial adjudication. |

---

## Benchmark Structure & File Layout

```
.
├── README.md
├── benchmark_spec.json
├── generator.py
├── verifier.py
├── scorer.py
├── baselines.py
├── gold_private_sample.jsonl
├── validation_report.md
├── failure_modes.md
└── solver_bundle/
    ├── SOLVER_MANIFEST.json
    ├── README.md
    ├── solver_packet.md
    ├── CONTRACT_FRAMEWORK.md
    ├── items_private_sample.jsonl
    └── cases/
        ├── case_001/
        │   ├── contract.md
        │   ├── billing_statement.json
        │   ├── architecture_profile.json
        │   ├── telemetry/
        │   │   └── telemetry_events.json
        │   └── dossiers/
        │       ├── tickets/
        │       ├── maintenance/
        │       └── rca/
        └── ... (case_002 through case_030)
```

---

## Strict CLI Execution Contract

```bash
# 1. Generate 30 private sample items and complete solver bundle from scratch
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .

# 2. Verify dataset integrity, schema compliance, asset completeness, and zero leakage
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl

# 3. Score predictions against ground truth
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

---

## Answer Format & Scoring
- **Target Answer:** Integer USD cents (e.g. `185000` representing $1,850.00).
- **Prediction Format:** JSON Lines file where each row contains `{"id": "case_XXX", "answer": <integer_cents>}`.
- **Scorer Flexibility:** `scorer.py` robustly normalizes integer cents, string integers (`"185000"`), standard currency strings (`"$1,850.00"`), and standard key dictionaries without penalizing benign formatting variations.
