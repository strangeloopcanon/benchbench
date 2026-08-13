# Master Cloud Services Agreement (MSA) & Service Level Schedule
**Customer ID:** CUST-1025  
**Contract Plan Tier:** `HIGH_THROUGHPUT_FINTECH`  
**Effective Date:** 2025-01-01  
**Governing Standard:** Master Cloud SLA Framework v4.2

---

## 1. Scope and Availability Targets
The Provider guarantees service availability during each calendar month measurement period.
- **Contracted Target Availability:** 99.95%
- **Measurement Base:** Calendar Month of 30 Days (43,200 Total Minutes).

## 2. Service Credit Schedule
If the Effective Monthly Uptime Percentage falls below the contracted target, the Customer is entitled to the following base service credit percentage:

| Effective Monthly Uptime Range | Base Service Credit (% of MRC) |
| :--- | :--- |
| 99.90% to 99.95% | 10% |
| 99.50% to 99.90% | 25% |
| Less than 99.50% | 50% |

## 3. Maximum Monthly Credit Cap
- Total aggregate service credits in any single calendar billing month shall not exceed **75% of the Monthly Recurring Charge (MRC)**.
- Any interim service credits already issued or refunded during the active billing month must be credited against this final amount.

## 4. Special Riders & Addenda
- **Addendum FIN-1 (Fintech Performance Rider):** A **1.25x Credit Multiplier** applies to gross credit calculation if Multi-AZ is active (1.00x for Single-AZ).
- **Addendum FIN-2:** Credit applies strictly to Monthly Recurring Charge (MRC) only. Variable bursting charges are excluded.

## 5. Standard Framework Incorporation
All outage criteria, maintenance notification rules (72-hour notice window requirement), RCA fault allocation, Force Majeure RTO grace periods, and interval deduplication rules are governed strictly by `CONTRACT_FRAMEWORK.md`.
