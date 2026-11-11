# Failure Modes & Diagnostic Taxonomy — Maritime General Average & Salvage Forensics (MGAF)

## Overview

`maritime_general_average_forensics` (MGAF) is designed so that **no single failure mode dominates all 30 items** and **naive single-formula scripts fail systematically** while still scoring non-zero (`4/30 = 13.33%`) on baseline cases. Because General Average apportionment couples numerator adjustments ($\text{GA}_{\text{pool}}$) with denominator adjustments ($\sum_j V_j$ via Rule XVII `Made Good` add-backs, Stage 1 Salvage deductions, and Rule XIX `2x` penalty assessments), any forensic misreading of a survey telex or tariff table propagates into `Lot-A`'s pro-rata share.

---

## 1. Six Primary Failure Modes

### FM-1: Endogenous `Made Good` Feedback Omission (Rule XVII)
- **Mechanism:** Under York-Antwerp Rule XVII, property sacrificed in General Average (`Made Good`) must be added back to the sacrificed interest's net arrived value when computing Stage 2 Contributory Values ($V_i = \text{NetArrived}_i + \text{MadeGood}_i$). Otherwise, the interest whose cargo was jettisoned for the common safety would escape contributing on the very value restored to it by the General Average pool.
- **Observed Error Pattern:** Solvers include `Made Good` in $\text{GA}_{\text{pool}}$ (numerator) but omit it from $V_i$ (denominator), inflating `Lot-A`'s share whenever another interest (`Lot-B`, `Lot-C`, `Vessel`, or `Freight`) suffers a General Average sacrifice, or deflating `Lot-A`'s share when `Lot-A` itself suffers a sacrifice (`mgaf_07`).
- **Affected Items:** `mgaf_05`, `mgaf_06`, `mgaf_07`, `mgaf_08`, `mgaf_09`, `mgaf_11`, `mgaf_12`, `mgaf_13`, `mgaf_15`, `mgaf_16`, `mgaf_20`, `mgaf_21`, `mgaf_22`, `mgaf_24`, `mgaf_26`, `mgaf_28`, `mgaf_29`, `mgaf_30`.

### FM-2: Causal Misclassification of Physical Losses (Rules I, III, V, XII)
- **Mechanism:** Survey logs report aggregate physical losses that must be decomposed using contemporaneous forensic telexes:
  - **Rule I (Deck Jettison):** Jettison from `CELLULAR_CONTAINER_DECK` (`mgaf_12` `Lot-C`) is allowable in GA, whereas jettison from `TIMBER_WELL_DECK` (`mgaf_12` `Lot-B`) or unauthorized `FLAT_RACK_WEATHER_DECK` (`mgaf_15` `Lot-B`, even under a `CONTRACTED_UNDER_DECK` B/L) is disallowed (`Made Good = 0`).
  - **Rule III (Shipboard Fire):** Extinguishing water damage to separate unburnt packages is allowable as GA Sacrifice, whereas damage to packages already actively burning or damage from smoke/soot/heat (`mgaf_06`, `mgaf_07`, `mgaf_11`, `mgaf_16`, `mgaf_30`) is Particular Average (`Made Good = 0`).
  - **Rule V & Rule XII:** Accidental storm rudder loss prior to voluntary beaching (`mgaf_08`) and forklift damage during non-GA single-interest restowage (`mgaf_09` `Lot-C`) are Particular Average.

### FM-3: Vessel Age & Rule XIII "New for Old" Deduction Traps
- **Mechanism:** Under Rule XIII, vessels with $\text{Age} = 2025 - \text{KEEL\_LAID\_YEAR} > 15$ incur a `1/3` "New for Old" deduction on sacrificial hull/machinery/boiler/bulkhead renewals and `1/6` on chain cables, while anchors and temporary repairs are exempt (`0` deduction). Critically, `100%` of the gross sacrificial damage reduces the Vessel's physical arrived value, while only the post-deduction `Made Good` is added back to $V_{\text{Vessel}}$ and $\text{GA}_{\text{pool}}$.
- **Observed Error Pattern:** Solvers read `Reflagged: 2016/2017/2018` from the dossier header (computing age $\le 15$) instead of cross-referencing `keel_laid_year` (`2004`–`2007`, age $18$–$21 > 15$) in `assets/fx_and_port_tariffs.csv`.
- **Affected Items:** `mgaf_13`, `mgaf_15` (control: keel laid 2013, age $12 \le 15$), `mgaf_16`, `mgaf_21`, `mgaf_26`, `mgaf_30`.

