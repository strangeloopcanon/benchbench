# Maritime General Average & Salvage Forensics (MGAF) — Solver Bundle

## Task Overview

You are given **30 maritime casualty & general average adjustment dossiers** (`mgaf_01` through `mgaf_30`).  
In each case, a commercial cargo vessel encountered a peril at sea, incurred emergency disbursements and/or property sacrifices, entered a Port of Refuge (sometimes following an independent Article 13 Salvage operation), and completed or terminated the maritime adventure.

Your objective for each item (`mgaf_01` through `mgaf_30`) is to determine the **Final Total Assessment Payable by Cargo Interest `Lot-A`** at the termination of the adventure, expressed as an **exact integer in USD cents** (`$1.00 = 100` cents):

$$\text{Answer (USD Cents)} = \text{Salvage}_{\text{Lot-A}} + \text{GA}_{\text{Lot-A}} + \text{SpecialCharges}_{\text{Lot-A}}$$

---

## Solver-Visible Files in `solver_bundle/`

1. `items_private_sample.jsonl` — The 30 benchmark items (`id`: `mgaf_01` to `mgaf_30`), including asset path pointers relative to `solver_bundle/` and summary metadata for each case.
2. `assets/maritime_ga_rulebook.md` — The authoritative **Maritime General Average & Salvage Adjusting Manual** governing all 30 cases (York-Antwerp Rules I, III, V, X, XI, XII, XIII, XIV, XVII, XIX, Rule F, Collect Freight at Risk, Two-Stage Salvage -> GA Cascade, and Non-Separation Agreement Bigham Caps).
3. `assets/fx_and_port_tariffs.csv` — Official schedule of vessel `keel_laid_year` vs `reflagged_year`, exchange rates on `bol_date`, `salvage_date`, and `termination_date`, and Collect Freight / Destination Discharge tariffs.
4. `assets/dossiers_part1.md` — Full operational dossiers (Manifests, Survey Logs, Disbursement Vouchers, and Contemporaneous Telex/Email Correspondence) for `mgaf_01` through `mgaf_10`.
5. `assets/dossiers_part2.md` — Full operational dossiers for `mgaf_11` through `mgaf_20`.
6. `assets/dossiers_part3.md` — Full operational dossiers for `mgaf_21` through `mgaf_30`.

---

## Output Format Contract

Produce predictions in JSONL format where each row contains:
```json
{"id": "mgaf_01", "answer": 999999}
```
- `id`: String item identifier (`"mgaf_01"` through `"mgaf_30"`).
- `answer`: Exact integer USD cents representing the total assessment (`Salvage_Lot_A + GA_Lot_A + SpecialCharges_Lot_A`) payable by `Lot-A`.
