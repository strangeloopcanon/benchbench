# General Conditions of the Subcontract
## Progress Payment Certification Procedures

**Document Reference: GC-2024-Rev3**
**Effective Date: January 1, 2024**
**Applicability: All subcontracts issued under this Master Agreement**

---

## Article 7 — Progress Payments

### §7.1 Work Completed to Date

The Work Completed to Date for each line item in the Schedule of Values shall be computed as:

    Work Completed to Date = Scheduled Value × (Current Percent Complete / 100)

Each line item's value shall be rounded to the nearest cent independently.

The **Total Work Completed to Date** is the sum of all line-item Work Completed to Date values. This is a cumulative figure representing all work from project inception through the current billing date.

### §7.2 Retention

Retention shall be withheld from each Application for Payment as follows:

- **Ten percent (10%)** of the amount due shall be retained until the Work is **fifty percent (50%) complete**.
- Upon reaching **fifty percent (50%) completion**, retention shall reduce to **five percent (5%)** of the amount due.

The completion threshold is determined by the **overall cumulative percent complete** of the subcontract (the `cumulative_percent_complete` field), NOT by individual line items. The retention rate applies to the **subtotal before retention** (gross earned + stored materials credit).

### §7.3 Previous Payments

The **Net Amount Due** for each Application for Payment shall be reduced by the total of all **Previous Payments** made to the Subcontractor under this subcontract. The Previous Payments value represents the cumulative sum of all prior certified and disbursed amounts.

### §7.4 Stored Materials

Materials delivered to the Project site but not yet incorporated into the Work may be included in the Application for Payment at **one hundred percent (100%)** of invoice value, provided that ALL of the following conditions are satisfied:

1. A **paid invoice or bill of sale** documenting the purchase is provided (`has_documentation` = true).
2. The materials are **properly stored and protected** from damage, theft, and weather (`is_protected` = true).
3. The materials are **covered under the Subcontractor's insurance policy** (`has_insurance` = true).

If **any one** of these three conditions is not met, the credit for that stored material entry is **$0.00**. There is no partial credit.

---

## Article 8 — Change Orders

### §8.1 Types of Change Orders

Change Orders (COs) may exist in one of four statuses:
- **Approved**: Fully executed by Owner, Contractor, and Subcontractor.
- **Pending**: Submitted and under review; not yet fully executed.
- **Disputed**: Parties disagree on scope, price, or responsibility.
- **Rejected**: Denied by the Owner or Contractor.

### §8.2 Change Order Earned Value

The Earned Value for each Change Order is:

    CO Earned = CO Amount × (CO Percent Complete / 100)

Where **CO Amount** is the total value of the change order and **CO Percent Complete** is the reported progress on that change order scope.

### §8.3 Billing Rates by Status

The amount billable for each Change Order depends on its status:

| Status | Billable Amount |
|--------|----------------|
| Approved | 100% of CO Earned |
| Pending | 50% of CO Earned |
| Disputed | 25% of CO Earned |
| Rejected | $0.00 |

The **Gross Earned (Change Orders)** is the sum of all billable CO amounts.

### §8.4 Material Classification

Change Orders flagged as material (`is_material` = true) contribute to the materials earned subtotal for tax calculation purposes (see §11.1).

---

## Article 9 — Liquidated Damages

### §9.1 Assessment

If the Subcontractor fails to achieve Substantial Completion by the contractual milestone date, Liquidated Damages (LDs) shall be assessed as follows:

    LD Amount = Days Behind Schedule × Daily LD Rate

Subject to the following provisions:

- The LD Amount shall **not exceed the LD Cap** specified in the subcontract.
- If the delay is classified as an **Excusable Delay** (including but not limited to: abnormal weather events, force majeure, Owner-caused delays, or changes in law), Liquidated Damages shall **NOT apply** regardless of the number of days behind schedule.

The LD deduction is applied **after** retention.

### §9.2 Data Fields

- `days_behind`: Calendar days between the contractual milestone and actual/projected completion.
- `daily_rate_cents`: The per-day LD assessment in cents.
- `cap_cents`: Maximum total LD assessment in cents.
- `is_excusable`: Boolean indicating whether the delay qualifies as excusable.

---

## Article 10 — Insurance Requirements

### §10.1 Continuous Coverage

The Subcontractor shall maintain continuous insurance coverage throughout the duration of the Work. Any lapse in coverage constitutes a material breach.

### §10.2 Payment Deduction for Lapse

If the Subcontractor's insurance lapses during the billing period, work performed during the lapse window is deemed **non-billable**. The deduction is calculated as:

    Insurance Deduction = Gross Earned This Period × (Lapse Days in Period / Total Days in Period)

