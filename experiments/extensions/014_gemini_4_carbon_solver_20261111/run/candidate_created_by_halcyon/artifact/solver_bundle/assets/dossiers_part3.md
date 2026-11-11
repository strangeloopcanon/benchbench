# Maritime General Average & Salvage Forensic Dossiers — Part 3 (`mgaf_21` to `mgaf_30`)

---

## CASE `mgaf_21` — MV Horn of Africa (Voyage VOY-21)
- **Vessel:** MV Horn of Africa (`IMO-9410121`) | **Reflagged:** 2018 (See `assets/fx_and_port_tariffs.csv` for official `keel_laid_year`!)
- **Bill of Lading Date:** `2025-06-25` | **Termination of Adventure Date:** `2025-08-08`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 21.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-21A | USD | 700,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-21B | USD | 1,200,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-21C | USD | 150,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-21 | USD | 2,550,000.00 | Hull & Machinery | N/A |

### 21.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound (see Customs Audit Telex `TELEX-21A` regarding willful under-declaration!). |
| `Vessel` | 150,000.00 USD | SACRIFICIAL_PROPULSION | `$150,000.00` gross renewal cost of main reduction gear intentionally sacrificed by running astern beyond rated load to refloat from coral reef. |

### 21.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-2101` | Djibouti Port & Tugs | 60,000.00 | USD | FINAL_PAID | Emergency refloating tug and Port of Refuge charges for common safety. |
| `VCH-2102` | OceanTow International | 140,000.00 | USD | FINAL_PAID | Ocean towage of vessel from Djibouti to destination (Substituted Expense under Rule F; see `TELEX-21B`). |
| `VCH-2103` | RedSea Cargo Inspect | 1,890.00 | USD | FINAL_PAID | Special customs seal and humidity inspection incurred solely for `Lot-A` (`Lot-A` Special Charge). |

### 21.4 Contemporaneous Telex & Email Correspondence
- **TELEX-21A (From: Customs & Post-Casualty Audit Unit, To: Adjuster):** "Post-casualty customs inspection at destination revealed that `Lot-C` (`BOL-21C`) was willfully under-declared on the Bill of Lading at `$150,000.00` USD to evade ad-valorem tariff rates. Commercial invoices seized from the consignee prove the **actual sound commercial CIF value** of `Lot-C` was **`$300,000.00` USD** (arrived undamaged)."
- **TELEX-21B (From: Hull & GA Surveyor, To: Adjuster):** "The `$150,000.00` main reduction gear damage was intentionally incurred by the Master running the engine astern beyond rated load to refloat from the coral reef for common safety (refer to `assets/fx_and_port_tariffs.csv` for the vessel's official `keel_laid_year`). Additionally, ocean towage (`VCH-2102`, `$140,000.00`) was performed as a Substituted Expense in lieu of Port of Refuge repairs, avoiding `$90,000.00` of allowable General Average cargo discharge, storage, and detention expenses and `$35,000.00` of private shipowner off-hire."

---

