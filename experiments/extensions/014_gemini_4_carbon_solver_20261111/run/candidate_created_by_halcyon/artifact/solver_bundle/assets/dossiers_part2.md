# Maritime General Average & Salvage Forensic Dossiers — Part 2 (`mgaf_11` to `mgaf_20`)

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
