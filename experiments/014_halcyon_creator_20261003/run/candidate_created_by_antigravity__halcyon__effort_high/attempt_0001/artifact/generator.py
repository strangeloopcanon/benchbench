#!/usr/bin/env python3
"""Procedural generator and reference solver for Maritime General Average & Salvage Forensics (MGAF).

CLI Contract:
  python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .
"""

from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import random
from typing import Any


RULEBOOK_MARKDOWN = """# Maritime General Average & Salvage Adjusting Manual (MGAF Consolidated Code)

**Version:** 2025.1 (York-Antwerp Charter Rules & Salvage Cascade Standard)  
**Applicability:** Governs all 30 adjustment dossiers (`mgaf_01` through `mgaf_30`).

---

## 1. Objective & Output Contract

For each case dossier (`mgaf_01` through `mgaf_30`), you act as the Senior Average Adjuster determining the **Final Total Assessment Payable by Cargo Interest `Lot-A`** at the termination of the maritime adventure, expressed as an **exact integer in USD cents** (`$1.00 = 100` cents).

$$\\text{Answer (USD Cents)} = \\text{Salvage}_{\\text{Lot-A}} + \\text{GA}_{\\text{Lot-A}} + \\text{SpecialCharges}_{\\text{Lot-A}}$$

Where:
1. $\\text{Salvage}_{\\text{Lot-A}}$ is `Lot-A`'s Stage 1 Salvage Contribution (in USD cents; `0` if no independent Article 13 Salvage Award occurred).
2. $\\text{GA}_{\\text{Lot-A}}$ is `Lot-A`'s Stage 2 General Average Contribution (in USD cents, subject to any applicable Bigham Clause cap).
3. $\\text{SpecialCharges}_{\\text{Lot-A}}$ is the sum of any Particular / Special Charges incurred specifically for the preservation, reconditioning, or inspection of `Lot-A` alone (in USD cents).
4. **Gross Assessment Rule:** The required answer is `Lot-A`'s **gross assessment contribution** as defined above, prior to netting out any credit distribution (`Made Good`) owed *to* `Lot-A` if `Lot-A` itself suffered a General Average sacrifice.
5. **Rounding Rule:** All intermediate currency conversions and pro-rata contribution shares are evaluated in USD cents and rounded to the nearest integer cent using standard `ROUND_HALF_UP` (halfway cases `.5` round away from zero).

---

## 2. Currency Conversion & Valuation Date Rules (Rule G & Rule XVII)

1. **Governing FX Rate for General Average:** Under York-Antwerp Rule G and Rule XVII, all property values (Sound Value, Physical Damage/Loss, and Amounts Made Good) and foreign-currency General Average disbursements are converted into USD using the exchange rate in force on the **Termination-of-Adventure Date (`TERMINATION_DATE`)** listed in `assets/fx_and_port_tariffs.csv` for that voyage—**never** the Bill of Lading Date (`BOL_DATE`) rate.
2. **Governing FX Rate for Stage 1 Salvage:** If an independent Salvage Award occurs at an intermediate port (`SALVAGE_DATE`), Salved Values for Stage 1 Salvage apportionment are evaluated at the `SALVAGE_DATE` FX rate (which equals the `TERMINATION_DATE` rate unless otherwise noted in the schedule).
3. **Commercial Invoice & Survey Errata:** If a contemporaneous **Surveyor Valuation Erratum**, **Booking Amendment Telex**, or **Lab Moisture Analysis Telex** in the dossier correspondence corrects a clerical invoice transposition or removes non-commercial water-absorption weight gain from a bulk cargo lot, the corrected commercial valuation governs over the unamended Bill of Lading table.

---

## 3. Classification of Physical Losses: General Average Sacrifice (`Made Good`) vs. Particular Average (`PA`)

Physical loss or damage to cargo, vessel, or freight falls into one of two categories:
- **General Average Sacrifice (`Made Good`):** Intentional and reasonable sacrifice of property made for the common safety in time of peril. An allowable sacrifice enters **both**:
  1. The **General Average Pool ($\\text{GA}_{\\text{pool}}$)** (numerator), AND
  2. The sacrificed interest's **Stage 2 Contributory Value ($V_i$)** via the Rule XVII "Made Good" add-back (denominator).
- **Particular Average (`PA` / Non-GA Loss):** Accidental damage caused by marine peril (storm flooding, accidental grounding damage prior to voluntary beaching, collision, machinery breakdown) or losses explicitly excluded from General Average by statute. Particular Average is **excluded (`0`) from the General Average Pool** and reduces the interest's arrived value **without** any "Made Good" add-back.

### 3.1 Rule I — Jettison of Deck Cargo
Jettison of cargo carried **under deck (`UNDER_DECK`)** for the common safety is allowable as General Average Sacrifice.
Jettison of cargo actually stowed **on deck** (`ACTUAL_STOW` in the Stowage Manifest / Survey Log) is governed strictly as follows:
- **`CELLULAR_CONTAINER_DECK`:** Recognized custom of the container trade; jettison for common safety is **ALLOWABLE as General Average Sacrifice**.
- **`TIMBER_WELL_DECK`, `FLAT_RACK_WEATHER_DECK`, or `UNDECLARED_WEATHER_DECK`:** **DISALLOWED in General Average (`Made Good = 0`)**, regardless of whether the Bill of Lading states `ON_DECK_AT_SHIPPER_RISK` or `CONTRACTED_UNDER_DECK` (unauthorized carrier deck stowage is a P&I carrier-liability breach, not a General Average sacrifice). The lost value still reduces the cargo's arrived physical value.

### 3.2 Rule III — Extinguishing Fire on Shipboard
When a fire occurs aboard ship:
- **Extinguishing Water / CO2 / Foam Damage to Unburnt Packages:** Damage caused by water or extinguishing measures to separate packages or cargo lots that were **not yet on fire** is **ALLOWABLE as General Average Sacrifice (`Made Good`)**.
- **Packages Already on Fire:** No compensation (`Made Good = 0`) is made for water or extinguishing damage to packages or bulk portions that were **already actively burning / on fire** when extinguishing measures were applied. Such loss is **Particular Average**.
- **Smoke and Heat Damage:** No compensation (`Made Good = 0`) is made for damage caused by **smoke, soot, or radiant heat** from the fire, however caused. Such loss is **Particular Average**.

### 3.3 Rule V — Voluntary Stranding vs. Accidental Drift
Damage to hull or cargo caused by **intentionally running the vessel ashore** for the common safety is allowable in General Average, whereas damage sustained while drifting ashore accidentally **prior** to the Master's intentional beaching order (as verified by the VDR / Bridge Log Telex) is **Particular Average**.

### 3.4 Rule XII — Damage to Cargo in Discharging, Storage, and Reloading
Damage to cargo sustained during handling, discharging, lighterage, storage, or reloading at a Port of Refuge is allowable as General Average Sacrifice **if and only if** the cost of that handling/discharge operation itself is allowable as General Average (e.g., discharging Hold #1 to access a GA hull fracture). If a cargo lot was discharged solely for its own re-stowing or preservation after shifting in heavy weather, both the discharge cost and any incidental handling damage are **disallowed in General Average** (treated as Particular/Special to that lot).

### 3.5 Rule XIII — Deductions "New for Old" on Vessel Sacrifices
When Vessel hull, machinery, or gear is sacrificed for the common safety:
1. Determine **Vessel Age** at the casualty year (`2025`):
   $$\\text{Vessel Age} = 2025 - \\text{KEEL\\_LAID\\_YEAR}$$
   *(Always use `KEEL_LAID_YEAR` from `assets/fx_and_port_tariffs.csv`, never a later `REFLAGGED_YEAR` or `REBUILT_YEAR` mentioned in narrative headers.)*
2. If $\\text{Vessel Age} \\le 15$: **No deduction (`0`)** "New for Old"; full sacrificial renewal cost is allowed as `Vessel Made Good`.
3. If $\\text{Vessel Age} > 15$:
   - **Machinery, Boilers, Winches, Hull Structure, Bulkheads, Rigging:** Deduct **one-third (`1/3`)** "New for Old" ($\\text{Made Good} = \\frac{2}{3} \\times \\text{Gross Sacrificial Renewal Cost}$).
   - **Chain Cables:** Deduct **one-sixth (`1/6`)** ($\\text{Made Good} = \\frac{5}{6} \\times \\text{Gross Cost}$).
   - **Anchors & Temporary Repairs:** **Exempt (`0` deduction)** ($\\text{Made Good} = 100\\%$ of sacrificial anchor loss; temporary repairs have `0` deduction).
   - **Contributory Value Impact:** The full physical sacrificial loss (`100%` of gross sacrificial damage) reduces the Vessel's physical arrived value, while only the post-deduction `Vessel Made Good` is added back to the Vessel's Contributory Value and the GA Pool.

### 3.6 Rule XIX — Undeclared or Willfully Under-Declared Cargo
If post-casualty customs inspection or commercial audit correspondence reveals that a cargo lot was shipped without notice or **willfully under-declared** on the Bill of Lading at a value lower than its actual commercial CIF value (`DECLARED_CIF < ACTUAL_COMMERCIAL_CIF`):
1. **Forfeiture of `Made Good`:** Any sacrifice or jettison of that misdeclared cargo lot is **DISALLOWED in General Average (`Made Good = 0`)**.
2. **Double Contributory Assessment (`2x` Penalty in Stage 2 GA):** In Stage 2 General Average, the misdeclared lot contributes on **DOUBLE (`2x`) its actual surviving net arrived commercial value**:
   $$V_{\\text{misdeclared}} = 2 \\times (\\text{ActualCommercialSoundValue} - \\text{TotalPhysicalLoss} - \\text{SalvageContribution})$$
3. **Exception for Pre-Sailing Clerical Amendments:** If a shipper submitted an honest clerical invoice correction **prior to sailing** that was accepted by the Carrier/Agent (as documented in the Booking Amendment Telex), Rule XIX does **not** apply; use the amended commercial value at `1x`.

---

## 4. Allowable General Average Disbursements & Expense Vouchers

### 4.1 Port of Refuge Expenses (Rule X) & Detention Crew Wages/Fuel (Rule XI)
Allowable in the General Average Pool:
- Inward and outward port charges, pilotage, towage, and tug assistance to enter/leave a Port of Refuge for common safety.
- Cost of discharging, lightering, storing, and reloading cargo when necessary for the common safety or to allow hull repairs necessary for the safe prosecution of the voyage.
- **Detention Wages, Maintenance, and Fuel (Rule XI):** Crew wages, maintenance, and fuel/stores consumed during the deviation to and detention at the Port of Refuge while common-safety measures or voyage-completion repairs are carried out.
- **Disallowed Post-Repair Detention:** Extra detention days incurred *after* physical vessel repairs are completed due solely to a customs hold or stevedore detention on a specific non-GA cargo lot are **disallowed in GA**. Similarly, normal sea-transit wages and fuel after the vessel resumes its voyage are **disallowed in GA**.

### 4.2 Temporary vs. Permanent Hull Repairs (Rule XIV)
- **Permanent Hull/Machinery Repairs of Accidental Damage:** Always **Particular Average to Vessel (`Disallowed in GA`)**.
- **Temporary Repairs for Common Safety or of GA Sacrifice:** **Allowable in full in GA** (with `0` New-for-Old deduction).
- **Temporary Repairs of Accidental (PA) Damage for Voyage Completion (Rule XIV Cap):** Allowable in GA **only up to the General Average expense strictly avoided** (e.g., avoided GA cost of discharging, storing, and reloading cargo at the Port of Refuge), disregarding any private saving to the Shipowner alone.

### 4.3 Substituted Expenses (Rule F Cap)
When an extra expense is incurred in place of another expense which would have been allowable as General Average (such as towing the vessel to destination or air-freighting a replacement shaft instead of discharging/storing cargo or detaining the ship at the Port of Refuge):
$$\\text{Allowable Substituted Expense in GA} = \\min(\\text{Actual Substituted Expense}, \\text{Avoided General Average Expense})$$
Any saving in non-GA expenses (such as off-hire charter savings or shipowner penalty avoidance) is excluded when computing the Rule F cap.

### 4.4 Superseded Draft Vouchers & Yard Credit Notes
Always reconcile the Adjuster's Expense Table against the **Agent / Yard Correspondence Telexes**:
- Draft vouchers (`STATUS: SUPERSEDED_DRAFT`) replaced by a final voucher must not be double-counted.
- Official Repair Yard or Port Rebate Credit Notes reduce the corresponding allowable voucher amount.

---

## 5. Freight at Risk (`FRT`) & Exempt Property Interests (Rule XVII)

### 5.1 Prepaid vs. Collect Freight
- **`PREPAID_ABSOLUTE` (Freight Prepaid & Non-Returnable):** Freight risk is merged into the CIF value of the cargo lots. Standalone `Freight` has `0` Contributory Value and `0` Made Good.
- **`COLLECT_AT_DESTINATION` (Collect Freight at Carrier's Risk):** Cargo lots (`Lot-A`, `Lot-B`, `Lot-C`) are valued ex-collect-freight, and `Freight` is a **separate 5th Contributory Interest**:
  1. **Net Freight at Risk per Ton:**
     $$\\text{NetFreightPerTon} = \\text{GrossCollectFreightPerTon} - \\text{ContingentDestinationDischargeCostPerTon}$$
  2. **Net Arrived Freight:** Earned on all cargo tons delivered at destination (even if delivered in damaged condition):
     $$\\text{NetArrivedFreight} = \\text{ArrivedTons} \\times \\text{NetFreightPerTon}$$
  3. **Freight Made Good:** Allowed **only** on cargo tons totally lost via an **allowable General Average Sacrifice (jettison)**:
     $$\\text{FreightMadeGood} = \\text{AllowableGAJettisonTons} \\times \\text{NetFreightPerTon}$$
     *(Cargo tons lost via Particular Average storm flooding generate `0` Freight Made Good.)*
  4. **Freight Contributory Value:**
     $$V_{\\text{Freight}} = \\text{NetArrivedFreight} + \\text{FreightMadeGood} - \\text{Salvage}_{\\text{Freight}}$$

### 5.2 Exempt vs. Non-Exempt Additional Manifest Items (Rule XVII)
- **Exempt from Contribution (`V = 0`):** Postal Mails (`MAIL_POUCHES`) and Crew/Passenger Personal Effects (`CREW_BAGGAGE`) are **exempt** from General Average contribution under Rule XVII.
- **Included in Contribution:** Time-Charterer's Bunkers (`TC_BUNKERS`) aboard at termination **must contribute** on their net arrived value.

---

## 6. Two-Stage Casualty Cascade (Salvage -> General Average) & Bigham Cap

### 6.1 Two-Stage Salvage + General Average Cascade
When independent salvors render services under Article 13 (`SALVAGE_AWARD > 0`):
1. **Stage 1 — Salvage Apportionment:**
   - Each interest's **Salved Value ($S_i$)** at the Salvage Termination Port is its actual sound commercial value (`1x`, even for Rule XIX cargo) minus all physical damage and jettison incurred prior to salvage termination:
     $$S_i = \\text{SoundValue}_i - \\text{TotalPhysicalLoss}_i$$
     *(Critically: Do **NOT** add back `Made Good` and do **NOT** apply Rule XIX `2x` doubling in Stage 1 Salvage!)*
   - Apportion the Salvage Award pro-rata over $S_{\\text{total}} = \\sum_j S_j$:
     $$\\text{Salvage}_i = \\text{round\\_half\\_up}\\left(\\text{SalvageAward} \\times \\frac{S_i}{S_{\\text{total}}}\\right)$$
2. **Stage 2 — General Average Apportionment:**
   - Deduct each interest's Stage 1 $\\text{Salvage}_i$ lien from its arrived value before applying Rule XVII `Made Good` add-back (or Rule XIX `2x` doubling):
     - For normal interests:
       $$V_i = (\\text{SoundValue}_i - \\text{TotalPhysicalLoss}_i - \\text{Salvage}_i) + \\text{MadeGood}_i$$
     - For Rule XIX willfully misdeclared interests (`MadeGood = 0`):
       $$V_i = 2 \\times (\\text{ActualCommercialSoundValue}_i - \\text{TotalPhysicalLoss}_i - \\text{Salvage}_i)$$
   - The General Average Pool is:
     $$\\text{GA}_{\\text{pool}} = \\sum_j \\text{MadeGood}_j + \\text{AllowableGAExpenses}$$
     *(The Stage 1 Salvage Award is **not** added into $\\text{GA}_{\\text{pool}}$ because it has already been separately apportioned in Stage 1 and deducted from $V_i$.)*
   - Uncapped GA Contribution for `Lot-A`:
     $$\\text{GA}_{\\text{Lot-A}}^{\\text{uncapped}} = \\text{round\\_half\\_up}\\left(\\text{GA}_{\\text{pool}} \\times \\frac{V_{\\text{Lot-A}}}{\\sum_j V_j}\\right)$$

### 6.2 Non-Separation Agreement & Bigham Clause Cap
If `Lot-A` is forwarded from the Port of Refuge under a Non-Separation Agreement containing a **Bigham Clause Cap ($\\text{Cap}_{\\text{Bigham}}$)**:
$$\\text{GA}_{\\text{Lot-A}} = \\min\\left(\\text{GA}_{\\text{Lot-A}}^{\\text{uncapped}}, \\text{Cap}_{\\text{Bigham}}\\right)$$
- The Bigham Cap applies **solely to $\\text{GA}_{\\text{Lot-A}}$** (Stage 2 General Average contribution). It never caps $\\text{Salvage}_{\\text{Lot-A}}$ (Stage 1 Salvage contribution) or $\\text{SpecialCharges}_{\\text{Lot-A}}$.
- If $\\text{GA}_{\\text{Lot-A}}^{\\text{uncapped}} \\le \\text{Cap}_{\\text{Bigham}}$, the cap does not bind and $\\text{GA}_{\\text{Lot-A}} = \\text{GA}_{\\text{Lot-A}}^{\\text{uncapped}}$.
"""


