# Maritime General Average & Salvage Adjusting Manual (MGAF Consolidated Code)

**Version:** 2025.1 (York-Antwerp Charter Rules & Salvage Cascade Standard)  
**Applicability:** Governs all 30 adjustment dossiers (`mgaf_01` through `mgaf_30`).

---

## 1. Objective & Output Contract

For each case dossier (`mgaf_01` through `mgaf_30`), you act as the Senior Average Adjuster determining the **Final Total Assessment Payable by Cargo Interest `Lot-A`** at the termination of the maritime adventure, expressed as an **exact integer in USD cents** (`$1.00 = 100` cents).

$$\text{Answer (USD Cents)} = \text{Salvage}_{\text{Lot-A}} + \text{GA}_{\text{Lot-A}} + \text{SpecialCharges}_{\text{Lot-A}}$$

Where:
1. $\text{Salvage}_{\text{Lot-A}}$ is `Lot-A`'s Stage 1 Salvage Contribution (in USD cents; `0` if no independent Article 13 Salvage Award occurred).
2. $\text{GA}_{\text{Lot-A}}$ is `Lot-A`'s Stage 2 General Average Contribution (in USD cents, subject to any applicable Bigham Clause cap).
3. $\text{SpecialCharges}_{\text{Lot-A}}$ is the sum of any Particular / Special Charges incurred specifically for the preservation, reconditioning, or inspection of `Lot-A` alone (in USD cents).
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
  1. The **General Average Pool ($\text{GA}_{\text{pool}}$)** (numerator), AND
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
   $$\text{Vessel Age} = 2025 - \text{KEEL\_LAID\_YEAR}$$
   *(Always use `KEEL_LAID_YEAR` from `assets/fx_and_port_tariffs.csv`, never a later `REFLAGGED_YEAR` or `REBUILT_YEAR` mentioned in narrative headers.)*
2. If $\text{Vessel Age} \le 15$: **No deduction (`0`)** "New for Old"; full sacrificial renewal cost is allowed as `Vessel Made Good`.
3. If $\text{Vessel Age} > 15$:
   - **Machinery, Boilers, Winches, Hull Structure, Bulkheads, Rigging:** Deduct **one-third (`1/3`)** "New for Old" ($\text{Made Good} = \frac{2}{3} \times \text{Gross Sacrificial Renewal Cost}$).
   - **Chain Cables:** Deduct **one-sixth (`1/6`)** ($\text{Made Good} = \frac{5}{6} \times \text{Gross Cost}$).
   - **Anchors & Temporary Repairs:** **Exempt (`0` deduction)** ($\text{Made Good} = 100\%$ of sacrificial anchor loss; temporary repairs have `0` deduction).
   - **Contributory Value Impact:** The full physical sacrificial loss (`100%` of gross sacrificial damage) reduces the Vessel's physical arrived value, while only the post-deduction `Vessel Made Good` is added back to the Vessel's Contributory Value and the GA Pool.

### 3.6 Rule XIX — Undeclared or Willfully Under-Declared Cargo
If post-casualty customs inspection or commercial audit correspondence reveals that a cargo lot was shipped without notice or **willfully under-declared** on the Bill of Lading at a value lower than its actual commercial CIF value (`DECLARED_CIF < ACTUAL_COMMERCIAL_CIF`):
1. **Forfeiture of `Made Good`:** Any sacrifice or jettison of that misdeclared cargo lot is **DISALLOWED in General Average (`Made Good = 0`)**.
2. **Double Contributory Assessment (`2x` Penalty in Stage 2 GA):** In Stage 2 General Average, the misdeclared lot contributes on **DOUBLE (`2x`) its actual surviving net arrived commercial value**:
   $$V_{\text{misdeclared}} = 2 \times (\text{ActualCommercialSoundValue} - \text{TotalPhysicalLoss} - \text{SalvageContribution})$$
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
$$\text{Allowable Substituted Expense in GA} = \min(\text{Actual Substituted Expense}, \text{Avoided General Average Expense})$$
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
     $$\text{NetFreightPerTon} = \text{GrossCollectFreightPerTon} - \text{ContingentDestinationDischargeCostPerTon}$$
  2. **Net Arrived Freight:** Earned on all cargo tons delivered at destination (even if delivered in damaged condition):
     $$\text{NetArrivedFreight} = \text{ArrivedTons} \times \text{NetFreightPerTon}$$
  3. **Freight Made Good:** Allowed **only** on cargo tons totally lost via an **allowable General Average Sacrifice (jettison)**:
     $$\text{FreightMadeGood} = \text{AllowableGAJettisonTons} \times \text{NetFreightPerTon}$$
     *(Cargo tons lost via Particular Average storm flooding generate `0` Freight Made Good.)*
  4. **Freight Contributory Value:**
     $$V_{\text{Freight}} = \text{NetArrivedFreight} + \text{FreightMadeGood} - \text{Salvage}_{\text{Freight}}$$