Where:
- **Lapse Days in Period** = the number of calendar days within the overlap of [lapse_start_day, lapse_end_day] and [period_start_day, period_end_day], inclusive on both ends.
- **Total Days in Period** = period_end_day − period_start_day + 1.
- **Gross Earned This Period** = Gross Earned (Original Scope) + Gross Earned (Change Orders). Stored materials are NOT affected by the insurance deduction.

If there is no overlap between the lapse window and the billing period, the deduction is $0.00.

### §10.3 Overlap Calculation

The overlap is computed as:
- overlap_start = max(lapse_start_day, period_start_day)
- overlap_end = min(lapse_end_day, period_end_day)
- lapse_days = max(0, overlap_end − overlap_start + 1)

---

## Article 11 — Taxes

### §11.1 Sales Tax on Materials

Sales tax shall be applied **only** to material line items and material-flagged Change Orders. The applicable tax rate is specified per project in the `tax_rate` field.

    Tax Amount = Materials Earned This Period × Tax Rate

Where **Materials Earned This Period** is the sum of:
- Earned value from line items where `is_material` = true, PLUS
- Billable Change Order value from COs where `is_material` = true.

### §11.2 Tax Exemption

If the project is designated as **tax-exempt** (`tax_exempt` = true), typically for government or nonprofit owners, NO sales tax shall be applied regardless of material content. The Tax Amount is $0.00.

### §11.3 Tax Treatment in Computation

Sales tax is **added** to the payment amount. It is computed on the materials earned this period (before retention or other deductions are applied to those materials).

---

## Article 12 — Deductions

### §12.1 Backcharges

Backcharges represent costs incurred by the Contractor due to the Subcontractor's failure to perform obligations. Each backcharge has a fixed dollar amount that is **deducted** from the current payment. The sum of all backcharge amounts is subtracted after retention.

### §12.2 Deficiency Holdbacks

When the Architect or Inspector identifies deficient work, a holdback amount is assessed for each deficiency. The holdback is **deducted** from the current payment and held until the deficiency is corrected. The sum of all deficiency holdback amounts is subtracted after retention.

---

## Article 13 — Computation Sequence (Cumulative Method)

The Certified Amount shall be computed using the **cumulative method** (consistent with AIA Document G702). The precise sequence is:

1. For each Schedule of Values line item, compute **Work Completed to Date**:
   `Completed_to_Date = Scheduled Value × (Current Percent Complete / 100)`
   Round each line item's completed value to the nearest cent independently.
2. Sum all line-item Completed to Date values → **Total Work Completed to Date**
3. Compute billable value for each Change Order (§8.2, §8.3) → **CO Earned to Date**
4. Compute Stored Materials Credit (§7.4)
5. **Total Completed & Stored** = Total Work Completed to Date + CO Earned to Date + Stored Materials Credit
6. Determine Retention Rate based on `cumulative_percent_complete` (§7.2)
7. **Retention Amount** = Total Completed & Stored × Retention Rate (rounded)
8. **Net Earned to Date** = Total Completed & Stored − Retention Amount
9. Subtract Backcharges (§12.1)
10. Subtract Deficiency Holdbacks (§12.2)
11. Subtract Liquidated Damages (§9.1)
12. Subtract Insurance Deduction (§10.2) — computed on **this period's work** only
13. Add Sales Tax (§11.1) — computed on **this period's materials** only
14. Subtract Previous Payments (§7.3) — the `previous_payments_cents` value
15. **Current Payment Due** = result of steps 8 through 14

### §13.1 Rounding

All intermediate monetary calculations shall be rounded to the nearest cent using **banker's rounding** (round half to even). The final Certified Amount is expressed as an integer number of cents (positive or negative).

### §13.2 This Period's Work Earned

For the Insurance Deduction (§10.2), "this period's work earned" means:
- (Total Work Completed to Date) minus (sum of each line item's `Scheduled Value × Previous Percent / 100`, rounded per line)
- Plus CO Earned to Date (full CO earned, since COs are new this period)

For the Sales Tax (§11.1), "this period's materials earned" means:
- The difference in completed value for material-flagged line items (current minus previous, computed per line), PLUS
- CO Earned to Date for material-flagged COs

### §13.3 Negative Amounts

The Certified Amount may be negative if deductions and previous payments exceed the earned value. A negative amount indicates an overpayment that the Subcontractor owes back to the Contractor.

---

## Article 14 — Answer Format

The solver shall provide the **Certified Amount in cents** as a single integer value for each item. For example, if the certified payment is $12,345.67, the answer is `1234567`. If the certified amount is negative $500.00, the answer is `-50000`.

---

*End of General Conditions*