### FM-4: Valuation-Date FX & Disbursement Voucher Reconciliation (Rules G, X, XI, XIV, F)
- **Mechanism:**
  - **Rule G / XVII FX Rate:** Foreign-currency sound values, losses, and GA vouchers (`EUR`, `GBP`, `SGD`, `JPY`, `CHF`) must be converted at `termination_fx_usd_per_unit` (`TERMINATION_DATE`), never `bol_fx_usd_per_unit` (`BOL_DATE`).
  - **Voucher Audits:** Solvers must exclude `SUPERSEDED_DRAFT` estimates (`mgaf_03`), deduct yard credit notes (`mgaf_04`), exclude post-repair detention caused by a single cargo lot's customs hold (`mgaf_14`), cap temporary repairs of accidental damage at avoided GA expenses (Rule XIV, `mgaf_17`), and cap substituted air-freight/towage expenses at avoided GA expenses excluding private shipowner off-hire savings (Rule F, `mgaf_18`, `mgaf_21`).

### FM-5: Rule XIX Willful Misdeclaration vs. Pre-Sailing Clerical Amendments
- **Mechanism:** Under Rule XIX, cargo willfully under-declared on the Bill of Lading (`DECLARED_CIF < ACTUAL_COMMERCIAL_CIF`) forfeits any `Made Good` (`0` in GA Pool) and is assessed on **double (`2x`) its actual surviving net arrived commercial value** in Stage 2 GA (`mgaf_19`, `mgaf_21`, `mgaf_23` `Lot-C`, `mgaf_28` `Lot-C`). By contrast, honest pre-sailing clerical amendments accepted by the Carrier prior to departure (`mgaf_10` `Lot-A`, `mgaf_23` `Lot-A`) are valued at `1x` their amended commercial value.

### FM-6: Collect Freight at Risk & Two-Stage Salvage -> GA Cascade Ordering
- **Mechanism:**
  - **Collect Freight (`COLLECT_AT_DESTINATION`):** Carrier's Net Freight at Risk ($\text{GrossFreightPerTon} - \text{DestDischargeCostPerTon}$) on delivered tons plus `Freight Made Good` on GA-jettisoned tons (excluding PA storm-lost tons) forms a 5th contributory interest (`mgaf_20`, `mgaf_22`, `mgaf_30`).
  - **Two-Stage Salvage Cascade:** Stage 1 Salvage (`SALVAGE_AWARD`) is apportioned over actual physical Salved Values ($S_i = \text{Sound}_i - \text{PhysicalLoss}_i$, at `1x` without `Made Good` add-back or Rule XIX doubling). Each interest's Stage 1 $\text{Salvage}_i$ lien is then deducted from its arrived value before computing Stage 2 $V_i$ (`mgaf_24`, `mgaf_26`, `mgaf_28`, `mgaf_29`, `mgaf_30`).
  - **Bigham Clause Cap:** Applies strictly to $\text{GA}_{\text{Lot-A}}$ (`mgaf_25`, `mgaf_29`, `mgaf_30`), never capping $\text{Salvage}_{\text{Lot-A}}$ or $\text{SpecialCharges}_{\text{Lot-A}}$.

---

## 2. Item-Level Failure Mode Matrix (`mgaf_01` – `mgaf_30`)