FX_CSV_CONTENT = """case_id,vessel_name,imo_number,keel_laid_year,reflagged_year,casualty_year,bol_date,termination_date,currency,bol_fx_usd_per_unit,salvage_fx_usd_per_unit,termination_fx_usd_per_unit,freight_mode,gross_collect_freight_usd_per_ton,dest_discharge_cost_usd_per_ton
mgaf_01,MV Northern Star,IMO-9410101,2015,2019,2025,2025-01-10,2025-02-14,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_02,MV Baltic Trader,IMO-9410102,2014,2018,2025,2025-01-18,2025-02-25,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_03,MV Iberian Crown,IMO-9410103,2016,2021,2025,2025-03-02,2025-04-18,EUR,1.1200,1.0500,1.0500,PREPAID_ABSOLUTE,0,0
mgaf_03,MV Iberian Crown,IMO-9410103,2016,2021,2025,2025-03-02,2025-04-18,GBP,1.3000,1.2500,1.2500,PREPAID_ABSOLUTE,0,0
mgaf_03,MV Iberian Crown,IMO-9410103,2016,2021,2025,2025-03-02,2025-04-18,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_04,MV Pacific Horizon,IMO-9410104,2017,2020,2025,2025-04-01,2025-05-12,SGD,0.7800,0.7500,0.7500,PREPAID_ABSOLUTE,0,0
mgaf_04,MV Pacific Horizon,IMO-9410104,2017,2020,2025,2025-04-01,2025-05-12,JPY,0.0070,0.0064,0.0064,PREPAID_ABSOLUTE,0,0
mgaf_04,MV Pacific Horizon,IMO-9410104,2017,2020,2025,2025-04-01,2025-05-12,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_05,MV Adriatic Sun,IMO-9410105,2018,2022,2025,2025-04-10,2025-05-20,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_06,MV Red Sea Falcon,IMO-9410106,2016,2020,2025,2025-04-15,2025-05-28,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_07,MV Coral Empress,IMO-9410107,2015,2019,2025,2025-04-22,2025-06-01,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_08,MV Aegean Glory,IMO-9410108,2015,2020,2025,2025-05-01,2025-06-10,CHF,1.1600,1.1000,1.1000,PREPAID_ABSOLUTE,0,0
mgaf_08,MV Aegean Glory,IMO-9410108,2015,2020,2025,2025-05-01,2025-06-10,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_09,MV Tasman Spirit,IMO-9410109,2014,2019,2025,2025-05-05,2025-06-15,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_10,MV Nordic Fjord,IMO-9410110,2017,2021,2025,2025-05-12,2025-06-22,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_11,MV Lusitania Star,IMO-9410111,2016,2020,2025,2025-05-01,2025-06-09,EUR,1.1400,1.0800,1.0800,PREPAID_ABSOLUTE,0,0
mgaf_11,MV Lusitania Star,IMO-9410111,2016,2020,2025,2025-05-01,2025-06-09,GBP,1.3200,1.2500,1.2500,PREPAID_ABSOLUTE,0,0
mgaf_11,MV Lusitania Star,IMO-9410111,2016,2020,2025,2025-05-01,2025-06-09,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_12,MV Timber King,IMO-9410112,2015,2019,2025,2025-05-18,2025-06-25,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_13,MV Iron Monarch,IMO-9410113,2006,2016,2025,2025-05-20,2025-06-28,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_14,MV Caledonia,IMO-9410114,2014,2018,2025,2025-05-25,2025-07-01,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_15,MV Kowloon Express,IMO-9410115,2013,2019,2025,2025-05-28,2025-07-02,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_16,MV Cape Horn,IMO-9410116,2004,2017,2025,2025-06-01,2025-07-03,EUR,1.1200,1.0500,1.0500,PREPAID_ABSOLUTE,0,0
mgaf_16,MV Cape Horn,IMO-9410116,2004,2017,2025,2025-06-01,2025-07-03,SGD,0.7800,0.7500,0.7500,PREPAID_ABSOLUTE,0,0
mgaf_16,MV Cape Horn,IMO-9410116,2004,2017,2025,2025-06-01,2025-07-03,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_17,MV Borealis,IMO-9410117,2015,2020,2025,2025-06-05,2025-07-12,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_18,MV Emerald Isle,IMO-9410118,2016,2021,2025,2025-06-10,2025-07-18,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_19,MV Levant Express,IMO-9410119,2015,2019,2025,2025-06-15,2025-07-24,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_20,MV Atlantic Carrier,IMO-9410120,2014,2018,2025,2025-06-20,2025-08-02,USD,1.0000,1.0000,1.0000,COLLECT_AT_DESTINATION,100,20
mgaf_21,MV Horn of Africa,IMO-9410121,2007,2018,2025,2025-06-25,2025-08-08,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_22,MV Strait of Malacca,IMO-9410122,2015,2020,2025,2025-07-01,2025-08-14,EUR,1.1000,1.0500,1.0500,COLLECT_AT_DESTINATION,120,20
mgaf_22,MV Strait of Malacca,IMO-9410122,2015,2020,2025,2025-07-01,2025-08-14,GBP,1.2800,1.2000,1.2000,COLLECT_AT_DESTINATION,120,20
mgaf_22,MV Strait of Malacca,IMO-9410122,2015,2020,2025,2025-07-01,2025-08-14,USD,1.0000,1.0000,1.0000,COLLECT_AT_DESTINATION,120,20
mgaf_23,MV Hansa Merchant,IMO-9410123,2016,2021,2025,2025-07-05,2025-08-19,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_24,MV Orion,IMO-9410124,2015,2020,2025,2025-07-10,2025-08-25,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_25,MV Bosphorus Queen,IMO-9410125,2014,2019,2025,2025-07-15,2025-08-30,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_26,MV Southern Cross,IMO-9410126,2005,2017,2025,2025-07-20,2025-09-04,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_27,MV Tyrrhenian Sea,IMO-9410127,2016,2020,2025,2025-07-25,2025-09-10,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_28,MV Polar Endurance,IMO-9410128,2015,2021,2025,2025-08-01,2025-09-15,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_29,MV Magellan,IMO-9410129,2014,2019,2025,2025-08-05,2025-09-20,USD,1.0000,1.0000,1.0000,PREPAID_ABSOLUTE,0,0
mgaf_30,MV Sovereign of the Seas,IMO-9410130,2006,2018,2025,2025-08-10,2025-09-28,GBP,1.3200,1.2500,1.2500,COLLECT_AT_DESTINATION,100,20
mgaf_30,MV Sovereign of the Seas,IMO-9410130,2006,2018,2025,2025-08-10,2025-09-28,USD,1.0000,1.0000,1.0000,COLLECT_AT_DESTINATION,100,20
"""