## CASE `mgaf_22` — MV Strait of Malacca (Voyage VOY-22)
- **Vessel:** MV Strait of Malacca (`IMO-9410122`) | **Reflagged:** 2020
- **Bill of Lading Date:** `2025-07-01` | **Termination of Adventure Date:** `2025-08-14`
- **Freight Terms:** `COLLECT_AT_DESTINATION` (Carrier's Risk — see `assets/fx_and_port_tariffs.csv`)
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 22.1 Cargo, Vessel & Collect Freight Manifest
| Interest | B/L or Ref | Currency | Declared Sound Value (Ex-Freight) | Shipped Metric Tons | Stowage Location |
|---|---|---|---:|---:|---|
| `Lot-A` | BOL-22A | EUR | 600,000.00 | 700 | Hold #1 (`UNDER_DECK`) |
| `Lot-B` | BOL-22B | GBP | 600,000.00 | 800 | Hold #2 (`UNDER_DECK`) |
| `Lot-C` | BOL-22C | USD | 390,000.00 | 500 | Hold #3 (`UNDER_DECK`) |
| `Vessel` | HULL-22 | USD | 2,200,000.00 | N/A | Hull & Machinery |
| `Freight` | FRT-22 | USD | See Tariff (`2,000 tons` total) | 2,000 | Collect Freight at Carrier's Risk |

### 22.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss | Initial Survey Tag | Description |
|---|---|---|
| `Lot-A` | 0.00 EUR (0 tons lost) | SOUND | All `700 tons` arrived sound. |
| `Lot-B` | 100,000.00 GBP (200 tons lost) | STORM_FLOODING_PA | `200 metric tons` (`100,000.00 GBP` cargo value) of `Lot-B` totally destroyed by accidental storm flooding prior to any GA act; `600 tons` (`500,000.00 GBP`) arrived sound. |
| `Lot-C` | 50,000.00 USD (100 tons lost) | JETTISON_UNDER_DECK | `100 metric tons` (`$50,000.00` USD cargo value) of `Lot-C` stowed in Hold #3 (`UNDER_DECK`) intentionally jettisoned for common safety; `400 tons` (`$340,000.00` USD) arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,200,000.00` USD. |
| `Freight` | Collect Freight on `300 tons` lost | MIXED_FREIGHT_LOSS | `200 tons` lost in accidental storm flooding + `100 tons` lost in under-deck jettison. |

### 22.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-2201` | Penang Refuge Port & Tugs | 102,000.00 | USD | FINAL_PAID | Emergency tug assistance and Port of Refuge charges for common safety. |
| `VCH-2202` | Master's Portage Bill | 38,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel at Penang Port of Refuge. |
| `VCH-2203` | Malacca Cargo Care | 725.50 | USD | FINAL_PAID | Special container dehumidification billed exclusively to `Lot-A`. |

### 22.4 Contemporaneous Telex & Email Correspondence
- **TELEX-22A (From: Carrier Freight & Currency Desk, To: Adjuster):** "All `2,000 metric tons` on Voyage VOY-22 were carried on `COLLECT_AT_DESTINATION` terms (see `assets/fx_and_port_tariffs.csv` for the gross collect freight rate per ton, contingent destination discharge cost per ton, and governing FX rates). At destination, `1,700 metric tons` were delivered and discharged (`700t` of `Lot-A`, `600t` of `Lot-B`, and `400t` of `Lot-C`). Of the `300 metric tons` lost during the voyage, `200 tons` (`Lot-B`) were lost in accidental heavy-weather bilge flooding prior to the casualty deviation, while `100 tons` (`Lot-C`) were intentionally jettisoned from Hold #3 for the common safety."

---

## CASE `mgaf_23` — MV Hansa Merchant (Voyage VOY-23)
- **Vessel:** MV Hansa Merchant (`IMO-9410123`) | **Reflagged:** 2021
- **Bill of Lading Date:** `2025-07-05` | **Termination of Adventure Date:** `2025-08-19`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 23.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-23A | USD | 500,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-23B | USD | 650,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-23C | USD | 100,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-23 | USD | 2,300,000.00 | Hull & Machinery | N/A |

### 23.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound (see `TELEX-23A`). |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound (see `TELEX-23B`). |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,300,000.00` USD. |

### 23.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-2301` | Bremerhaven Port & Tugs | 175,000.00 | USD | FINAL_PAID | Emergency tug assistance and Port of Refuge charges for common safety. |
| `VCH-2302` | Master's Portage Bill | 65,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel at Bremerhaven Port of Refuge. |

### 23.4 Contemporaneous Telex & Email Correspondence
- **TELEX-23A (From: Carrier Booking Desk, To: Adjuster):** "Prior to vessel departure on `2025-07-05`, shipper of `Lot-A` voluntarily submitted Booking Correction `BC-23A` amending `BOL-23A` from `$500,000.00` to its true commercial CIF value of `$550,000.00` USD, which Carrier accepted and endorsed prior to sailing."
- **TELEX-23B (From: Customs Enforcement Unit, To: Adjuster):** "Post-casualty customs X-ray inspection of `Lot-C` (`BOL-23C`) revealed undeclared semiconductor lithography modules willfully concealed inside crates declared as 'scrap metal' at `$100,000.00` USD. The **actual sound commercial CIF value** of `Lot-C` was **`$250,000.00` USD**."

---

## CASE `mgaf_24` — MV Orion (Voyage VOY-24)
- **Vessel:** MV Orion (`IMO-9410124`) | **Reflagged:** 2020
- **Bill of Lading Date:** `2025-07-10` | **Termination of Adventure Date:** `2025-08-25`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** **`$200,000.00` USD** (`SALV-2401`)

### 24.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-24A | USD | 800,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-24B | USD | 1,000,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-24C | USD | 400,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-24 | USD | 2,000,000.00 | Hull & Machinery | N/A |

### 24.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound at both Salvage Port and Final Destination. |
| `Lot-B` | 200,000.00 USD | PRE_SALVAGE_JETTISON | `$200,000.00` of `Lot-B` stowed in Hold #2 (`UNDER_DECK`) was intentionally jettisoned for common safety **prior** to the arrival of the LOF Salvors; the remaining `$800,000.00` was saved and delivered. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Salved and arrived value `$2,000,000.00` USD. |

### 24.3 Salvage Award & General Average Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Stage / Type | Description |
|---|---|---:|---|---|---|
| `SALV-2401` | Poseidon LOF Salvors | 200,000.00 | USD | STAGE_1_SALVAGE | Independent Article 13 Salvage Award for towing vessel off lee shore into port. |
| `VCH-2401` | Refuge Port & Adjuster | 100,000.00 | USD | STAGE_2_GA_EXPENSE | Port of Refuge dues, pilotage, and Rule XI detention wages/fuel incurred after salvage termination. |

### 24.4 Contemporaneous Telex & Email Correspondence
- **TELEX-24A (From: LOF Salvage Arbitrator, To: Average Adjuster):** "Confirm that `Lot-B`'s `$200,000.00` under-deck jettison occurred six hours before Poseidon Salvors connected their towline. Accordingly, `SALV-2401` (`$200,000.00` USD) was awarded strictly over the property physically saved at the termination of the salvage service, prior to the subsequent General Average adjustment."

---

## CASE `mgaf_25` — MV Bosphorus Queen (Voyage VOY-25)
- **Vessel:** MV Bosphorus Queen (`IMO-9410125`) | **Reflagged:** 2019
- **Bill of Lading Date:** `2025-07-15` | **Termination of Adventure Date:** `2025-08-30`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`
- **Non-Separation Agreement:** **Signed with Bigham Clause**

### 25.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-25A | USD | 1,000,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-25B | USD | 800,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-25C | USD | 700,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-25 | USD | 2,500,000.00 | Hull & Machinery | N/A |

### 25.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound; forwarded under Non-Separation Agreement with Bigham Clause. |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Net arrived value `$2,500,000.00` USD. |

### 25.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-2501` | Istanbul Refuge Port & Tugs | 210,000.00 | USD | FINAL_PAID | Emergency tug assistance, Port of Refuge dues, and cargo handling for common safety. |
| `VCH-2502` | Master's Portage Bill | 140,000.00 | USD | FINAL_PAID | Rule XI crew detention wages, maintenance, and fuel during prolonged refuge repair. |
| `VCH-2503` | Marmara Cargo Care | 1,320.00 | USD | FINAL_PAID | Special desiccant and customs inspection incurred solely for `Lot-A` prior to forwarding. |

### 25.4 Contemporaneous Telex & Email Correspondence
- **TELEX-25A (From: Average Adjuster Legal Desk, To: `Lot-A` Underwriters):** "`Lot-A` was forwarded from Istanbul to destination aboard a feeder vessel under a standard Non-Separation Agreement incorporating the **Bigham Clause**. Joint freight audit confirms that if `Lot-A` owners had taken delivery at Istanbul and forwarded `Lot-A` to destination at their own expense, their total independent forwarding cost would have been **`$54,500.00` USD**. Note that `VCH-2503` (`$1,320.00` USD) was a pre-forwarding Special Charge incurred specifically for `Lot-A`'s preservation."

---

## CASE `mgaf_26` — MV Southern Cross (Voyage VOY-26)
- **Vessel:** MV Southern Cross (`IMO-9410126`) | **Reflagged:** 2017 (See `assets/fx_and_port_tariffs.csv` for official `keel_laid_year`!)
- **Bill of Lading Date:** `2025-07-20` | **Termination of Adventure Date:** `2025-09-04`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** **`$200,000.00` USD** (`SALV-2601`)

### 26.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-26A | USD | 1,000,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-26B | USD | 800,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-26C | USD | 700,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-26 | USD | 2,800,000.00 | Hull & Machinery | N/A |

### 26.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 300,000.00 USD | PRE_SALVAGE_MACHINERY_SACRIFICE | `$300,000.00` gross renewal cost of auxiliary boilers & thrusters intentionally sacrificed for common safety **prior** to LOF salvage connection. |

### 26.3 Salvage Award & General Average Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Stage / Type | Description |
|---|---|---:|---|---|---|
| `SALV-2601` | Tasman Salvage Corp | 200,000.00 | USD | STAGE_1_SALVAGE | Independent Article 13 Salvage Award (`$200,000.00` USD). |
| `VCH-2601` | Sydney Refuge Port & Detention | 100,000.00 | USD | STAGE_2_GA_EXPENSE | Allowable Port of Refuge charges and Rule XI detention wages/fuel. |
| `VCH-2602` | Southern Reefer Check | 850.00 | USD | SPECIAL_LOT_A | Special probe calibration billed exclusively to `Lot-A`. |

### 26.4 Contemporaneous Telex & Email Correspondence
- **TELEX-26A (From: Classification & GA Surveyor, To: Adjuster):** "The `$300,000.00` sacrificial damage to the Vessel's auxiliary boilers and thrusters occurred before Tasman Salvage Corp connected towlines, reducing the Vessel's physical salved value at the salvage port accordingly. When computing the subsequent General Average adjustment, verify MV Southern Cross's `keel_laid_year` in `assets/fx_and_port_tariffs.csv` for applicable Rule XIII 'New for Old' deductions."

---

## CASE `mgaf_27` — MV Tyrrhenian Sea (Voyage VOY-27)
- **Vessel:** MV Tyrrhenian Sea (`IMO-9410127`) | **Reflagged:** 2020
- **Bill of Lading Date:** `2025-07-25` | **Termination of Adventure Date:** `2025-09-10`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** `None ($0.00)`

### 27.1 Cargo & Property Manifest (Including Non-Cargo Manifest Rows)
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Property Category | Stowage Location |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-27A | USD | 650,000.00 | Commercial Cargo | Hold #1 (`UNDER_DECK`) |
| `Lot-B` | BOL-27B | USD | 600,000.00 | Commercial Cargo | Hold #2 (`UNDER_DECK`) |
| `Lot-C` | BOL-27C | USD | 400,000.00 | Commercial Cargo | Hold #3 (`UNDER_DECK`) |
| `Vessel` | HULL-27 | USD | 2,200,000.00 | Ship Hull & Machinery | Hull & Machinery |
| `TC_BUNKERS` | BNK-27 | USD | 150,000.00 | Time-Charterer's Fuel Bunkers | Double-Bottom Tanks |
| `MAIL_POUCHES` | MAIL-27 | USD | 120,000.00 | International Postal Mails | Strongroom (`UNDER_DECK`) |
| `CREW_BAGGAGE` | BAG-27 | USD | 80,000.00 | Crew & Passenger Personal Effects | Accommodation Deck |

### 27.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| All Listed Items | 0.00 USD | SOUND | All property aboard arrived intact at destination after emergency refuge towage. |

### 27.3 Master & Adjuster Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Voucher Status | Description |
|---|---|---:|---|---|---|
| `VCH-2701` | Naples Refuge Port & Tugs | 165,000.00 | USD | FINAL_PAID | Emergency ocean tug into Naples and Port of Refuge dues for common safety. |
| `VCH-2702` | Master's Portage Bill | 75,000.00 | USD | FINAL_PAID | Rule XI crew detention wages and fuel during Port of Refuge stay. |
| `VCH-2703` | Tyrrhenian Cargo Seal | 420.75 | USD | FINAL_PAID | Special customs bonding and seal check exclusively for `Lot-A`. |

### 27.4 Contemporaneous Telex & Email Correspondence
- **TELEX-27A (From: Senior Adjuster, To: Manifest Clerk):** "Table 27.1 lists all property aboard at the termination of the adventure, including `TC_BUNKERS` (`$150,000.00` owned by the Time-Charterer), `MAIL_POUCHES` (`$120,000.00` postal mail bags), and `CREW_BAGGAGE` (`$80,000.00` personal effects). Filter contributory vs. statutorily exempt property in accordance with Rule XVII."

---

## CASE `mgaf_28` — MV Polar Endurance (Voyage VOY-28)
- **Vessel:** MV Polar Endurance (`IMO-9410128`) | **Reflagged:** 2021
- **Bill of Lading Date:** `2025-08-01` | **Termination of Adventure Date:** `2025-09-15`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** **`$500,000.00` USD** (`SALV-2801`)

### 28.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-28A | USD | 1,000,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-28B | USD | 950,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-28C | USD | 200,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-28 | USD | 2,600,000.00 | Hull & Machinery | N/A |

### 28.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound. |
| `Lot-B` | 50,000.00 USD | PRE_SALVAGE_JETTISON | `$50,000.00` of `Lot-B` stowed in Hold #2 (`UNDER_DECK`) jettisoned for common safety **prior** to arrival of salvors; `$900,000.00` saved and arrived at destination. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound (see Customs Audit Telex `TELEX-28A`!). |
| `Vessel` | 0.00 USD | NET_ARRIVED | Salved and arrived value `$2,600,000.00` USD. |

### 28.3 Salvage Award & General Average Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Stage / Type | Description |
|---|---|---:|---|---|---|
| `SALV-2801` | Icebreaker Salvage Ltd | 500,000.00 | USD | STAGE_1_SALVAGE | Independent Article 13 Salvage Award (`$500,000.00` USD) for freeing vessel from pack ice and towing to refuge. |
| `VCH-2801` | Tromso Refuge Port & Detention | 150,000.00 | USD | STAGE_2_GA_EXPENSE | Allowable Port of Refuge dues, pilotage, and Rule XI detention wages/fuel. |
| `VCH-2802` | Polar Thermal Audit | 1,540.00 | USD | SPECIAL_LOT_A | Special cold-chain certification billed exclusively to `Lot-A`. |

### 28.4 Contemporaneous Telex & Email Correspondence
- **TELEX-28A (From: Customs & Salvage Legal Counsel, To: Adjuster):** "Customs inspection at Tromso proved that `Lot-C` (`BOL-28C`, declared at `$200,000.00` USD) was willfully under-declared on the Bill of Lading; its **actual sound commercial CIF value** was **`$500,000.00` USD** (saved intact). Apply the Two-Stage Salvage -> General Average Cascade and Rule XIX per the Adjusting Manual."

---

## CASE `mgaf_29` — MV Magellan (Voyage VOY-29)
- **Vessel:** MV Magellan (`IMO-9410129`) | **Reflagged:** 2019
- **Bill of Lading Date:** `2025-08-05` | **Termination of Adventure Date:** `2025-09-20`
- **Freight Terms:** `PREPAID_ABSOLUTE`
- **Independent Salvage Award (Art. 13):** **`$150,000.00` USD** (`SALV-2901`)
- **Non-Separation Agreement:** **Signed with Bigham Clause**

### 29.1 Cargo & Property Manifest
| Interest | B/L or Ref | Currency | Declared Sound CIF / Value | Stowage Location | B/L Stowage Clause |
|---|---|---|---:|---|---|
| `Lot-A` | BOL-29A | USD | 600,000.00 | Hold #1 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-B` | BOL-29B | USD | 950,000.00 | Hold #2 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Lot-C` | BOL-29C | USD | 600,000.00 | Hold #3 (`UNDER_DECK`) | CONTRACTED_UNDER_DECK |
| `Vessel` | HULL-29 | USD | 2,000,000.00 | Hull & Machinery | N/A |

### 29.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss (Currency) | Initial Survey Tag | Description |
|---|---:|---|---|
| `Lot-A` | 0.00 USD | SOUND | Arrived sound; forwarded from Port of Refuge under Non-Separation Agreement with Bigham Clause. |
| `Lot-B` | 150,000.00 USD | PRE_SALVAGE_JETTISON | `$150,000.00` of `Lot-B` stowed in Hold #2 (`UNDER_DECK`) jettisoned for common safety **prior** to salvage; `$800,000.00` saved and arrived at destination. |
| `Lot-C` | 0.00 USD | SOUND | Arrived sound. |
| `Vessel` | 0.00 USD | NET_ARRIVED | Salved and arrived value `$2,000,000.00` USD. |

### 29.3 Salvage Award & General Average Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Stage / Type | Description |
|---|---|---:|---|---|---|
| `SALV-2901` | Atlantic Salvors Ltd | 150,000.00 | USD | STAGE_1_SALVAGE | Independent Article 13 Salvage Award (`$150,000.00` USD). |
| `VCH-2901` | Dakar Refuge Port & Detention | 250,000.00 | USD | STAGE_2_GA_EXPENSE | Allowable Port of Refuge charges, cargo handling, and Rule XI detention wages/fuel. |
| `VCH-2902` | WestAfrica Cargo Check | 910.25 | USD | SPECIAL_LOT_A | Special container inspection incurred exclusively for `Lot-A` prior to forwarding. |

### 29.4 Contemporaneous Telex & Email Correspondence
- **TELEX-29A (From: Average Adjuster Legal Desk, To: `Lot-A` Underwriters):** "Following termination of the Stage 1 salvage services at Dakar, `Lot-A` was forwarded to destination under a Non-Separation Agreement incorporating a verified **Bigham Clause forwarding cost cap of `$42,000.00` USD**."

---

## CASE `mgaf_30` — MV Sovereign of the Seas (Voyage VOY-30)
- **Vessel:** MV Sovereign of the Seas (`IMO-9410130`) | **Reflagged:** 2018 (See `assets/fx_and_port_tariffs.csv` for official `keel_laid_year`!)
- **Bill of Lading Date:** `2025-08-10` | **Termination of Adventure Date:** `2025-09-28`
- **Freight Terms:** `COLLECT_AT_DESTINATION` (Carrier's Risk — see `assets/fx_and_port_tariffs.csv`)
- **Independent Salvage Award (Art. 13):** **`$250,000.00` USD** (`SALV-3001`)
- **Non-Separation Agreement:** **Signed with Bigham Clause**

### 30.1 Cargo, Vessel & Collect Freight Manifest
| Interest | B/L or Ref | Currency | Declared Sound Value (Ex-Freight) | Shipped Metric Tons | Stowage Location |
|---|---|---|---:|---:|---|
| `Lot-A` | BOL-30A | GBP | 800,000.00 | 800 | Hold #1 (`UNDER_DECK`) |
| `Lot-B` | BOL-30B | USD | 1,050,000.00 | 1,000 | Hold #2 (`UNDER_DECK`) |
| `Lot-C` | BOL-30C | USD | 600,000.00 | 700 | Hold #3 (`UNDER_DECK`) |
| `Vessel` | HULL-30 | USD | 2,550,000.00 | N/A | Hull & Machinery |
| `Freight` | FRT-30 | USD | See Tariff (`2,500 tons` total) | 2,500 | Collect Freight at Carrier's Risk |

### 30.2 Port of Refuge Survey & Loss Log
| Interest | Reported Loss | Initial Survey Tag | Description |
|---|---|---|
| `Lot-A` | 0.00 GBP (0 tons lost) | SOUND | All `800 tons` arrived sound. |
| `Lot-B` | 250,000.00 USD (0 tons lost; delivered damaged) | PRE_SALVAGE_HOLD_FIRE | Hold #2 fire extinguished prior to salvage connection: `$100,000.00` active fire charring on burning crates + `$150,000.00` extinguishing water on separate unburnt crates. All `1,000 tons` were physically delivered at destination in damaged condition. |
| `Lot-C` | 0.00 USD (0 tons lost) | SOUND | All `700 tons` arrived sound. |
| `Vessel` | 150,000.00 USD | PRE_SALVAGE_BOILER_SACRIFICE | `$150,000.00` gross renewal cost of auxiliary boiler & pumps sacrificed during fire/refloating prior to salvage connection. |
| `Freight` | 0.00 USD (all `2,500 tons` delivered) | SOUND_FREIGHT_EARNED | All `2,500 metric tons` were physically delivered and discharged at destination. |

### 30.3 Salvage Award & General Average Disbursement Vouchers
| Voucher ID | Payee / Category | Amount | Currency | Stage / Type | Description |
|---|---|---:|---|---|---|
| `SALV-3001` | Sovereign Salvors Consortium | 250,000.00 | USD | STAGE_1_SALVAGE | Independent Article 13 Salvage Award (`$250,000.00` USD) apportioned over Stage 1 Salved Values (including Collect Freight at Risk). |
| `VCH-3001` | Malta Refuge Port & Detention | 150,000.00 | USD | STAGE_2_GA_EXPENSE | Allowable Port of Refuge charges and Rule XI detention wages/fuel. |
| `VCH-3002` | MedLab Cargo Inspect | 2,480.50 | USD | SPECIAL_LOT_A | Special customs and temperature certification incurred exclusively for `Lot-A`. |

### 30.4 Contemporaneous Telex & Email Correspondence
- **TELEX-30A (From: Senior Average Adjuster, To: Case File):** "All `2,500 metric tons` (including the damaged `Lot-B` crates) were physically discharged at destination, so the Carrier earned Collect Freight on all `2,500 tons` (see `assets/fx_and_port_tariffs.csv` for gross freight and contingent discharge tariff rates, `GBP` exchange rates, and the vessel's official `keel_laid_year`). In addition, `Lot-A` was covered by a Non-Separation Agreement at Malta with an independent **Bigham Clause forwarding cost cap of `$85,000.00` USD**."

