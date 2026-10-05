# Master Cloud Services Agreement (MSA) & Service Level Schedule
**Customer ID:** CUST-1028  
**Contract Plan Tier:** `MISSION_CRITICAL_VIP`  
**Effective Date:** 2025-01-01  
**Governing Standard:** Master Cloud SLA Framework v4.2

---

## 1. Scope and Availability Targets
The Provider guarantees service availability during each calendar month measurement period.
- **Contracted Target Availability:** 99.99%
- **Measurement Base:** Calendar Month of 30 Days (43,200 Total Minutes).

## 2. Service Credit Schedule
If the Effective Monthly Uptime Percentage falls below the contracted target, the Customer is entitled to the following base service credit percentage:

| Effective Monthly Uptime Range | Base Service Credit (% of MRC) |
| :--- | :--- |
| 99.95% to 99.99% | 15% |
| 99.90% to 99.95% | 30% |
| Less than 99.90% | 60% |

## 3. Maximum Monthly Credit Cap
- Total aggregate service credits in any single calendar billing month shall not exceed **100% of the Monthly Recurring Charge (MRC)**.
- Any interim service credits already issued or refunded during the active billing month must be credited against this final amount.

## 4. Special Riders & Addenda
- **Addendum VIP-1 (Mission Critical Acceleration):** A **1.50x Credit Multiplier** applies to the gross credit calculation, PROVIDED THAT Customer has active Multi-AZ / Multi-Region high availability architecture configured. If Customer operates Single-AZ, standard 1.00x multiplier applies.
- **Addendum VIP-2 (Variable Fee Ingestion):** Service credit percentage applies to the sum of Monthly Recurring Charge (MRC) AND Variable Usage Spend.

## 5. Standard Framework Incorporation
All outage criteria, maintenance notification rules (72-hour notice window requirement), RCA fault allocation, Force Majeure RTO grace periods, and interval deduplication rules are governed strictly by `CONTRACT_FRAMEWORK.md`.
