# Maritime Freight & Customs Audit (MFCA) Benchmark

Welcome to the **Maritime Freight & Customs Audit (MFCA)** benchmark package. This is a mess-reconciliation, multi-document financial audit evaluation.

MFCA evaluates a model's ability to act as a trade compliance auditor. It forces the solver to synthesize messy documents (Commercial Invoices, Bills of Lading, Vessel Logs, Exchange Rate lists, and natural language Email chains) to calculate exact customs duties, carrier charges, and identify audit reconciliation flags.

---

## 1. Directory Structure

```
├── README.md                 # This file (overview, CLI rules, and comparison)
├── benchmark_spec.json       # Capability claims, versioning, and specs
├── failure_modes.md          # Expected failure modes in solver models
├── generator.py              # Scenario and asset generator (30 items)
├── verifier.py               # Structural and schema verifier
├── scorer.py                 # Mathematical and flag-based scorer
├── gold_private_sample.jsonl # Private golden answers (30 rows)
├── validation_report.md      # Validation report, audit trace, and baseline results
└── solver_bundle/            # Public solver bundle (no gold answers!)
    ├── SOLVER_MANIFEST.json  # Manifest listing all asset files
    ├── README.md             # Solver instructions
    ├── trade_policy.md       # Canonical trade policy and tariff schedule
    ├── items_private_sample.jsonl # Input item definitions with asset links
    └── assets/               # Scenario assets folder
        └── item_001/         # Item-specific files:
            ├── bill_of_lading.md
            ├── commercial_invoice.md
            ├── vessel_port_log.md
            ├── exchange_rates.md
            └── email_correspondence.md
```

---

## 2. Strict CLI Contract

The following exact commands must be used to execute and grade the benchmark:

1. **Generate Scenarios**:
   ```bash
   /Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
   ```
2. **Verify Solver Bundle**:
   ```bash
   /Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
   ```
3. **Grade Predictions**:
   ```bash
   /Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
   ```

---

## 3. Data Contract

### Gold Answers & Predictions Schema
Both `gold_private_sample.jsonl` and solver predictions (`predictions.jsonl`) must contain rows of this exact format:
```json
{
  "id": "item_001",
  "answer": {
    "customs_duty_usd": 932.19,
    "carrier_charges_usd": 11400.0,
    "reconciliation_flag": "CURRENCY_VALUATION_ERROR"
  }
}
```

- `customs_duty_usd` (float): The actual customs duty payable to the government in USD, rounded to 2 decimal places. Enforced to within **\$0.05 tolerance** by the scorer.
- `carrier_charges_usd` (float): The actual carrier charges payable (freight + fuel/seasonal surcharges + demurrage + detention) in USD, rounded to 2 decimal places. Enforced to within **\$0.05 tolerance** by the scorer.
- `reconciliation_flag` (string): The category of audit discrepancy, matched case-insensitively. Must be one of:
  - `"HS_RECLASSIFICATION"`
  - `"INCOTERM_MISMATCH"`
  - `"DEMURRAGE_OVERCHARGE"`
  - `"CURRENCY_VALUATION_ERROR"`
  - `"NO_DISCREPANCY"`

---

## 4. Comparison to Existing Benchmarks

### Closest Benchmark: Reimbursement Forensics
MFCA is closest in shape to **Reimbursement Forensics** (from the BenchBench landscape), which reconciliation of receipts, policies, and emails under strict numeric targets and low solver saturation.

### Why MFCA is Not a Duplicate:
1. **Domain Shift**: Shifting from corporate travel expenses to global maritime shipping and customs tariffs. This introduces international trade law, customs valuations, and freight terms.
2. **Harder Chronological Logic**: introduces complex weekend-exclusion demurrage free time and standard charge stages, combined with **retrospective penal rate inclusions**. Naive datetime scripts will fail.
3. **Financial Regulatory Math**: Introduces Merchandise Processing Fee (MPF) minimum caps (\$30.00) and maximum caps (\$600.00), Harbor Maintenance Fees (HMF), and Free Trade Agreement (FTA) exclusions, which are structurally different from simple expense additions.
4. **Natural Language Discrepancy Categorization**: The solver is graded not just on raw numbers, but on identifying *why* the financial records didn't reconcile, requiring high-fidelity semantic classification of the operational errors.