CANONICAL_CASES: list[dict[str, Any]] = [
    {
        "id": "mgaf_01",
        "vessel": "MV Northern Star",
        "imo": "IMO-9410101",
        "voyage": "VOY-01",
        "reflagged": 2019,
        "keel_laid": 2015,
        "bol_date": "2025-01-10",
        "term_date": "2025-02-14",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 120000,
        "lot_a_special_cents": 124550,
        "interests": [
            {"name": "Lot-A", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2610000, "pa_loss_usd": 110000, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_02",
        "vessel": "MV Baltic Trader",
        "imo": "IMO-9410102",
        "voyage": "VOY-02",
        "reflagged": 2018,
        "keel_laid": 2014,
        "bol_date": "2025-01-18",
        "term_date": "2025-02-25",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 200000,
        "lot_a_special_cents": 84025,
        "interests": [
            {"name": "Lot-A", "sound_usd": 750000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 900000, "pa_loss_usd": 150000, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 3200000, "pa_loss_usd": 200000, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_03",
        "vessel": "MV Iberian Crown",
        "imo": "IMO-9410103",
        "voyage": "VOY-03",
        "reflagged": 2021,
        "keel_laid": 2016,
        "bol_date": "2025-03-02",
        "term_date": "2025-04-18",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 150000,
        "lot_a_special_cents": 0,
        "interests": [
            {"name": "Lot-A", "sound_usd": 420000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 380000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 1700000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_04",
        "vessel": "MV Pacific Horizon",
        "imo": "IMO-9410104",
        "voyage": "VOY-04",
        "reflagged": 2020,
        "keel_laid": 2017,
        "bol_date": "2025-04-01",
        "term_date": "2025-05-12",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 188000,
        "lot_a_special_cents": 141080,
        "interests": [
            {"name": "Lot-A", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 640000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 360000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_05",
        "vessel": "MV Adriatic Sun",
        "imo": "IMO-9410105",
        "voyage": "VOY-05",
        "reflagged": 2022,
        "keel_laid": 2018,
        "bol_date": "2025-04-10",
        "term_date": "2025-05-20",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 75000,
        "lot_a_special_cents": 0,
        "interests": [
            {"name": "Lot-A", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 100000},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 1000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_06",
        "vessel": "MV Red Sea Falcon",
        "imo": "IMO-9410106",
        "voyage": "VOY-06",
        "reflagged": 2020,
        "keel_laid": 2016,
        "bol_date": "2025-04-15",
        "term_date": "2025-05-28",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 110000,
        "lot_a_special_cents": 62500,
        "interests": [
            {"name": "Lot-A", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 800000, "pa_loss_usd": 160000, "gross_ga_sacrifice_usd": 90000},
            {"name": "Lot-C", "sound_usd": 360000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_07",
        "vessel": "MV Coral Empress",
        "imo": "IMO-9410107",
        "voyage": "VOY-07",
        "reflagged": 2019,
        "keel_laid": 2015,
        "bol_date": "2025-04-22",
        "term_date": "2025-06-01",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 90000,
        "lot_a_special_cents": 115075,
        "interests": [
            {"name": "Lot-A", "sound_usd": 700000, "pa_loss_usd": 100000, "gross_ga_sacrifice_usd": 60000},
            {"name": "Lot-B", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 1500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_08",
        "vessel": "MV Aegean Glory",
        "imo": "IMO-9410108",
        "voyage": "VOY-08",
        "reflagged": 2020,
        "keel_laid": 2015,
        "bol_date": "2025-05-01",
        "term_date": "2025-06-10",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 120000,
        "lot_a_special_cents": 0,
        "interests": [
            {"name": "Lot-A", "sound_usd": 550000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 650000, "pa_loss_usd": 50000, "gross_ga_sacrifice_usd": 80000},
            {"name": "Lot-C", "sound_usd": 350000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2700000, "pa_loss_usd": 200000, "gross_ga_sacrifice_usd": 120000},
        ],
    },
    {
        "id": "mgaf_09",
        "vessel": "MV Tasman Spirit",
        "imo": "IMO-9410109",
        "voyage": "VOY-09",
        "reflagged": 2019,
        "keel_laid": 2014,
        "bol_date": "2025-05-05",
        "term_date": "2025-06-15",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 180000,
        "lot_a_special_cents": 231040,
        "interests": [
            {"name": "Lot-A", "sound_usd": 900000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 700000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 70000},
            {"name": "Lot-C", "sound_usd": 450000, "pa_loss_usd": 50000, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 3000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_10",
        "vessel": "MV Nordic Fjord",
        "imo": "IMO-9410110",
        "voyage": "VOY-10",
        "reflagged": 2021,
        "keel_laid": 2017,
        "bol_date": "2025-05-12",
        "term_date": "2025-06-22",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 160000,
        "lot_a_special_cents": 49000,
        "interests": [
            {"name": "Lot-A", "sound_usd": 450000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 600000, "pa_loss_usd": 120000, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 570000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 1500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_11",
        "vessel": "MV Lusitania Star",
        "imo": "IMO-9410111",
        "voyage": "VOY-11",
        "reflagged": 2020,
        "keel_laid": 2016,
        "bol_date": "2025-05-01",
        "term_date": "2025-06-09",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 130000,
        "lot_a_special_cents": 175060,
        "interests": [
            {"name": "Lot-A", "sound_usd": 540000, "pa_loss_usd": 40000, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 100000},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 60000, "gross_ga_sacrifice_usd": 50000},
            {"name": "Vessel", "sound_usd": 2660000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_12",
        "vessel": "MV Timber King",
        "imo": "IMO-9410112",
        "voyage": "VOY-12",
        "reflagged": 2019,
        "keel_laid": 2015,
        "bol_date": "2025-05-18",
        "term_date": "2025-06-25",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 160000,
        "lot_a_special_cents": 0,
        "interests": [
            {"name": "Lot-A", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 720000, "pa_loss_usd": 120000, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 80000},
            {"name": "Vessel", "sound_usd": 2500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_13",
        "vessel": "MV Iron Monarch",
        "imo": "IMO-9410113",
        "voyage": "VOY-13",
        "reflagged": 2016,
        "keel_laid": 2006,
        "bol_date": "2025-05-20",
        "term_date": "2025-06-28",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 150000,
        "lot_a_special_cents": 92050,
        "interests": [
            {"name": "Lot-A", "sound_usd": 800000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            # 180k machinery (1/3 ded = 60k) + 30k anchor (0 ded) + 60k chain (1/6 ded = 10k) -> 270k gross, 70k ded -> 200k Made Good
            {"name": "Vessel", "sound_usd": 3270000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 270000, "rule_xiii_deduction_num_den": (7, 27)},
        ],
    },
    {
        "id": "mgaf_14",
        "vessel": "MV Caledonia",
        "imo": "IMO-9410114",
        "voyage": "VOY-14",
        "reflagged": 2018,
        "keel_laid": 2014,
        "bol_date": "2025-05-25",
        "term_date": "2025-07-01",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 190000,
        "lot_a_special_cents": 0,
        "interests": [
            {"name": "Lot-A", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 1500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_15",
        "vessel": "MV Kowloon Express",
        "imo": "IMO-9410115",
        "voyage": "VOY-15",
        "reflagged": 2019,
        "keel_laid": 2013,
        "bol_date": "2025-05-28",
        "term_date": "2025-07-02",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 150000,
        "lot_a_special_cents": 133020,
        "interests": [
            {"name": "Lot-A", "sound_usd": 700000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 600000, "pa_loss_usd": 100000, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 90000},
        ],
    },
    {
        "id": "mgaf_16",
        "vessel": "MV Cape Horn",
        "imo": "IMO-9410116",
        "voyage": "VOY-16",
        "reflagged": 2017,
        "keel_laid": 2004,
        "bol_date": "2025-06-01",
        "term_date": "2025-07-03",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 130000,
        "lot_a_special_cents": 212000,
        "interests": [
            {"name": "Lot-A", "sound_usd": 840000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 600000, "pa_loss_usd": 60000, "gross_ga_sacrifice_usd": 90000},
            {"name": "Lot-C", "sound_usd": 420000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2230000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 90000, "rule_xiii_deduction_num_den": (1, 3)},
        ],
    },
    {
        "id": "mgaf_17",
        "vessel": "MV Borealis",
        "imo": "IMO-9410117",
        "voyage": "VOY-17",
        "reflagged": 2020,
        "keel_laid": 2015,
        "bol_date": "2025-06-05",
        "term_date": "2025-07-12",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 180000,
        "lot_a_special_cents": 64050,
        "interests": [
            {"name": "Lot-A", "sound_usd": 450000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 550000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 1500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_18",
        "vessel": "MV Emerald Isle",
        "imo": "IMO-9410118",
        "voyage": "VOY-18",
        "reflagged": 2021,
        "keel_laid": 2016,
        "bol_date": "2025-06-10",
        "term_date": "2025-07-18",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 200000,
        "lot_a_special_cents": 0,
        "interests": [
            {"name": "Lot-A", "sound_usd": 900000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 700000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_19",
        "vessel": "MV Levant Express",
        "imo": "IMO-9410119",
        "voyage": "VOY-19",
        "reflagged": 2019,
        "keel_laid": 2015,
        "bol_date": "2025-06-15",
        "term_date": "2025-07-24",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 160000,
        "lot_a_special_cents": 118000,
        "interests": [
            {"name": "Lot-A", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 450000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 50000, "rule_xix_double": True},
            {"name": "Lot-C", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2100000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_20",
        "vessel": "MV Atlantic Carrier",
        "imo": "IMO-9410120",
        "voyage": "VOY-20",
        "reflagged": 2018,
        "keel_laid": 2014,
        "bol_date": "2025-06-20",
        "term_date": "2025-08-02",
        "freight_terms": "COLLECT_AT_DESTINATION",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 130000,
        "lot_a_special_cents": 45025,
        "interests": [
            {"name": "Lot-A", "sound_usd": 800000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 1000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 200000},
            {"name": "Lot-C", "sound_usd": 560000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Freight", "sound_usd": 240000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 20000},
        ],
    },
    {
        "id": "mgaf_21",
        "vessel": "MV Horn of Africa",
        "imo": "IMO-9410121",
        "voyage": "VOY-21",
        "reflagged": 2018,
        "keel_laid": 2007,
        "bol_date": "2025-06-25",
        "term_date": "2025-08-08",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 150000,
        "lot_a_special_cents": 189000,
        "interests": [
            {"name": "Lot-A", "sound_usd": 700000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 1200000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 300000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0, "rule_xix_double": True},
            {"name": "Vessel", "sound_usd": 2550000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 150000, "rule_xiii_deduction_num_den": (1, 3)},
        ],
    },
    {
        "id": "mgaf_22",
        "vessel": "MV Strait of Malacca",
        "imo": "IMO-9410122",
        "voyage": "VOY-22",
        "reflagged": 2020,
        "keel_laid": 2015,
        "bol_date": "2025-07-01",
        "term_date": "2025-08-14",
        "freight_terms": "COLLECT_AT_DESTINATION",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 140000,
        "lot_a_special_cents": 72550,
        "interests": [
            {"name": "Lot-A", "sound_usd": 630000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 720000, "pa_loss_usd": 120000, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 390000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 50000},
            {"name": "Vessel", "sound_usd": 2200000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Freight", "sound_usd": 200000, "pa_loss_usd": 20000, "gross_ga_sacrifice_usd": 10000},
        ],
    },
    {
        "id": "mgaf_23",
        "vessel": "MV Hansa Merchant",
        "imo": "IMO-9410123",
        "voyage": "VOY-23",
        "reflagged": 2021,
        "keel_laid": 2016,
        "bol_date": "2025-07-05",
        "term_date": "2025-08-19",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 240000,
        "lot_a_special_cents": 0,
        "interests": [
            {"name": "Lot-A", "sound_usd": 550000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 650000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 250000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0, "rule_xix_double": True},
            {"name": "Vessel", "sound_usd": 2300000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_24",
        "vessel": "MV Orion",
        "imo": "IMO-9410124",
        "voyage": "VOY-24",
        "reflagged": 2020,
        "keel_laid": 2015,
        "bol_date": "2025-07-10",
        "term_date": "2025-08-25",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 200000,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 100000,
        "lot_a_special_cents": 0,
        "interests": [
            {"name": "Lot-A", "sound_usd": 800000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 1000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 200000},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_25",
        "vessel": "MV Bosphorus Queen",
        "imo": "IMO-9410125",
        "voyage": "VOY-25",
        "reflagged": 2019,
        "keel_laid": 2014,
        "bol_date": "2025-07-15",
        "term_date": "2025-08-30",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": 54500,
        "allowable_ga_vouchers_usd": 350000,
        "lot_a_special_cents": 132000,
        "interests": [
            {"name": "Lot-A", "sound_usd": 1000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 800000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 700000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_26",
        "vessel": "MV Southern Cross",
        "imo": "IMO-9410126",
        "voyage": "VOY-26",
        "reflagged": 2017,
        "keel_laid": 2005,
        "bol_date": "2025-07-20",
        "term_date": "2025-09-04",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 200000,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 100000,
        "lot_a_special_cents": 85000,
        "interests": [
            {"name": "Lot-A", "sound_usd": 1000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 800000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 700000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2800000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 300000, "rule_xiii_deduction_num_den": (1, 3)},
        ],
    },
    {
        "id": "mgaf_27",
        "vessel": "MV Tyrrhenian Sea",
        "imo": "IMO-9410127",
        "voyage": "VOY-27",
        "reflagged": 2020,
        "keel_laid": 2016,
        "bol_date": "2025-07-25",
        "term_date": "2025-09-10",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 0,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 240000,
        "lot_a_special_cents": 42075,
        "interests": [
            {"name": "Lot-A", "sound_usd": 650000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-C", "sound_usd": 400000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2200000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "TC_Bunkers", "sound_usd": 150000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Mail_Pouches", "sound_usd": 0, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Crew_Baggage", "sound_usd": 0, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_28",
        "vessel": "MV Polar Endurance",
        "imo": "IMO-9410128",
        "voyage": "VOY-28",
        "reflagged": 2021,
        "keel_laid": 2015,
        "bol_date": "2025-08-01",
        "term_date": "2025-09-15",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 500000,
        "bigham_cap_usd": None,
        "allowable_ga_vouchers_usd": 150000,
        "lot_a_special_cents": 154000,
        "interests": [
            {"name": "Lot-A", "sound_usd": 1000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 950000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 50000},
            {"name": "Lot-C", "sound_usd": 500000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0, "rule_xix_double": True},
            {"name": "Vessel", "sound_usd": 2600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_29",
        "vessel": "MV Magellan",
        "imo": "IMO-9410129",
        "voyage": "VOY-29",
        "reflagged": 2019,
        "keel_laid": 2014,
        "bol_date": "2025-08-05",
        "term_date": "2025-09-20",
        "freight_terms": "PREPAID_ABSOLUTE",
        "salvage_award_usd": 150000,
        "bigham_cap_usd": 42000,
        "allowable_ga_vouchers_usd": 250000,
        "lot_a_special_cents": 91025,
        "interests": [
            {"name": "Lot-A", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 950000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 150000},
            {"name": "Lot-C", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
    {
        "id": "mgaf_30",
        "vessel": "MV Sovereign of the Seas",
        "imo": "IMO-9410130",
        "voyage": "VOY-30",
        "reflagged": 2018,
        "keel_laid": 2006,
        "bol_date": "2025-08-10",
        "term_date": "2025-09-28",
        "freight_terms": "COLLECT_AT_DESTINATION",
        "salvage_award_usd": 250000,
        "bigham_cap_usd": 85000,
        "allowable_ga_vouchers_usd": 150000,
        "lot_a_special_cents": 248050,
        "interests": [
            {"name": "Lot-A", "sound_usd": 1000000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Lot-B", "sound_usd": 1050000, "pa_loss_usd": 100000, "gross_ga_sacrifice_usd": 150000},
            {"name": "Lot-C", "sound_usd": 600000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
            {"name": "Vessel", "sound_usd": 2550000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 150000, "rule_xiii_deduction_num_den": (1, 3)},
            {"name": "Freight", "sound_usd": 200000, "pa_loss_usd": 0, "gross_ga_sacrifice_usd": 0},
        ],
    },
]


def round_half_up_int(val: Decimal) -> int:
    return int(val.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def solve_case(case: dict[str, Any]) -> int:
    """Exact two-stage Maritime General Average & Salvage reference adjuster."""
    salved_cents: dict[str, int] = {}
    made_good_cents: dict[str, int] = {}
    rule_xix_flags: dict[str, bool] = {}

    for item in case["interests"]:
        name = item["name"]
        sound_c = int(Decimal(str(item["sound_usd"])) * 100)
        pa_c = int(Decimal(str(item["pa_loss_usd"])) * 100)
        gross_sac_c = int(Decimal(str(item["gross_ga_sacrifice_usd"])) * 100)
        num, den = item.get("rule_xiii_deduction_num_den", (0, 1))
        ded_c = (gross_sac_c * num) // den
        is_xix = bool(item.get("rule_xix_double", False))
        rule_xix_flags[name] = is_xix
        made_good_cents[name] = 0 if is_xix else (gross_sac_c - ded_c)
        salved_cents[name] = sound_c - pa_c - gross_sac_c

    salvage_award_c = int(Decimal(str(case["salvage_award_usd"])) * 100)
    salvage_contrib_c: dict[str, int] = {}
    if salvage_award_c > 0:
        total_salved_c = sum(salved_cents.values())
        for name, s_c in salved_cents.items():
            salvage_contrib_c[name] = round_half_up_int(
                Decimal(salvage_award_c) * Decimal(s_c) / Decimal(total_salved_c)
            )
    else:
        for name in salved_cents:
            salvage_contrib_c[name] = 0

    contrib_val_c: dict[str, int] = {}
    for name, s_c in salved_cents.items():
        net_arrived_c = s_c - salvage_contrib_c[name]
        if rule_xix_flags[name]:
            contrib_val_c[name] = 2 * net_arrived_c
        else:
            contrib_val_c[name] = net_arrived_c + made_good_cents[name]

    total_contrib_c = sum(contrib_val_c.values())
    ga_pool_c = sum(made_good_cents.values()) + int(
        Decimal(str(case["allowable_ga_vouchers_usd"])) * 100
    )
    lot_a_ga_uncapped_c = round_half_up_int(
        Decimal(ga_pool_c) * Decimal(contrib_val_c["Lot-A"]) / Decimal(total_contrib_c)
    )

    if case.get("bigham_cap_usd") is not None:
        bigham_cap_c = int(Decimal(str(case["bigham_cap_usd"])) * 100)
        lot_a_ga_c = min(lot_a_ga_uncapped_c, bigham_cap_c)
    else:
        lot_a_ga_c = lot_a_ga_uncapped_c

    return salvage_contrib_c["Lot-A"] + lot_a_ga_c + int(case["lot_a_special_cents"])


DOSSIERS_PART1_MD = """# Maritime General Average & Salvage Forensic Dossiers — Part 1 (`mgaf_01` to `mgaf_10`)

---

## CASE `mgaf_01` — MV Northern Star (Voyage VOY-01)
- **Vessel:** MV Northern Star (`IMO-9410101`) | **Reflagged:** 2019 (See `assets/fx_and_port_tariffs.csv` for official `keel_laid_year`)
- **Bill of Lading Date:** `2025-01-10` | **Termination of Adventure Date:** `2025-02-14`
- **Freight Terms:** `PREPAID_ABSOLUTE` (Merged into Cargo CIF)
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 1.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-01A | USD | 400,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-01B | USD | 600,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-01C | USD | 500,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-01 | USD | 2,610,000.00 | Hull & Machinery | N/A |

### 1.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | No physical loss; minor condensation treated via special dehumidification. |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 110,000.00 USD | HULL_FRACTURE | Accidental bottom shell plating fracture sustained when vessel grounded on uncharted sandbar prior to refloating operations. |

### 1.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-0101` | Harbor Tug Corp | 85,000.00 | USD | FINAL_PAID | Emergency tug assistance to refloat vessel from sandbar for common safety of ship and cargo. |
| `VCH-0102` | Refuge Port Authority | 35,000.00 | USD | FINAL_PAID | Port of refuge inward/outward pilotage, towage, and port dues for common safety inspection. |
| `VCH-0103` | Drydock & Steel Ltd | 110,000.00 | USD | FINAL_PAID | Permanent replacement of fractured bottom shell plating sustained in accidental grounding. |
| `VCH-0104` | CargoCare Specialists | 1,245.50 | USD | FINAL_PAID | Dehumidification and desiccant repacking performed exclusively on `Lot-A` containers at port of refuge. |

### 1.4 Contemporaneous Telex & Email Correspondence
- **TELEX-01A (From: Senior Hull Surveyor, To: Average Adjuster):** "Confirm the `$110,000.00` bottom shell damage (`VCH-0103`) was sustained immediately upon accidental grounding before refloating tugs were engaged. It is accidental Particular Average to the Vessel, not a General Average sacrifice."
- **TELEX-01B (From: Cargo Surveyor, To: Adjuster):** "`VCH-0104` (`$1,245.50`) was requested solely by `Lot-A` underwriters for `Lot-A` silica-gel repacking; allocate exclusively to `Lot-A`."

---

## CASE `mgaf_02` — MV Baltic Trader (Voyage VOY-02)
- **Vessel:** MV Baltic Trader (`IMO-9410102`) | **Reflagged:** 2018
- **Bill of Lading Date:** `2025-01-18` | **Termination of Adventure Date:** `2025-02-25`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 2.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-02A | USD | 750,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-02B | USD | 900,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-02C | USD | 500,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-02 | USD | 3,200,000.00 | Hull & Machinery | N/A |

### 2.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 150,000.00 USD | WATER_INGRESS | Accidental sea-water ingress through storm-damaged ventilator cowl during heavy gale prior to deviation. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 200,000.00 USD | SHAFT_FRACTURE | Accidental fatigue fracture of main propulsion tailshaft in heavy seas. |

### 2.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-0201` | DeepSea Towage Co | 140,000.00 | USD | FINAL_PAID | Emergency ocean tug assistance towing disabled vessel into Port of Refuge for common safety. |
| `VCH-0202` | Refuge Port Authority | 40,000.00 | USD | FINAL_PAID | Inward/outward port charges, pilotage, and berthage at Port of Refuge. |
| `VCH-0203` | Master's Portage Bill | 20,000.00 | USD | FINAL_PAID | Crew wages, maintenance, and fuel consumed during detention at Port of Refuge under Rule XI. |
| `VCH-0204` | Master's Portage Bill | 15,000.00 | USD | FINAL_PAID | Crew wages and fuel consumed during normal sea transit after resuming original voyage track. |
| `VCH-0205` | Nordic Marine Works | 200,000.00 | USD | FINAL_PAID | Permanent replacement of fractured tailshaft (`SHAFT_FRACTURE`). |
| `VCH-0206` | Survey Associates | 840.25 | USD | FINAL_PAID | Special thermographic inspection billed exclusively to `Lot-A` cargo interest. |

### 2.4 Contemporaneous Telex & Email Correspondence
- **TELEX-02A (From: Joint Surveyor, To: Adjuster):** "Both the `$150,000.00` storm water damage to `Lot-B` and the `$200,000.00` tailshaft fracture on `Vessel` were accidental marine perils sustained prior to any General Average act."
- **TELEX-02B (From: Adjuster Audit Note):** "`VCH-0204` (`$15,000.00`) covers normal sea transit after leaving the Port of Refuge. `VCH-0205` (`$200,000.00`) covers permanent repair of the accidental shaft fracture. `VCH-0206` (`$840.25`) was incurred exclusively for `Lot-A`."

---

## CASE `mgaf_03` — MV Iberian Crown (Voyage VOY-03)
- **Vessel:** MV Iberian Crown (`IMO-9410103`) | **Reflagged:** 2021
- **Bill of Lading Date:** `2025-03-02` | **Termination of Adventure Date:** `2025-04-18`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 3.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-03A | EUR | 400,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-03B | GBP | 400,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-03C | USD | 380,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-03 | USD | 1,700,000.00 | Hull & Machinery | N/A |

### 3.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 EUR | SOUND | Arrived sound at destination. |
| `Lot-B` | 0.00 GBP | SOUND | Arrived sound at destination. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound at destination. |
| `Vessel` | 0.00 USD | NET_ARRIVED | `$1,700,000.00` USD stated in Section 3.1 is already net of minor storm wear. |

### 3.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-0301` | Lisbon Refuge Port | 62,000.00 | USD | FINAL_PAID | Refuge port entry/exit dues, pilotage, and mooring for common safety. |
| `VCH-0302-DRAFT` | Tagus Towage SA | 45,000.00 | USD | SUPERSEDED_DRAFT | Preliminary pro-forma estimate for emergency tug assistance. |
| `VCH-0302-FINAL` | Tagus Towage SA | 58,000.00 | USD | FINAL_PAID | Final settled invoice for emergency tug assistance. |
| `VCH-0303` | Master's Portage Bill | 30,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel during Port of Refuge stay. |

### 3.4 Contemporaneous Telex & Email Correspondence
- **TELEX-03A (From: Port Agent Lisbon, To: Adjuster):** "`VCH-0302-DRAFT` (`$45,000.00`) was an initial unbilled estimate replaced in full by `VCH-0302-FINAL` (`$58,000.00`). Do not double-count the draft voucher."
- **TELEX-03B (From: Cargo Underwriter Query, To: Adjuster):** "Shippers of `Lot-A` (`400,000 EUR`) and `Lot-B` (`400,000 GBP`) attached their Bill of Lading Date (`2025-03-02`) exchange rates to their commercial invoices. Apply the governing valuation date rate from `assets/fx_and_port_tariffs.csv` per the Adjusting Manual."

---

## CASE `mgaf_04` — MV Pacific Horizon (Voyage VOY-04)
- **Vessel:** MV Pacific Horizon (`IMO-9410104`) | **Reflagged:** 2020
- **Bill of Lading Date:** `2025-04-01` | **Termination of Adventure Date:** `2025-05-12`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 4.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-04A | SGD | 800,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-04B | JPY | 100,000,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-04C | USD | 360,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-04 | USD | 2,400,000.00 | Hull & Machinery | N/A |

### 4.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 SGD | SOUND | Arrived sound. |
| `Lot-B` | 0.00 JPY | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,400,000.00` USD at termination. |

### 4.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-0401` | Straits Salvage & Lighterage | 160,000.00 | SGD | FINAL_PAID | Emergency tug & lighterage at Port of Refuge for common safety (paid in SGD). |
| `VCH-0402` | Jurong Port Authority | 48,000.00 | USD | FINAL_PAID | Refuge port dues, pilotage, and Rule XI detention fuel/wages. |
| `VCH-0403` | Keppel Repair Dock | 32,000.00 | USD | FINAL_PAID | Temporary hull patch required for common safety at Port of Refuge. |
| `VCH-0404` | ColdChain Inspect Pte | 1,410.80 | USD | FINAL_PAID | Special reefer telemetry audit requested for `Lot-A` only. |

### 4.4 Contemporaneous Telex & Email Correspondence
- **TELEX-04A (From: Keppel Repair Dock Accounting, To: Master & Adjuster):** "We hereby issue Official Credit Note `CN-0403` for `$12,000.00` USD against `VCH-0403` (`$32,000.00` USD) due to unused steel cofferdam rental."
- **TELEX-04B (From: Port Agent Singapore):** "`VCH-0401` (`160,000.00 SGD`) is an allowable General Average disbursement; convert all foreign-currency values and disbursements at the governing FX rate in `assets/fx_and_port_tariffs.csv`. `VCH-0404` (`$1,410.80` USD) pertains solely to `Lot-A`."

---

## CASE `mgaf_05` — MV Adriatic Sun (Voyage VOY-05)
- **Vessel:** MV Adriatic Sun (`IMO-9410105`) | **Reflagged:** 2022
- **Bill of Lading Date:** `2025-04-10` | **Termination of Adventure Date:** `2025-05-20`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 5.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-05A | USD | 500,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-05B | USD | 600,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-05C | USD | 400,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-05 | USD | 1,000,000.00 | Hull & Machinery | N/A |

### 5.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 100,000.00 USD | JETTISON_UNDER_DECK | `$100,000.00` of `Lot-B` steel coils stowed in Hold #2 (`UNDER_DECK`) were intentionally jettisoned by Master's order to lighten the ship and refloat from reef. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$1,000,000.00` USD. |

### 5.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-0501` | Bari Tug & Pilotage | 50,000.00 | USD | FINAL_PAID | Emergency tug and pilotage into Port of Refuge for common safety. |
| `VCH-0502` | Master's Portage Bill | 25,000.00 | USD | FINAL_PAID | Rule XI detention wages and fuel during Port of Refuge survey and trim adjustment. |

### 5.4 Contemporaneous Telex & Email Correspondence
- **TELEX-05A (From: Cargo Surveyor Bari, To: Adjuster):** "Verified that the `$100,000.00` jettison of `Lot-B` was taken from Hold #2 (`UNDER_DECK`) for the common safety of vessel and cargo during refloating operations."

---

## CASE `mgaf_06` — MV Red Sea Falcon (Voyage VOY-06)
- **Vessel:** MV Red Sea Falcon (`IMO-9410106`) | **Reflagged:** 2020
- **Bill of Lading Date:** `2025-04-15` | **Termination of Adventure Date:** `2025-05-28`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 6.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-06A | USD | 600,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-06B | USD | 800,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-06C | USD | 360,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-06 | USD | 2,400,000.00 | Hull & Machinery | N/A |

### 6.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound in Hold #1. |
| `Lot-B` | 250,000.00 USD | HOLD_FIRE_AND_WATER | Combined damage in Hold #2 during fire-fighting operation (see Forensic Thermal Telex `TELEX-06A`). |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound in Hold #3. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,400,000.00` USD. |

### 6.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-0601` | FireFighting Tugs Jeddah | 70,000.00 | USD | FINAL_PAID | Emergency fire-fighting tug and CO2 recharge at Port of Refuge for common safety. |
| `VCH-0602` | Jeddah Port & Detention | 40,000.00 | USD | FINAL_PAID | Refuge port dues and Rule XI detention crew wages/fuel. |
| `VCH-0603` | Hold-1 Air Scrubbing Co | 625.00 | USD | FINAL_PAID | Special ozone deodorization service requested solely by `Lot-A` consignee. |

### 6.4 Contemporaneous Telex & Email Correspondence
- **TELEX-06A (From: Forensic Fire & Thermal Surveyor, To: Adjuster):** "We completed package-by-package inspection of the `$250,000.00` loss to `Lot-B` in Hold #2:
  1. `$90,000.00` was water saturation damage from fire hoses to separate lower-tier crates that had **no fire or char contact whatsoever**.
  2. `$100,000.00` was damage to crates that were **already actively burning** when hold flooding commenced.
  3. `$60,000.00` was **smoke and soot discoloration only** on dry upper-tier crates."
- **TELEX-06B (From: Port Agent Jeddah):** "`VCH-0603` (`$625.00`) was ordered solely for `Lot-A` containers."

---

## CASE `mgaf_07` — MV Coral Empress (Voyage VOY-07)
- **Vessel:** MV Coral Empress (`IMO-9410107`) | **Reflagged:** 2019
- **Bill of Lading Date:** `2025-04-22` | **Termination of Adventure Date:** `2025-06-01`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 7.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-07A | USD | 700,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-07B | USD | 500,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-07C | USD | 400,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-07 | USD | 1,500,000.00 | Hull & Machinery | N/A |

### 7.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 160,000.00 USD | HOLD_FIRE_AND_WATER | Combined Hold #1 fire-extinguishing and smoke loss to `Lot-A` (see `TELEX-07A`). |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$1,500,000.00` USD. |

### 7.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-0701` | Colombo Port & Fire Tugs | 62,000.00 | USD | FINAL_PAID | Emergency fire-tug response and Port of Refuge dues for common safety. |
| `VCH-0702` | Master's Portage Bill | 28,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel at Colombo Port of Refuge. |
| `VCH-0703` | Salvage Dry-Pack Ltd | 1,150.75 | USD | FINAL_PAID | Special vacuum re-bagging of surviving `Lot-A` parcels (`Lot-A` Special Charge). |

### 7.4 Contemporaneous Telex & Email Correspondence
- **TELEX-07A (From: Joint Cargo Surveyor, To: Adjuster):** "Inspection of `Lot-A`'s `$160,000.00` loss in Hold #1 confirms that `$60,000.00` was extinguishing water damage to separate unburnt pallets, while `$100,000.00` was smoke and radiant heat damage from the electrical fire in the forward bulkhead."
- **TELEX-07B (From: Adjuster Reminder):** "Per Section 1.4 of the Adjusting Manual, report `Lot-A`'s gross assessment contribution (`GA_Lot_A + SpecialCharges_Lot_A`) prior to netting out any credit allowance."

---

## CASE `mgaf_08` — MV Aegean Glory (Voyage VOY-08)
- **Vessel:** MV Aegean Glory (`IMO-9410108`) | **Reflagged:** 2020
- **Bill of Lading Date:** `2025-05-01` | **Termination of Adventure Date:** `2025-06-10`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 8.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-08A | CHF | 500,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-08B | USD | 650,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-08C | USD | 350,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-08 | USD | 2,700,000.00 | Hull & Machinery | N/A |

### 8.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 CHF | SOUND | Arrived sound. |
| `Lot-B` | 130,000.00 USD | STORM_AND_JETTISON | `$50,000.00` crushed in Hold #2 during storm roll + `$80,000.00` under-deck cargo jettisoned to refloat. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 320,000.00 USD | RUDDER_AND_BEACHING | `$200,000.00` storm rudder loss + `$120,000.00` bottom plating damage from voluntary beaching. |

### 8.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-0801` | Piraeus Tugs & Port | 85,000.00 | USD | FINAL_PAID | Refloating tugs and Port of Refuge charges for common safety. |
| `VCH-0802` | Master's Portage Bill | 35,000.00 | USD | FINAL_PAID | Rule XI crew wages and fuel during Port of Refuge detention. |

### 8.4 Contemporaneous Telex & Email Correspondence
- **TELEX-08A (From: VDR & Hull Surveyor, To: Adjuster):** "Voyage Data Recorder confirms the `$200,000.00` rudder loss occurred accidentally in storm seas prior to the General Average act, after which the Master intentionally ran the vessel ashore on a soft sandspit for the common safety, causing `$120,000.00` bottom plating damage. Check `assets/fx_and_port_tariffs.csv` for the vessel's `keel_laid_year` (`2015`) and the governing `CHF` exchange rate."

---

## CASE `mgaf_09` — MV Tasman Spirit (Voyage VOY-09)
- **Vessel:** MV Tasman Spirit (`IMO-9410109`) | **Reflagged:** 2019
- **Bill of Lading Date:** `2025-05-05` | **Termination of Adventure Date:** `2025-06-15`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 9.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-09A | USD | 900,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-09B | USD | 700,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-09C | USD | 450,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-09 | USD | 3,000,000.00 | Hull & Machinery | N/A |

### 9.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 70,000.00 USD | DISCHARGE_HANDLING | Crane & sling damage sustained while discharging Hold #1 at Port of Refuge. |
| `Lot-C` | 50,000.00 USD | DISCHARGE_HANDLING | Forklift damage sustained while discharging and restowing Hold #3 at Port of Refuge. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$3,000,000.00` USD. |

### 9.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-0901` | Auckland Port & Tugs | 110,000.00 | USD | FINAL_PAID | Port of Refuge entry/exit, pilotage, and Rule XI detention wages/fuel. |
| `VCH-0902` | Stevedore Co (Hold #1) | 70,000.00 | USD | FINAL_PAID | Discharging, storing, and reloading `Lot-B` (Hold #1) required to access and weld submerged hull frame fracture necessary for safe prosecution of the voyage. |
| `VCH-0903` | Stevedore Co (Hold #3) | 40,000.00 | USD | FINAL_PAID | Discharging and restowing `Lot-C` (Hold #3) solely because `Lot-C` timber packs had shifted in heavy weather and required re-lashing for `Lot-C`'s own preservation. |
| `VCH-0904` | Assay & Seal Ltd | 2,310.40 | USD | FINAL_PAID | Special customs re-sealing and moisture certification on `Lot-A` containers (`Lot-A` Special Charge). |

### 9.4 Contemporaneous Telex & Email Correspondence
- **TELEX-09A (From: Port Surveyor Auckland, To: Adjuster):** "Hold #1 discharge (`VCH-0902`, `$70,000.00`) was strictly required to reach the submerged hull frame fracture for common safety repairs, and the `$70,000.00` sling damage to `Lot-B` occurred directly during that operation. By contrast, Hold #3 discharge (`VCH-0903`, `$40,000.00`) was not required for any ship repair or common safety peril, and the `$50,000.00` forklift damage to `Lot-C` occurred during that Hold #3 restowage. Apply Rule X and Rule XII."

---

## CASE `mgaf_10` — MV Nordic Fjord (Voyage VOY-10)
- **Vessel:** MV Nordic Fjord (`IMO-9410110`) | **Reflagged:** 2021
- **Bill of Lading Date:** `2025-05-12` | **Termination of Adventure Date:** `2025-06-22`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 10.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-10A | USD | 540,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-10B | USD | 600,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-10C | USD | 570,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-10 | USD | 1,500,000.00 | Hull & Machinery | N/A |

### 10.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound (see Pre-Sailing Clerical Erratum `TELEX-10A`). |
| `Lot-B` | 120,000.00 USD | STORM_HATCH_LEAK | Accidental sea-water ingress through storm-damaged hatch seal (see Lab Moisture Telex `TELEX-10B`). |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$1,500,000.00` USD. |

### 10.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1001` | Bergen Port & Tugs | 105,000.00 | USD | FINAL_PAID | Emergency tug assistance and Port of Refuge charges for common safety. |
| `VCH-1002` | Master's Portage Bill | 55,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel at Bergen Port of Refuge. |
| `VCH-1003` | Fjord Cargo Survey | 490.00 | USD | FINAL_PAID | Special sampling & seal fee exclusively for `Lot-A`. |

### 10.4 Contemporaneous Telex & Email Correspondence
- **TELEX-10A (From: Carrier Manifest Desk, To: Adjuster — Pre-Sailing Clerical Erratum):** "Prior to sailing on `2025-05-12`, shipper of `Lot-A` filed verified clerical correction `ERR-10A` proving that `BOL-10A` transposed digits `$540,000.00` instead of the true commercial CIF invoice value `$450,000.00` USD. Carrier accepted the correction prior to departure."
- **TELEX-10B (From: Lab Moisture Analyst, To: Adjuster):** "Although `Lot-B` bulk grain weighed 10% heavier on the destination weighbridge due to absorbed sea water from the accidental storm hatch leak, absorbed water has zero commercial value; actual commercial loss from the accidental wetting is `$120,000.00` USD."
"""


DOSSIERS_PART2_MD = """# Maritime General Average & Salvage Forensic Dossiers — Part 2 (`mgaf_11` to `mgaf_20`)

---

## CASE `mgaf_11` — MV Lusitania Star (Voyage VOY-11)
- **Vessel:** MV Lusitania Star (`IMO-9410111`) | **Reflagged:** 2020
- **Bill of Lading Date:** `2025-05-01` | **Termination of Adventure Date:** `2025-06-09`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 11.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-11A | EUR | 500,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-11B | GBP | 400,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-11C | USD | 400,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-11 | USD | 2,660,000.00 | Hull & Machinery | N/A |

### 11.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 40,000.00 USD | SMOKE_SCORCH | Smoke permeation into Hold #1 through ventilation trunk during Hold #2 fire (valued in USD at `$40,000.00`). |
| `Lot-B` | 80,000.00 GBP | EXTINGUISHING_WATER | Fire-hose water damage to unburnt `Lot-B` textiles in Hold #2 (`80,000.00 GBP`). |
| `Lot-C` | 110,000.00 USD | FIRE_AND_WATER | Combined fire-fighting loss in Hold #2 (`$60,000.00` active flame char + `$50,000.00` extinguishing water on unburnt drums). |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,660,000.00` USD. |

### 11.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1101` | Gibraltar Fire & Port | 92,000.00 | USD | FINAL_PAID | Fire-fighting tugs, CO2 system refill, and Port of Refuge dues for common safety. |
| `VCH-1102` | Master's Portage Bill | 38,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel during Port of Refuge stay. |
| `VCH-1103` | Lab Air-Test Gibraltar | 1,750.60 | USD | FINAL_PAID | Special particulate certification ordered solely for `Lot-A` cargo release (`Lot-A` Special Charge). |

### 11.4 Contemporaneous Telex & Email Correspondence
- **TELEX-11A (From: Forensic Fire Surveyor Gibraltar, To: Adjuster):** "Confirmed under Rule III:
  - `Lot-A`'s `$40,000.00` USD loss was caused strictly by smoke and soot without water or flame contact.
  - `Lot-B`'s `80,000.00 GBP` loss was caused strictly by extinguishing water poured onto separate packages that had not been touched by fire.
  - `Lot-C`'s `$110,000.00` USD loss comprises `$60,000.00` USD of drums already on fire when water was applied and `$50,000.00` USD of separate unburnt drums damaged solely by extinguishing water.
  Convert all `EUR` and `GBP` figures at the Termination Date (`2025-06-09`) rates in `assets/fx_and_port_tariffs.csv`."

---

## CASE `mgaf_12` — MV Timber King (Voyage VOY-12)
- **Vessel:** MV Timber King (`IMO-9410112`) | **Reflagged:** 2019
- **Bill of Lading Date:** `2025-05-18` | **Termination of Adventure Date:** `2025-06-25`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 12.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-12A | USD | 500,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-12B | USD | 720,000.00 | Weather Deck (`TIMBER_WELL_DECK`) | ON_DECK_AT_SHIPPER_RISK |
| `Lot-C` | BOL-12C | USD | 400,000.00 | Hatch #2 Cell Guides (`CELLULAR_CONTAINER_DECK`) | CUSTOMARY_CONTAINER_DECK |
| `Vessel` | HULL-12 | USD | 2,500,000.00 | Hull & Machinery | N/A |

### 12.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 120,000.00 USD | JETTISON_GA_CANDIDATE | `$120,000.00` of `Lot-B` breakbulk timber stowed on `TIMBER_WELL_DECK` jettisoned by Master to correct severe list in hurricane. |
| `Lot-C` | 80,000.00 USD | JETTISON_GA_CANDIDATE | `$80,000.00` of `Lot-C` containers stowed in `CELLULAR_CONTAINER_DECK` jettisoned by Master to correct severe list in hurricane. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,500,000.00` USD. |

### 12.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1201` | Halifax Port & Tugs | 115,000.00 | USD | FINAL_PAID | Emergency tug escort and Port of Refuge charges for common safety. |
| `VCH-1202` | Master's Portage Bill | 45,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel at Port of Refuge. |

### 12.4 Contemporaneous Telex & Email Correspondence
- **TELEX-12A (From: Cargo Stowage Surveyor, To: Adjuster):** "Although the preliminary boarding clerk tagged both jettisons as `JETTISON_GA_CANDIDATE`, Stowage Plan inspection proves that `Lot-B`'s jettisoned cargo was breakbulk lumber stowed on `TIMBER_WELL_DECK`, whereas `Lot-C`'s jettisoned containers were stowed in certified `CELLULAR_CONTAINER_DECK` cell guides. Apply Section 3.1 (Rule I — Jettison of Deck Cargo) of the Adjusting Manual."

---

## CASE `mgaf_13` — MV Iron Monarch (Voyage VOY-13)
- **Vessel:** MV Iron Monarch (`IMO-9410113`) | **Reflagged:** 2016 (Check `assets/fx_and_port_tariffs.csv` for official `keel_laid_year`!)
- **Bill of Lading Date:** `2025-05-20` | **Termination of Adventure Date:** `2025-06-28`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 13.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-13A | USD | 800,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-13B | USD | 600,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-13C | USD | 400,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-13 | USD | 3,270,000.00 | Hull & Machinery | N/A |

### 13.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 270,000.00 USD | SACRIFICIAL_GEAR_LOSS | Intentional common-safety sacrifice to refloat off rocky shoal: `$180,000.00` main propulsion machinery over-speed sacrifice + `$30,000.00` port bower anchor slipped + `$60,000.00` starboard chain cable cut. |

### 13.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1301` | Cape Town Refuge Port | 110,000.00 | USD | FINAL_PAID | Refloating tug assistance, pilotage, and Rule XI detention wages/fuel. |
| `VCH-1302` | Table Bay Temporary Weld | 40,000.00 | USD | FINAL_PAID | Temporary underwater hull patch at Port of Refuge required for common safety. |
| `VCH-1303` | Protea Cargo Survey | 920.50 | USD | FINAL_PAID | Special ultrasonic hatch-seal test requested solely for `Lot-A` (`Lot-A` Special Charge). |

### 13.4 Contemporaneous Telex & Email Correspondence
- **TELEX-13A (From: Classification Society Surveyor, To: Adjuster):** "Note that while MV Iron Monarch was reflagged in `2016`, her official `keel_laid_year` in `assets/fx_and_port_tariffs.csv` is `2006` (making her 19 years old in `2025`). Apply Rule XIII ('New for Old' deductions for vessels over 15 years old) separately to the `$180,000.00` machinery sacrifice, the `$30,000.00` anchor sacrifice, the `$60,000.00` chain cable sacrifice, and the `$40,000.00` temporary repair (`VCH-1302`) per Section 3.5 of the Adjusting Manual."

---

## CASE `mgaf_14` — MV Caledonia (Voyage VOY-14)
- **Vessel:** MV Caledonia (`IMO-9410114`) | **Reflagged:** 2018
- **Bill of Lading Date:** `2025-05-25` | **Termination of Adventure Date:** `2025-07-01`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 14.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-14A | USD | 600,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-14B | USD | 500,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-14C | USD | 400,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-14 | USD | 1,500,000.00 | Hull & Machinery | N/A |

### 14.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$1,500,000.00` USD. |

### 14.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1401` | Clyde Refuge Port & Tugs | 88,000.00 | USD | FINAL_PAID | Emergency tug assistance and Port of Refuge inward/outward dues. |
| `VCH-1402` | Clyde Marine Engineering | 30,000.00 | USD | FINAL_PAID | Temporary rudder stock repair required for common safety and voyage completion. |
| `VCH-1403` | Master's Portage Bill | 112,000.00 | USD | FINAL_PAID | Claimed 14 days of Port of Refuge detention wages, maintenance, and fuel at `$8,000.00/day` (see Port Agent Telex `TELEX-14A`). |

### 14.4 Contemporaneous Telex & Email Correspondence
- **TELEX-14A (From: Port Agent Greenock, To: Adjuster):** "Audit of `VCH-1403` (`14 days @ $8,000.00/day = $112,000.00`) shows that physical rudder repairs and seaworthiness certification were completed at the end of Day 9 (`9 days @ $8,000.00/day = $72,000.00`). The remaining 5 days of detention (`5 days @ $8,000.00/day = $40,000.00`) were caused solely by a customs phytosanitary hold placed on `Lot-B` after vessel repairs were already complete. Apply Section 4.1 (Rule XI) of the Adjusting Manual."

---

## CASE `mgaf_15` — MV Kowloon Express (Voyage VOY-15)
- **Vessel:** MV Kowloon Express (`IMO-9410115`) | **Reflagged:** 2019 | **Keel Laid:** 2013
- **Bill of Lading Date:** `2025-05-28` | **Termination of Adventure Date:** `2025-07-02`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 15.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-15A | USD | 700,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-15B | USD | 600,000.00 | Aft Weather Deck (`FLAT_RACK_WEATHER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-15C | USD | 400,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-15 | USD | 2,400,000.00 | Hull & Machinery | N/A |

### 15.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 100,000.00 USD | DECK_JETTISON | `$100,000.00` of `Lot-B` machinery stowed on `FLAT_RACK_WEATHER_DECK` jettisoned during typhoon (see `TELEX-15A`). |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 90,000.00 USD | SACRIFICIAL_WINCH | `$90,000.00` sacrificial destruction of aft mooring winch & gear cut away for common safety during typhoon refloating. |

### 15.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1501` | Kaohsiung Port & Tugs | 150,000.00 | USD | FINAL_PAID | Emergency tug assistance, Port of Refuge dues, and Rule XI detention wages/fuel. |
| `VCH-1502` | Taiwan Cargo Inspect | 1,330.20 | USD | FINAL_PAID | Special shock-logger calibration and inspection exclusively for `Lot-A` (`Lot-A` Special Charge). |

### 15.4 Contemporaneous Telex & Email Correspondence
- **TELEX-15A (From: Maritime Legal & Survey Team, To: Adjuster):** "Although `BOL-15B` was issued as `CONTRACTED_UNDER_DECK`, the terminal loaded `Lot-B`'s jettisoned flat-rack onto `FLAT_RACK_WEATHER_DECK` (not cellular container deck guides). Apply Section 3.1 (Rule I) of the Adjusting Manual to `Lot-B`'s `$100,000.00` jettison. Also check `assets/fx_and_port_tariffs.csv` for MV Kowloon Express's `keel_laid_year` (`2013`) when evaluating Rule XIII on the `$90,000.00` sacrificial winch loss."

---

## CASE `mgaf_16` — MV Cape Horn (Voyage VOY-16)
- **Vessel:** MV Cape Horn (`IMO-9410116`) | **Reflagged:** 2017 (Check `assets/fx_and_port_tariffs.csv` for `keel_laid_year`)
- **Bill of Lading Date:** `2025-06-01` | **Termination of Adventure Date:** `2025-07-03`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 16.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-16A | EUR | 800,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-16B | SGD | 800,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-16C | USD | 420,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-16 | USD | 2,230,000.00 | Hull & Machinery | N/A |

### 16.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 EUR | SOUND | Arrived sound. |
| `Lot-B` | 200,000.00 SGD | HOLD_FIRE_AND_WATER | Hold #2 fire: `120,000.00 SGD` extinguishing water on unburnt crates + `80,000.00 SGD` active fire charring. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 90,000.00 USD | BULKHEAD_SACRIFICE | `$90,000.00` USD gross cost of cutting access holes in Hold #2 bulkhead to flood burning hold for common safety. |

### 16.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1601` | Valparaiso Port & Fire Tugs | 130,000.00 | USD | FINAL_PAID | Emergency fire-tug response, Port of Refuge dues, and Rule XI detention wages/fuel. |
| `VCH-1602` | Andean Cargo Care | 2,120.00 | USD | FINAL_PAID | Special nitrogen-purge service performed exclusively on `Lot-A` containers (`Lot-A` Special Charge). |

### 16.4 Contemporaneous Telex & Email Correspondence
- **TELEX-16A (From: Senior Adjuster, To: Case File):** "Cross-reference `assets/fx_and_port_tariffs.csv` for `mgaf_16`:
  1. Convert `EUR` and `SGD` figures at the Termination Date (`2025-07-03`) rates (`EUR = $1.05`, `SGD = $0.75`).
  2. Apply Rule III to `Lot-B`'s `200,000.00 SGD` loss (`120,000.00 SGD` unburnt water sacrifice vs `80,000.00 SGD` active fire char).
  3. Check `keel_laid_year` (`2004`, age 21 years > 15 years) and apply the Rule XIII `1/3` 'New for Old' deduction to the `$90,000.00` USD sacrificial bulkhead renewal."

---

## CASE `mgaf_17` — MV Borealis (Voyage VOY-17)
- **Vessel:** MV Borealis (`IMO-9410117`) | **Reflagged:** 2020
- **Bill of Lading Date:** `2025-06-05` | **Termination of Adventure Date:** `2025-07-12`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 17.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-17A | USD | 450,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-17B | USD | 550,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-17C | USD | 500,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-17 | USD | 1,500,000.00 | Hull & Machinery | N/A |

### 17.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | `$1,500,000.00` USD is net arrived value after accidental storm shell cracking. |

### 17.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1701` | Reykjavik Port & Tugs | 115,000.00 | USD | FINAL_PAID | Port of Refuge inward/outward dues, tug escort, and Rule XI detention wages/fuel. |
| `VCH-1702` | SubSea Cofferdam Ltd | 95,000.00 | USD | FINAL_PAID | Temporary underwater cofferdam welding of **accidental** storm hull crack effected solely to complete the voyage without discharging cargo (see `TELEX-17A`). |
| `VCH-1703` | Arctic Survey Group | 640.50 | USD | FINAL_PAID | Special temperature-seal verification billed exclusively to `Lot-A` (`Lot-A` Special Charge). |

### 17.4 Contemporaneous Telex & Email Correspondence
- **TELEX-17A (From: Hull & GA Surveyor Reykjavik, To: Adjuster):** "The hull crack repaired under `VCH-1702` (`$95,000.00`) was caused by accidental heavy-weather ice impact (Particular Average), not a General Average sacrifice. Performing the temporary underwater weld avoided `$65,000.00` of allowable General Average cargo discharging, storage, and reloading costs at Reykjavik, plus `$20,000.00` of private shipowner charter off-hire penalties. Apply Section 4.2 (Rule XIV Cap on Temporary Repairs of Accidental Damage) of the Adjusting Manual."

---

## CASE `mgaf_18` — MV Emerald Isle (Voyage VOY-18)
- **Vessel:** MV Emerald Isle (`IMO-9410118`) | **Reflagged:** 2021
- **Bill of Lading Date:** `2025-06-10` | **Termination of Adventure Date:** `2025-07-18`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 18.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-18A | USD | 900,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-18B | USD | 700,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-18C | USD | 400,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-18 | USD | 2,000,000.00 | Hull & Machinery | N/A |

### 18.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,000,000.00` USD. |

### 18.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1801` | Cork Refuge Port & Tugs | 128,000.00 | USD | FINAL_PAID | Emergency towage into Cork, port dues, and actual Rule XI detention wages/fuel incurred during stay. |
| `VCH-1802` | HeavyLift Air Charter | 110,000.00 | USD | FINAL_PAID | Extra cost of air-freighting replacement governor assembly from Hamburg to Cork instead of waiting for sea freight (Substituted Expense under Rule F; see `TELEX-18A`). |

### 18.4 Contemporaneous Telex & Email Correspondence
- **TELEX-18A (From: Average Adjuster Technical Note, To: File):** "Air-freighting the replacement assembly (`VCH-1802`, `$110,000.00`) saved exactly `12 days` of additional Port of Refuge detention at `$6,000.00/day` (`$72,000.00` of allowable Rule XI GA crew wages, fuel, and port berthage) and saved the Shipowner `$25,000.00` in private demurrage penalties. Apply Section 4.3 (Rule F Cap on Substituted Expenses) of the Adjusting Manual."

---

## CASE `mgaf_19` — MV Levant Express (Voyage VOY-19)
- **Vessel:** MV Levant Express (`IMO-9410119`) | **Reflagged:** 2019
- **Bill of Lading Date:** `2025-06-15` | **Termination of Adventure Date:** `2025-07-24`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 19.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-19A | USD | 600,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-19B | USD | 200,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-19C | USD | 500,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-19 | USD | 2,100,000.00 | Hull & Machinery | N/A |

### 19.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 50,000.00 USD | JETTISON_UNDER_DECK | `$50,000.00` (at actual commercial value) of `Lot-B` jettisoned from Hold #2 for common safety (see Customs Audit Telex `TELEX-19A`!). |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,100,000.00` USD. |

### 19.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-1901` | Limassol Port & Tugs | 112,000.00 | USD | FINAL_PAID | Emergency refloating tugs and Port of Refuge charges for common safety. |
| `VCH-1902` | Master's Portage Bill | 48,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel at Limassol Port of Refuge. |
| `VCH-1903` | MedSurvey Cyprus | 1,180.00 | USD | FINAL_PAID | Special customs bond & inspection incurred solely for `Lot-A` (`Lot-A` Special Charge). |

### 19.4 Contemporaneous Telex & Email Correspondence
- **TELEX-19A (From: Customs & Post-Casualty Commercial Audit Unit, To: Average Adjuster):** "URGENT — RULE XIX VIOLATION ON `Lot-B` (`BOL-19B`): Customs seizure of the true commercial invoices proves the shipper of `Lot-B` willfully misdeclared precision avionics as 'industrial iron fittings' at `$200,000.00` USD to evade ad-valorem freight. The **actual sound commercial CIF value** of `Lot-B` at shipment and termination was **`$450,000.00` USD**, of which **`$50,000.00` USD** (at actual commercial value) was jettisoned during the casualty and **`$400,000.00` USD** arrived intact. Apply Section 3.6 (Rule XIX — Undeclared or Willfully Under-Declared Cargo: forfeiture of Made Good and `2x` double assessment on surviving commercial value) of the Adjusting Manual."

---

## CASE `mgaf_20` — MV Atlantic Carrier (Voyage VOY-20)
- **Vessel:** MV Atlantic Carrier (`IMO-9410120`) | **Reflagged:** 2018
- **Bill of Lading Date:** `2025-06-20` | **Termination of Adventure Date:** `2025-08-02`
- **Freight Terms:** `COLLECT_AT_DESTINATION` (Carrier's Risk — see `assets/fx_and_port_tariffs.csv` and Section 5.1 of the Manual!)
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 20.1 Cargo, Vessel & Collect Freight Manifest
| Interest | B/L or Ref | Currency | Declared Sound Value (Ex-Freight) | Shipped Metric Tons | Stowage Location |
|---|---|---|---:|---:|---|
| `Lot-A` | BOL-20A | USD | 800,000.00 | 1,000 | Hold #1 (`UNDER_DECK`) |
| `Lot-B` | BOL-20B | USD | 1,000,000.00 | 1,250 | Hold #2 (`UNDER_DECK`) |
| `Lot-C` | BOL-20C | USD | 560,000.00 | 750 | Hold #3 (`UNDER_DECK`) |
| `Vessel` | HULL-20 | USD | 2,400,000.00 | N/A | Hull & Machinery |
| `Freight` | FRT-20 | USD | See Tariff (`3,000 tons` total) | 3,000 | Collect Freight at Carrier's Risk |

### 20.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss | Initial Survey Tag | Description |
|---|---|---|
| `Lot-A` | 0.00 USD (0 tons lost) | SOUND | All `1,000 tons` arrived sound. |
| `Lot-B` | 200,000.00 USD (250 tons lost) | JETTISON_UNDER_DECK | `250 metric tons` (`$200,000.00` cargo value) of `Lot-B` jettisoned from Hold #2 (`UNDER_DECK`) for common safety; `1,000 tons` (`$800,000.00`) arrived sound. |
| `Lot-C` | 0.00 USD (0 tons lost) | SOUND | All `750 tons` arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,400,000.00` USD. |
| `Freight` | Collect Freight on `250 tons` jettisoned | FREIGHT_SACRIFICE | Gross collect freight `$100.00/ton` less contingent destination discharge cost `$20.00/ton` (see `TELEX-20A`). |

### 20.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-2001` | Azores Refuge Port & Tugs | 95,000.00 | USD | FINAL_PAID | Emergency tug assistance and Port of Refuge charges for common safety. |
| `VCH-2002` | Master's Portage Bill | 35,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel at Azores Port of Refuge. |
| `VCH-2003` | Atlantic Survey Services | 450.25 | USD | FINAL_PAID | Special moisture-barrier sealing billed exclusively to `Lot-A` (`Lot-A` Special Charge). |

### 20.4 Contemporaneous Telex & Email Correspondence
- **TELEX-20A (From: Carrier Freight Audit Desk, To: Average Adjuster):** "Per `assets/fx_and_port_tariffs.csv`, all `3,000 metric tons` of cargo on Voyage VOY-20 were carried on `COLLECT_AT_DESTINATION` terms at a Gross Collect Freight rate of `$100.00/ton`, with a Contingent Destination Discharge Cost of `$20.00/ton` payable by the Carrier only on tons actually discharged at destination (`NetFreightPerTon = $80.00/ton`). Of the `3,000 tons` shipped, `2,750 tons` arrived at destination and `250 tons` (`Lot-B`) were jettisoned in General Average. Apply Section 5.1 of the Adjusting Manual to compute `Freight Made Good` (entering the GA Pool) and `V_Freight` (entering the Contributory Value denominator alongside `Lot-A`, `Lot-B`, `Lot-C`, and `Vessel`)."
"""
