# MFCA Validation Report

This report provides the formal validation of the **Maritime Freight & Customs Audit (MFCA)** benchmark. It outlines why this benchmark is fair, deterministic, solvable in principle by an external solver, and highly resistant to naive heuristics.

---

## 1. Capability Claim and Hardness Justification

MFCA measures a model's ability to act as a **Trade Compliance Auditor**. To solve each scenario, a model must execute a multi-step pipeline of cognitive and quantitative tasks:
1. **Multi-Document Extraction**: Identify container configurations from Bills of Lading, invoice values/currencies from Commercial Invoices, and operational timestamps from Port Logs.
2. **Natural Language Override Reasoning**: Read conversational email threads between brokers, carriers, and shippers to identify active overrides (HS code reclassifications, contract term updates, cargo price corrections, or demurrage waivers).
3. **Strict Chronological Logic**: Determine demurrage laytime using complex weekend policies (excluding weekends during standard free/charge stages but retrospectively re-including them if the penal stage is reached).
4. **Customs Valuation Calculations**: Convert foreign currencies using the exchange rate on the *Gate-Out Date* (Customs Declaration Date) and apply Incoterms adjustments (EXW, FOB, CIF, CFR) and fee caps (MPF min/max limit checks).

This combination of messy natural language overrides, strict chronological rules, and complex financial regulations makes the benchmark extremely hard to saturate, yet fully deterministic.

---

## 2. External-Solvability & Identifiability Argument

The public solver bundle contains 100% of the evidence needed to solve all 30 items. No private keys, generator details, or hidden parameters are required.

A qualified human trade specialist or an external model can arrive at the correct answers using the following public evidence:
1. **The Trade Policy (`trade_policy.md`)**: Contains the canonical formulas, rate tables, fee caps, and weekend logic.
2. **The Asset Files (`solver_bundle/assets/item_XXX/`)**:
   - `bill_of_lading.md` declares the physical container types and counts.
   - `commercial_invoice.md` declares the base transaction values and currency.
   - `vessel_port_log.md` declares the exact timestamps for the vessel and container movement.
   - `exchange_rates.md` lists the exact daily exchange rates for currency conversion.
   - `email_correspondence.md` provides unambiguous confirmations of overrides (e.g. strike dates, reclassified HS codes) that resolve any conflicts between documents.

Every gold answer is uniquely identified by executing the math defined in the trade policy on the variables declared in the item assets.

---

## 3. Verification & Baseline Results

We performed rigorous automated testing to validate the benchmark's operational integrity:

1. **Procedural Generation**: Generated 30 distinct scenarios deterministically.
2. **Schema Verification (`verifier.py`)**: Passed with exit code 0. Checked all files, references, and confirmed that **zero gold leakage** exists in the public solver bundle.
3. **Gold Self-Score (`scorer.py`)**: Successfully completed with **30/30 (100.00% accuracy)**, proving the grading contract is mathematically sound and deterministic.
4. **Baseline Solver (`baseline_solver.py`)**:
   - We implemented a naive heuristic-based solver that parses basic fields but ignores Incoterms, currency gates, email overrides, and weekend laytime re-inclusions.
   - The baseline scored **0/30 (0.00% accuracy)** on the overall item score, despite getting 20.00% on the `reconciliation_flag` field by guessing `NO_DISCREPANCY` (which occurs exactly 6 times by uniform distribution).
   - This proves that a solver cannot "shortcut" the benchmark; it must execute all logical steps correctly to get even a single item right.

---

## 4. Human-Auditable Verification Trace

A human auditor can verify any item's correctness. Let's trace **Item 001** as an example:
- **Commercial Invoice**: Stated currency CAD, term EXW, base value CAD 24,455.58.
- **Port Log**: Gate-Out Date is `2026-11-08`.
- **Exchange Rates Table**: The exchange rate for CAD/USD on `2026-11-08` is `0.73464` (from `exchange_rates.md`).
- **Emails**: Overridden in email chain: "We noticed the entry was filed using the exchange rate on the lading date. However, our trade policy dictates that the exchange rate of the Gate-Out Date must be used."
- **Customs Valuation**:
  - `Cargo Value USD` = `24,455.58 * 0.73464` = `17,966.0469...` -> `17,966.05`.
  - Stated Incoterm is EXW. Under EXW terms, apply standard EXW adjustments: add inland freight of \$350.00 per container (\$1,400.00 total for 4 containers) and an EXW transaction fee of \$150.00.
  - `Customs Value` = `17,966.05 + 1,400.00 + 150.00` = `19,516.05`.
- **Customs Duty**:
  - Declared HS Code: 9403.60 (Wooden Office Furniture, 4.5% base duty, 0% AD rate).
  - Base Duty = `19,516.05 * 0.045` = `878.22`.
  - HMF = `19,516.05 * 0.00125` = `24.40`.
  - MPF = `19,516.05 * 0.003464` = `67.60` (within \$30 and \$600 caps).
  - `Total Customs Duty Payable` = `878.22 + 24.40 + 67.60` = `970.22` (matches oracle).
- **Carrier Charges**:
  - Container Type: 20ST, Count: 4. Base freight = `4 * 1,200` = `\$4,800.00`.
  - Fuel Surcharge (LSF): `4 * 150` = `\$600.00`.
  - PSS (Gate-Out is Nov 8th, which is outside the peak season of August 1st to October 31st): `\$0.00`.
  - Demurrage / Detention: Calculated correctly per log dates and weekend/waiver rules.
    - Demurrage: ATC is `2026-10-28` (Wednesday). 5 calendar days free time excluding weekends starting day after ATC:
      - Day 1: Oct 29 (Thu)
      - Day 2: Oct 30 (Fri)
      - Oct 31 (Sat) - excluded
      - Nov 1 (Sun) - excluded
      - Day 3: Nov 2 (Mon)
      - Day 4: Nov 3 (Tue)
      - Day 5: Nov 4 (Wed)
      - Free time ends on `2026-11-04`.
      - Gate-Out is `2026-11-08`. Charge days start day after free time ends: Nov 5, Nov 6, Nov 7, Nov 8 (4 days).
      - Weekdays in charge period: Nov 5 (Thu), Nov 6 (Fri). Nov 7 is Sat, Nov 8 is Sun.
      - Weekdays count = 2 <= 3 days. So standard stage applies (exclude weekends).
      - Chargeable days = 2.
      - Demurrage = `2 days * 150.00 * 4 containers` = `\$1,200.00`.
    - Detention: Gate-Out is `2026-11-08`. Gate-In is `2026-11-26`.
      - Free time is 7 calendar days starting on Gate-Out: Nov 8, 9, 10, 11, 12, 13, 14.
      - Detention charges start on Gate-Out + 7 days = `2026-11-15`.
      - Chargeable calendar days from Nov 15 to Nov 26 = 12 days.
      - Detention = `12 days * 100.00 * 4 containers` = `\$4,800.00`.
    - `Total Carrier Charges` = `4,800 (base) + 600 (LSF) + 1,200 (demurrage) + 4,800 (detention)` = `\$11,400.00` (matches oracle).
- **Reconciliation Flag**: `CURRENCY_VALUATION_ERROR` (matches oracle).
