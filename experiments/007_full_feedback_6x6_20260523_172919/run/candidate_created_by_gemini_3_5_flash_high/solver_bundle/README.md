# Solver Instructions - Maritime Freight & Customs Audit (MFCA)

Welcome to the **Maritime Freight & Customs Audit (MFCA)** solver bundle.

Your task is to act as a **Trade Compliance Auditor** and reconcile 30 shipping portfolios. You are provided with a canonical global trade policy, a list of items to solve, and messy raw text documents for each item.

---

## 1. Directory Structure

- `README.md`: This file (instructions and details).
- `trade_policy.md`: The canonical global shipping policy, rate tables, fee percentages, and tariff classifications.
- `items_private_sample.jsonl`: The input JSONL file containing all item IDs and asset filepaths.
- `assets/item_XXX/`: Folder containing raw markdown text files for a specific shipping transaction:
  - `bill_of_lading.md`
  - `commercial_invoice.md`
  - `vessel_port_log.md`
  - `exchange_rates.md`
  - `email_correspondence.md`

---

## 2. Your Task

For each item listed in `items_private_sample.jsonl`:
1. **Extract operational variables**: Container types/counts, commercial invoice cargo value, timestamps for berthing, discharge, gate-out (pick-up), and gate-in (empty return).
2. **Read exchange rates**: Convert the foreign cargo value to USD using the exchange rate active on the **Gate-Out Date** (Customs Declaration Date).
3. **Parse email correspondence**: Identify any operational updates or overrides confirmed in emails (e.g. HS code reclassifications, Incoterms disputes, price corrections, or demurrage waivers).
4. **Compute Customs Value & Duties**: Apply the confirmed Incoterm adjustments, duty rates (and anti-dumping if applicable), Harbor Maintenance Fee (HMF = 0.125%), and Merchandise Processing Fee (MPF = 0.3464%, subject to a \$30.00 minimum and \$600.00 maximum).
5. **Compute Carrier Charges**: Sum the base ocean freight, Low-Sulfur Fuel (LSF) surcharge (\$150/container), Peak Season Surcharge (PSS = \$250/container if gate-out falls in Aug 1st to Oct 31st), demurrage (excluding weekends during standard rate, but retrospectively including weekends if penal stage is reached, subtracting email waivers), and detention.
6. **Classify discrepancy flag**: Categorize the audit reconciliation flag as one of the 5 categories.

---

## 3. Output Format

You must output a JSONL file containing one row per item in this exact schema:
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

- `customs_duty_usd` (float): Stated in USD, rounded to 2 decimal places.
- `carrier_charges_usd` (float): Stated in USD, rounded to 2 decimal places.
- `reconciliation_flag` (string): Must be exactly one of:
  - `"HS_RECLASSIFICATION"`
  - `"INCOTERM_MISMATCH"`
  - `"DEMURRAGE_OVERCHARGE"`
  - `"CURRENCY_VALUATION_ERROR"`
  - `"NO_DISCREPANCY"`
