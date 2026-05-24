# Expected Failure Modes for Solvers in MFCA

The **Maritime Freight & Customs Audit (MFCA)** benchmark is designed to expose deep reasoning and math vulnerabilities in frontier LLMs. Below are the specific cognitive, mathematical, and logical failure modes we anticipate solvers will exhibit.

---

## 1. Chronological & Demurrage Failure Modes

### 1.1 Free-Time Exclusions
- **The Trap**: Demurrage free time starts the day *after* completion of discharge (ATC) and spans 5 calendar days, but **excludes Saturdays and Sundays**.
- **Failure Mode**: Models will naively do a simple calendar addition `ATC + 5 days` without inspecting whether weekends occurred in that window.
- **Example**: If ATC is October 9th (Friday), free time starts Saturday Oct 10th. Correct free time ends October 16th (Friday) because Sat/Sun are excluded. Naive models will calculate October 14th (Wednesday).

### 1.2 Penal Rate Weekend Re-inclusion (The Retrospective Trap)
- **The Trap**: Demurrage charge stage 1 (Days 1–3) excludes weekends. Stage 2 (Day 4+) includes weekends retrospectively for all penal days.
- **Failure Mode**: Models will either never count weekends at all, or will always count weekends, or will only count weekends starting on day 4 without including the retrospective days. This causes large discrete calculation errors.

### 1.3 Demurrage vs. Detention Confusion
- **The Trap**: Demurrage (port storage) has strict weekend exclusions. Detention (container rental) has **no weekend exclusions** (weekends are always included).
- **Failure Mode**: Models will apply demurrage weekend-exclusion heuristics to detention calculations, leading to undercharging carrier fees.

---

## 2. Trade Compliance & Customs Valuation Failure Modes

### 2.1 Incoterms Valuation Errors
- **The Trap**: Different Incoterms require different adjustments. `EXW` adds inland freight ($350) and export clearance ($150). `CIF` adds ocean freight (10%) and insurance (1.5%) if not itemized. `FOB` adds nothing.
- **Failure Mode**: Models will use raw Commercial Invoice amounts as the customs basis directly, failing to apply the Incoterms rules in Section 1.1 of the policy.

### 2.2 Currency Conversion Date Misalignment
- **The Trap**: Policy dictates that foreign currencies must be converted using the exchange rate on the **Customs Declaration Date** (defined as the **Gate-Out Date**).
- **Failure Mode**: Models will convert currency using the Lading Date (when cargo loaded) or Invoice Date, which are common industry practices but violate this specific policy.

### 2.3 Fee Cap & Limit Violations (MPF & HMF)
- **The Trap**: The Merchandise Processing Fee (MPF) is 0.3464% of the Customs Value, but is subject to a strict **minimum of \$30.00** and a **maximum of \$600.00**.
- **Failure Mode**: Models will omit the min/max caps on high-value or low-value shipments, returning raw calculated values like \$15.20 (which should be \$30.00) or \$1,200.00 (which should be \$600.00).

### 2.4 FTA vs. Fees Misunderstanding
- **The Trap**: Free Trade Agreements (FTAs) reduce the *base duty* to \$0.00, but the **HMF and MPF fees still apply**.
- **Failure Mode**: Models will set the entire customs duty to \$0.00 when an FTA certificate is mentioned, failing to add the HMF and MPF components.

---

## 3. Natural Language Override & Resolution Failures

### 3.1 Email Override Neglect
- **The Trap**: Crucial instructions (e.g. HS reclassification, transaction price typos, or demurrage waivers) are buried in conversational emails rather than formal tables.
- **Failure Mode**: Models relying on high-level table extraction will miss these conversational nuances and compute "correct" values for the *wrong* variables.

### 3.2 Improper Demurrage Waiver Adjustments
- **The Trap**: If a strike occurred and a waiver is granted, those specific calendar dates must be excluded from the laytime/charge timeline.
- **Failure Mode**: Models will subtract the waiver days from the *final dollar amount* (e.g., subtracting \$150 or \$300) rather than subtracting the *calendar dates* from the timeline, which leads to mathematically incorrect penal-rate triggers.