### 5.2 Exempt vs. Non-Exempt Additional Manifest Items (Rule XVII)
- **Exempt from Contribution (`V = 0`):** Postal Mails (`MAIL_POUCHES`) and Crew/Passenger Personal Effects (`CREW_BAGGAGE`) are **exempt** from General Average contribution under Rule XVII.
- **Included in Contribution:** Time-Charterer's Bunkers (`TC_BUNKERS`) aboard at termination **must contribute** on their net arrived value.

---

## 6. Two-Stage Casualty Cascade (Salvage -> General Average) & Bigham Cap

### 6.1 Two-Stage Salvage + General Average Cascade
When independent salvors render services under Article 13 (`SALVAGE_AWARD > 0`):
1. **Stage 1 — Salvage Apportionment:**
   - Each interest's **Salved Value ($S_i$)** at the Salvage Termination Port is its actual sound commercial value (`1x`, even for Rule XIX cargo) minus all physical damage and jettison incurred prior to salvage termination:
     $$S_i = \text{SoundValue}_i - \text{TotalPhysicalLoss}_i$$
     *(Critically: Do **NOT** add back `Made Good` and do **NOT** apply Rule XIX `2x` doubling in Stage 1 Salvage!)*
   - Apportion the Salvage Award pro-rata over $S_{\text{total}} = \sum_j S_j$:
     $$\text{Salvage}_i = \text{round\_half\_up}\left(\text{SalvageAward} \times \frac{S_i}{S_{\text{total}}}\right)$$
2. **Stage 2 — General Average Apportionment:**
   - Deduct each interest's Stage 1 $\text{Salvage}_i$ lien from its arrived value before applying Rule XVII `Made Good` add-back (or Rule XIX `2x` doubling):
     - For normal interests:
       $$V_i = (\text{SoundValue}_i - \text{TotalPhysicalLoss}_i - \text{Salvage}_i) + \text{MadeGood}_i$$
     - For Rule XIX willfully misdeclared interests (`MadeGood = 0`):
       $$V_i = 2 \times (\text{ActualCommercialSoundValue}_i - \text{TotalPhysicalLoss}_i - \text{Salvage}_i)$$
   - The General Average Pool is:
     $$\text{GA}_{\text{pool}} = \sum_j \text{MadeGood}_j + \text{AllowableGAExpenses}$$
     *(The Stage 1 Salvage Award is **not** added into $\text{GA}_{\text{pool}}$ because it has already been separately apportioned in Stage 1 and deducted from $V_i$.)*
   - Uncapped GA Contribution for `Lot-A`:
     $$\text{GA}_{\text{Lot-A}}^{\text{uncapped}} = \text{round\_half\_up}\left(\text{GA}_{\text{pool}} \times \frac{V_{\text{Lot-A}}}{\sum_j V_j}\right)$$

### 6.2 Non-Separation Agreement & Bigham Clause Cap
If `Lot-A` is forwarded from the Port of Refuge under a Non-Separation Agreement containing a **Bigham Clause Cap ($\text{Cap}_{\text{Bigham}}$)**:
$$\text{GA}_{\text{Lot-A}} = \min\left(\text{GA}_{\text{Lot-A}}^{\text{uncapped}}, \text{Cap}_{\text{Bigham}}\right)$$
- The Bigham Cap applies **solely to $\text{GA}_{\text{Lot-A}}$** (Stage 2 General Average contribution). It never caps $\text{Salvage}_{\text{Lot-A}}$ (Stage 1 Salvage contribution) or $\text{SpecialCharges}_{\text{Lot-A}}$.
- If $\text{GA}_{\text{Lot-A}}^{\text{uncapped}} \le \text{Cap}_{\text{Bigham}}$, the cap does not bind and $\text{GA}_{\text{Lot-A}} = \text{GA}_{\text{Lot-A}}^{\text{uncapped}}$.
