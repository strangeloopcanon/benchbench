# Maritime General Average & Salvage Forensic Dossiers — Part 1 (`mgaf_01` to `mgaf_10`)

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
