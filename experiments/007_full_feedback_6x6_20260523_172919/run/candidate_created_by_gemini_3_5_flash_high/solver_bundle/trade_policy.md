# Maritime Freight & Customs Audit (MFCA) - Canonical Trade Policy & Tariff Schedule

This document outlines the official trade policies, customs fees, and carrier charge structures that must be applied when auditing and reconciling shipping portfolios. All calculations must adhere strictly to these rules.

---

## 1. Customs Valuation and Duties

Customs duties are calculated as a percentage of the **Customs Value** (also known as the Transaction Value) of the imported cargo.

### 1.1 Incoterms Adjustments
The Customs Value must be calculated in USD by adjusting the Commercial Invoice value based on the stated Incoterm:
- **CIF (Cost, Insurance, and Freight)**: The invoice value already includes freight and insurance. Thus:
  $$\text{Customs Value} = \text{Invoice Cargo Value} + \text{Invoice Insurance} + \text{Invoice Ocean Freight}$$
  *Note: If insurance or ocean freight is not separately itemized on the invoice, default additions must be applied: Ocean Freight = 10% of Cargo Value, Insurance = 1.5% of Cargo Value.*
- **FOB (Free on Board)**: The Customs Value is exactly equal to the Invoice Cargo Value.
  $$\text{Customs Value} = \text{Invoice Cargo Value}$$
- **EXW (Ex Works)**: Inland freight and export fees must be added to the invoice cargo value.
  $$\text{Customs Value} = \text{Invoice Cargo Value} + \$350.00 \text{ (Inland Freight)} + \$150.00 \text{ (Export Clearance)}$$
- **CFR (Cost and Freight)**: Invoice value includes freight but not insurance. Insurance must be added:
  $$\text{Customs Value} = \text{Invoice Cargo Value} + \text{Invoice Insurance}$$
  *Note: If insurance is not itemized, add a default 1.5% of Cargo Value.*

### 1.2 Exchange Rate Conversion
- All foreign currency invoice amounts (EUR, GBP, JPY, CAD) must be converted to USD.
- The exchange rate used must be the rate active on the **Customs Declaration Date**, which is defined as the **Gate-Out Date** (the calendar date the container was picked up from the port).
- Use the exact rate provided in the scenario's `exchange_rates.md` table for that date.

### 1.3 Customs Fees & Surcharges
The total customs duty payable to the government is:
$$\text{Total Customs Duty Payable} = \text{Base Duty} + \text{Anti-Dumping Duty} + \text{HMF} + \text{MPF}$$

- **Base Duty**: $\text{Customs Value} \times \text{HS Code Duty Rate}$.
  - *Free Trade Agreement (FTA) Exception*: If a Free Trade Agreement certificate is validated in the email correspondence, the Base Duty is reduced to **$0.00** (0% rate).
- **Anti-Dumping Duty**: Certain HS codes are subject to anti-dumping tariffs (e.g., 15.0%). If applicable, this is calculated as:
  $$\text{Anti-Dumping Duty} = \text{Customs Value} \times \text{Anti-Dumping Rate}$$
- **Harbor Maintenance Fee (HMF)**: $0.125\%$ ($0.00125$) of the Customs Value.
- **Merchandise Processing Fee (MPF)**: $0.3464\%$ ($0.003464$) of the Customs Value.
  - MPF is subject to a **minimum of \$30.00** and a **maximum of \$600.00**. If the calculated MPF is less than \$30.00, it rounds up to \$30.00. If it exceeds \$600.00, it caps at \$600.00.
  - *Note*: Both HMF and MPF apply even if an FTA reduces the base duty to 0%.

### 1.4 HS Code Tariff Rates Table
Use the following table to determine the default duty rate:

| HS Code | Commodity Description | Default Duty Rate | Anti-Dumping Rate |
| :--- | :--- | :---: | :---: |
| **8471.30** | Portable Automatic Data Processing Machines (Laptops, Tablets) | 0.0% | 0.0% |
| **8517.13** | Smartphones / Cellular Network Handsets | 2.5% | 0.0% |
| **8517.18** | Other Transmission Apparatus (Routers, Modems) | 3.0% | 0.0% |
| **9403.20** | Metal Furniture of a Kind Used in Offices | 5.0% | 15.0% |
| **9403.60** | Wooden Furniture of a Kind Used in Offices | 4.5% | 0.0% |
| **7412.20** | Copper Tube or Pipe Fittings | 3.0% | 0.0% |
| **7415.33** | Copper Screws, Bolts, and Nuts | 4.0% | 12.0% |

---

## 2. Carrier Charges

Carrier charges consist of basic freight rates, seasonal surcharges, demurrage, and detention.

### 2.1 Ocean Freight Rates
Base rates are charged per container:
- **20ft Standard (20ST)**: \$1,200.00 per container.
- **40ft Standard (40ST)**: \$2,000.00 per container.
- **40ft High Cube (40HC)**: \$2,200.00 per container.

### 2.2 Fuel & Peak Season Surcharges
- **Low-Sulfur Fuel (LSF) Surcharge**: A flat \$150.00 per container.
- **Peak Season Surcharge (PSS)**: \$250.00 per container. This surcharge is only applied if the container's **Gate-Out Date** falls between **August 1st and October 31st (inclusive)**.

### 2.3 Demurrage (Port Storage Charges)
Demurrage is charged by the carrier for keeping the container inside the port past the allowed free time.
- **Free Time**: **5 calendar days** starting on the day *after* the Completion of Discharge (ATC).
  - *Example*: If ATC is October 10th, the free time starts on October 11th and ends on October 15th.
- **Demurrage Free Time Weekend Policy**:
  - Saturdays and Sundays are **excluded** from free time days.
  - *Example*: If free time starts on Friday (Day 1), Saturday and Sunday are skipped, and Monday is Day 2.
- **Demurrage Charge Calculation**:
  - Charges begin the calendar day after the free time ends, up to the **Gate-Out Date** (the day the container is picked up).
  - **Standard Rate Stage (Days 1–3 after free time)**: \$150.00 per container per day. Saturdays and Sundays are **excluded** from standard charge days.
  - **Penal Rate Stage (Day 4 and onwards)**: \$300.00 per container per day. Once the penal rate stage is reached, Saturdays and Sundays are **included** in all charge days (including retrospectively for the penal days).
  - *Demurrage Waivers*: If the email correspondence contains a formal waiver (e.g. port strike, equipment failure), the specified waiver days must be subtracted from the total chargeable demurrage days before computing the fee.

### 2.4 Detention (Container Rental Charges)
Detention is charged by the carrier for keeping the container outside the port past the allowed empty return time.
- **Free Time**: **7 calendar days** starting on the day of **Gate-Out** (pick-up day).
  - *Example*: If Gate-Out is October 15th, free time runs from October 15th to October 21st inclusive.
- **Detention Free Time Weekend Policy**:
  - Saturdays and Sundays are **included** in detention free time days.
- **Detention Charge Calculation**:
  - Charges begin the calendar day after free time ends, up to the **Gate-In Date** (empty container returned to depot).
  - **Detention Rate**: \$100.00 per container per day.
  - Saturdays and Sundays are **always included** in detention charge days.
