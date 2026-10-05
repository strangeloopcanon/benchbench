# Failure Modes Analysis for CloudSLA-Forensics

This document outlines the systematic failure modes and trap layers that punish one-pass heuristics, naive prompt-only LLM reasoning, and superficial scripting on CloudSLA-Forensics.

---

## 1. Primary Cognitive & Forensic Failure Modes

### Failure Mode 1: Maintenance Lead-Time Blindness (The 72-Hour Rule)
- **Description:** A solver sees a maintenance ticket and blindly deducts the entire duration as "approved maintenance."
- **Trap Mechanism:** Under `CONTRACT_FRAMEWORK.md §2.1`, scheduled maintenance is exempt **only if** written notice was transmitted $\ge 72$ hours prior to the window start timestamp. If notice was transmitted 48 hours before, the notice is legally invalid and 100% of the duration counts as unscheduled outage.
- **Impact:** Leads to substantial under-counting of compensable outage minutes and an erroneously high uptime percentage.

### Failure Mode 2: Maintenance Overrun Truncation
- **Description:** A solver identifies a valid maintenance notice (e.g., 2 hours scheduled) and ignores the actual telemetry duration (e.g., 2 hours 45 minutes).
- **Trap Mechanism:** While the scheduled 2 hours are exempt, the 45-minute overrun is an unscheduled outage and must accrue compensable downtime.
- **Impact:** Causes the calculated downtime to miss the critical overrun delta.

### Failure Mode 3: Neglect of Root Cause Analysis (RCA) Fault Allocation
- **Description:** A solver extracts the gross duration from telemetry logs (e.g., 180 minutes) without reading the associated RCA report in `dossiers/rca/`.
- **Trap Mechanism:** The RCA report establishes that 45 minutes of the outage was caused by customer-side DNS or deployment script failure, with only 135 minutes attributable to provider hypervisor failure. Per SLA §5.3, customer-attributable minutes must be subtracted.
- **Impact:** Leads to gross over-counting of compensable downtime, triggering higher credit tiers than warranted.

### Failure Mode 4: Overlapping Multi-Service Double-Counting
- **Description:** In complex multi-service outages (e.g., Database and API Gateway degrading simultaneously between 14:00 and 15:30), a solver independently sums duration minutes ($90 + 90 = 180$ minutes).
- **Trap Mechanism:** The master framework specifies that monthly downtime is the set-theoretic union of outage intervals (90 total minutes), not the sum of individual service incidents.
- **Impact:** Causes severe inflation of downtime.

### Failure Mode 5: Misapplication of Conditional Addendum Multipliers
- **Description:** A solver detects `Addendum VIP-1` (which specifies a 1.50x credit multiplier) in `contract.md` and immediately applies it to the calculation.
- **Trap Mechanism:** The Addendum explicitly contains a condition precedent: the multiplier applies *only if* the customer has active Multi-AZ / Multi-Region deployment enabled in `architecture_profile.json`. If `multi_az_enabled` is `false`, standard terms (1.00x) apply.
- **Impact:** Produces a 50% overstatement of gross credits.

### Failure Mode 6: Base Charge Scope Confusion (MRC vs Variable Spend)
- **Description:** Solvers confuse whether credits apply to Monthly Recurring Charges (MRC) only or to Total Billed Spend (MRC + Variable Usage).
- **Trap Mechanism:** Standard contracts apply credits solely to MRC. Only specific custom addenda (e.g., `Addendum VIP-2`) authorize credit calculations against variable spend.
- **Impact:** Discrepancy of thousands of dollars in final settlement amount.

### Failure Mode 7: Monthly Cap and Prior Credit Reconciliation Omission
- **Description:** Computing gross credits and failing to apply the contract cap (e.g., 50% or 75% of MRC) or failing to deduct interim credits already issued earlier in the billing cycle.
- **Trap Mechanism:** Real enterprise contracts enforce hard caps and credit reconciliation ledgers.
- **Impact:** Emits gross credit instead of net payable credit.

### Failure Mode 8: Below-Threshold Distractor Misclassification
- **Description:** A customer opened a support ticket for latency alerts, but telemetry reveals the error rate was only 1.2% (below the 5.0% contractual Outage threshold).
- **Trap Mechanism:** Solvers treating all opened tickets as outages without checking telemetry breach thresholds will over-compensate.
- **Impact:** Accrues non-compensable downtime.

---

## 2. Model Vulnerability Distribution Matrix

| Difficulty Level | Key Challenge Layers | Vulnerable Solver Types | Expected Success Rate |
| :--- | :--- | :--- | :--- |
| **Level 1 (Items 1-6)** | Basic contract reading, 1-2 incidents, standard tier lookup | Naive zero-shot prompts | 70% - 90% |
| **Level 2 (Items 7-12)** | Maintenance overrun, interval union deduplication | Simple regex / non-forensic scripts | 40% - 60% |
| **Level 3 (Items 13-18)** | RCA multi-phase timeline attribution, notice 72h lead time verification | Solvers that do not parse ticket dossiers | 20% - 40% |
| **Level 4 (Items 19-24)** | Conditional VIP addenda, Multi-AZ prerequisites, variable spend | Models that ignore architecture files or legal conditions | 10% - 30% |
| **Level 5 (Items 25-30)** | Full multi-tier forensic stack: Force Majeure RTO + Cap + Prior Credit | Models prone to compounding arithmetic or reasoning drift | 5% - 20% |