| Item ID | Tier | Primary Failure Modes Tested | Gold Answer (USD Cents) | Naive Unadjusted Baseline (USD Cents) | Naive Error (USD Cents) |
|---|---:|---|---:|---:|---:|
| `mgaf_01` | 1 | Baseline PA hull repair filter + Special Charge (`VCH-0104`) | `1324550` | `1324550` | `0` (Exact Match) |
| `mgaf_02` | 1 | Post-refuge transit wage exclusion + PA shaft repair filter | `3084025` | `3084025` | `0` (Exact Match) |
| `mgaf_03` | 1 | FM-4: `BOL_DATE` vs `TERMINATION_DATE` FX + `SUPERSEDED_DRAFT` voucher | `2100000` | `2890128` | `+790128` |
| `mgaf_04` | 1 | FM-4: Multi-currency (`SGD`/`JPY`) FX + Yard Credit Note `CN-0403` | `2961080` | `3836115` | `+875035` |
| `mgaf_05` | 1 | FM-1: Under-deck jettison `Made Good` numerator + denominator feedback | `3500000` | `1562500` | `-1937500` |
| `mgaf_06` | 2 | FM-1, FM-2: Rule III fire water (`$90k` GA) vs active char (`$100k`) & smoke (`$60k`) | `3062500` | `1775813` | `-1286687` |
| `mgaf_07` | 2 | FM-1, FM-2: `Lot-A` own sacrifice (`$60k` water GA vs `$100k` smoke PA) gross rule | `3115075` | `2049540` | `-1065535` |
| `mgaf_08` | 2 | FM-1, FM-2, FM-4: `CHF` FX + accidental rudder (`$200k` PA) vs beaching (`$120k` GA) | `4400000` | `1804029` | `-2595971` |
| `mgaf_09` | 2 | FM-1, FM-2: Rule X/XII GA discharge damage (`Lot-B`) vs non-GA restowage (`Lot-C`) | `4731040` | `4231929` | `-499111` |
| `mgaf_10` | 2 | FM-4, FM-5: Pre-sailing clerical invoice transposition (`$540k` -> `$450k`) + moisture | `2449000` | `2815711` | `+366711` |
| `mgaf_11` | 2 | FM-1, FM-2, FM-4: Multi-currency (`EUR`/`GBP`) Rule III 3-lot fire/smoke/water split | `3675060` | `1978436` | `-1696624` |
| `mgaf_12` | 3 | FM-1, FM-2: Rule I `TIMBER_WELL_DECK` (PA) vs `CELLULAR_CONTAINER_DECK` (GA) | `3000000` | `2040816` | `-959184` |
| `mgaf_13` | 3 | FM-1, FM-3: Rule XIII `keel_laid_year=2006` (`1/3` machinery, `0` anchor, `1/6` chain) | `5692050` | `2509250` | `-3182800` |
| `mgaf_14` | 3 | FM-4: Rule XI detention split (`9 days` repair GA vs `5 days` `Lot-B` customs hold PA) | `3800000` | `3800000` | `0` (Exact Match)* |
| `mgaf_15` | 3 | FM-1, FM-2, FM-3: Unauthorized `FLAT_RACK_WEATHER_DECK` jettison + age $12 \le 15$ winch | `4333020` | `2809822` | `-1523198` |
| `mgaf_16` | 3 | FM-1, FM-2, FM-3, FM-4: `EUR`/`SGD` FX + Rule III fire + Rule XIII `2004` bulkhead (`1/3`) | `6092000` | `2788524` | `-3303476` |
| `mgaf_17` | 3 | FM-4: Rule XIV temporary accidental repair cap (`$95k` capped at `$65k` avoided GA) | `2764050` | `2764050` | `0` (Exact Match)* |
| `mgaf_18` | 3 | FM-4: Rule F substituted air-freight cap (`$110k` capped at `$72k` avoided GA) | `4500000` | `5355000` | `+855000` |
| `mgaf_19` | 4 | FM-5: Rule XIX willful misdeclaration on `Lot-B` (forfeit `$50k` MG + `2x` on `$400k`) | `2518000` | `2941529` | `+423529` |
| `mgaf_20` | 4 | FM-1, FM-6: `COLLECT_AT_DESTINATION` Net Freight at Risk (`$80/t`) + Freight Made Good | `5645025` | `2325727` | `-3319298` |
| `mgaf_21` | 4 | FM-3, FM-4, FM-5: Rule XIII (`2007` `1/3` ded) + Rule F towage cap (`$90k`) + Rule XIX `2x` | `3689000` | `3371609` | `-317391` |
| `mgaf_22` | 4 | FM-1, FM-4, FM-6: `EUR`/`GBP` FX + Collect Freight PA flood (`200t`) vs GA jettison (`100t`) | `3222550` | `2446822` | `-775728` |
| `mgaf_23` | 4 | FM-5: Pre-sailing booking amendment (`Lot-A` `1x`) vs post-casualty Rule XIX (`Lot-C` `2x`) | `3300000` | `3380282` | `+80282` |
| `mgaf_24` | 5 | FM-1, FM-6: Two-Stage Salvage (`$200k`) -> GA Cascade with pre-salvage jettison | `9700000` | `2000000` | `-7700000` |
| `mgaf_25` | 5 | FM-6: Non-Separation Agreement Bigham Clause Cap (`$54,500` binds vs `$70,000` uncapped) | `5582000` | `7132000` | `+1550000` |
| `mgaf_26` | 5 | FM-1, FM-3, FM-6: Two-Stage Salvage + pre-salvage boiler sacrifice + Rule XIII (`2005` `1/3`) | `9845000` | `2085000` | `-7760000` |
| `mgaf_27` | 5 | FM-6: Rule XVII `TC_BUNKERS` (contributory) vs `MAIL_POUCHES` & `CREW_BAGGAGE` (exempt) | `3942075` | `3756361` | `-185714` |
| `mgaf_28` | 5 | FM-1, FM-5, FM-6: Two-Stage Salvage (`$500k`) + Rule XIX (`1x` in Salvage, `2x` in GA) | `13754000` | `3345489` | `-10408511` |
| `mgaf_29` | 5 | FM-1, FM-6: Two-Stage Salvage + Bigham Cap (`$42,000` caps Stage 2 GA only, not Salvage) | `6541025` | `3841025` | `-2700000` |
| `mgaf_30` | 5 | FM-1..FM-6: Full synthesis (`GBP` FX + Collect Freight + Rule III + Rule XIII + Salvage + non-binding Bigham Cap) | `12848050` | `4078050` | `-8770000` |

*(Note: In `mgaf_01`, `mgaf_02`, `mgaf_14`, and `mgaf_17`, a baseline script that filters basic voucher tags scores `4/30 = 13.33%`, confirming the task is well-calibrated without being trivially solvable.)*
