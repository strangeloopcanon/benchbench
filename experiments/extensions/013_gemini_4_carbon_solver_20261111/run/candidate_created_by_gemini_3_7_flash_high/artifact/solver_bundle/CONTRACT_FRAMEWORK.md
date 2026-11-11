# Master Cloud SLA Legal & Mathematical Framework (v4.2)
**Publication Reference:** CloudSLA-Standard-2026.4  
**Applicability:** Universal adjudication standard for all Cloud Infrastructure SLA arbitration cases.

---

## 1. Core Principles & Definitions
This document sets forth the authoritative, unambiguous mathematical and procedural rules for calculating service credit entitlements under Cloud Services Master Agreements.

### 1.1 Measurement Period
- All evaluations are conducted over a standard monthly billing period.
- For a 30-day billing month (e.g. April 2026), the Total Available Period is:
  $$\text{Total Period Minutes } (M_{\text{total}}) = 30 \times 24 \times 60 = 43,200 \text{ minutes}$$

### 1.2 Outage Qualification Criteria
An incident event qualifies as an **Unscheduled Outage Event** if and only if:
1. The observed API error rate is $\ge 5.0\%$ or service is entirely unavailable. Incidents with error rate $< 5.0\%$ are classified as non-breaching telemetry fluctuations and accrue **0 minutes** of compensable downtime.
2. The event is not fully excused by the exclusions set forth in Section 2.

---

## 2. Exclusions and Deductions from Outage Time

### 2.1 Scheduled Maintenance Windows
- **Timely Notice Rule:** Maintenance is exempt from downtime calculations **IF AND ONLY IF** formal written notice was transmitted $\ge 72$ hours prior to the scheduled window start timestamp (`notice_sent_at` $\le$ `target_window_start` $- 72\text{h}$).
- **Tardy Notice Penalty:** If notice was sent $< 72$ hours prior, the notice is invalid, and **100% of the maintenance duration counts as unscheduled outage**.
- **Overrun Rule:** For timely notices, the scheduled window is exempt. However, any time elapsed beyond the scheduled window duration is an **Unscheduled Maintenance Overrun** and is fully compensable.

### 2.2 Customer-Attributable Fault (RCA Allocation)
- When an official Root Cause Analysis (RCA) determines that a portion of an incident was caused by Customer misconfiguration, malformed scripts, or unannounced load spikes, that specific customer-attributable duration ($M_{\text{cust}}$) is deducted from the incident duration:
  $$M_{\text{compensable}} = M_{\text{gross}} - M_{\text{cust}}$$

### 2.3 Force Majeure & Third-Party Transit Cuts (RTO Grace Period)
- For documented Force Majeure events (e.g. Tier-1 transit carrier metro fiber cuts, utility grid power loss), the Provider is granted an **RTO Grace Period of 30 minutes**.
- If total event duration is $\le 30$ minutes, compensable downtime is **0**.
- If total event duration exceeds 30 minutes, compensable downtime equals the excess duration:
  $$M_{\text{compensable}} = M_{\text{gross}} - 30$$

---

## 3. Incident Deduplication (Union of Outage Intervals)
- In multi-service or multi-incident deployments, outages across different services (or multiple concurrent incidents) during overlapping timestamps **must not be double-counted**.
- The Total Compensable Outage Minutes ($M_{\text{outage}}$) is the exact measure of the **union of all compensable intervals**:
  $$M_{\text{outage}} = \left| \bigcup_{i} [\text{start}_i, \text{end}_i] \right|$$

---

## 4. Uptime Percentage Calculation
The Effective Monthly Uptime Percentage ($U$) is calculated as:
$$U = \frac{M_{\text{total}} - M_{\text{outage}}}{M_{\text{total}}} \times 100.0$$

---

## 5. Credit Schedule & Financial Adjudication

### 5.1 Base Credit Tier Lookup
Evaluate $U$ against the Contract Schedule table:
- Match the tier where $\text{min\_uptime} \le U < \text{max\_uptime}$.
- If $U \ge \text{Contract Target}$, Base Credit Percentage $C = 0\%$.

### 5.2 Addenda Multipliers & Eligibility
- If the Contract includes an Addendum with a VIP Multiplier ($M_{\text{vip}}$):
  - Check whether Customer satisfies the architectural prerequisite (e.g. `multi_az_enabled == true`).
  - If satisfied, apply $M_{\text{vip}}$ (e.g. 1.50x or 1.25x).
  - If prerequisite is not satisfied (e.g. Single-AZ deployment), $M_{\text{vip}} = 1.00$.

### 5.3 Applicable Base Charge
- **Standard Contracts:** Credit applies to Monthly Recurring Charge (MRC) only.
- **Variable Spend Addendum (e.g. VIP-2):** Credit applies to $\text{MRC} + \text{Variable Usage Charge}$.

### 5.4 Gross Credit Calculation
$$\text{Credit}_{\text{gross}} = \text{round}\left( \text{Applicable Base Charge} \times \frac{C}{100} \times M_{\text{vip}} \right)$$
*(Standard rounding to nearest integer cent: half-way values round up).*

### 5.5 Monthly Cap and Prior Issued Credits
1. **Apply Cap:**
   $$\text{Credit}_{\text{capped}} = \min\left( \text{Credit}_{\text{gross}}, \text{MRC} \times \frac{\text{Max Cap \%}}{100} \right)$$
2. **Subtract Prior Credits:**
   $$\text{Credit}_{\text{net}} = \max\left( 0, \text{Credit}_{\text{capped}} - \text{Prior Credits Issued} \right)$$

The final result $\text{Credit}_{\text{net}}$ is the exact integer USD cents payable.
