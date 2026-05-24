#!/usr/bin/env python3
import os
import json
import random
import argparse
from datetime import datetime, date, timedelta

# HS Code Tariff Schedule from policy
HS_TARIFFS = {
    "8471.30": {"desc": "Laptops & Tablets", "rate": 0.000, "ad_rate": 0.0},
    "8517.13": {"desc": "Smartphones", "rate": 0.025, "ad_rate": 0.0},
    "8517.18": {"desc": "Routers & Modems", "rate": 0.030, "ad_rate": 0.0},
    "9403.20": {"desc": "Metal Office Furniture", "rate": 0.050, "ad_rate": 0.15},
    "9403.60": {"desc": "Wooden Office Furniture", "rate": 0.045, "ad_rate": 0.0},
    "7412.20": {"desc": "Copper Tube Fittings", "rate": 0.030, "ad_rate": 0.0},
    "7415.33": {"desc": "Copper Screws, Bolts", "rate": 0.040, "ad_rate": 0.12}
}

CURRENCIES = ["EUR", "GBP", "JPY", "CAD", "USD"]

# Exchange rates generator (base rates with small deterministic daily fluctuations)
def get_exchange_rate(curr, d, seed=20260516):
    if curr == "USD":
        return 1.0

    import hashlib
    # Deterministic daily drift based on seed and date hash
    date_str = d.strftime("%Y-%m-%d")
    h_str = f"{seed}_{curr}_{date_str}"
    h = int(hashlib.sha256(h_str.encode('utf-8')).hexdigest(), 16) % 1000
    drift = (h - 500) / 100000.0  # tiny fluctuation

    bases = {
        "EUR": 1.085,
        "GBP": 1.255,
        "JPY": 0.00645,
        "CAD": 0.732
    }

    return round(bases[curr] + drift, 5)

def calculate_demurrage_free_time_end(atc_date):
    # 5 calendar days starting the day after ATC.
    # Saturdays and Sundays are excluded.
    free_days_counted = 0
    current_date = atc_date
    while free_days_counted < 5:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # Monday to Friday
            free_days_counted += 1
    return current_date

def calculate_demurrage_charges(atc_date, gate_out_date, container_count, waiver_dates):
    free_end = calculate_demurrage_free_time_end(atc_date)
    if gate_out_date <= free_end:
        return 0.0

    # Charge days begin the calendar day after free time ends up to gate_out_date
    charge_dates = []
    curr = free_end + timedelta(days=1)
    while curr <= gate_out_date:
        if curr not in waiver_dates:
            charge_dates.append(curr)
        curr += timedelta(days=1)

    if not charge_dates:
        return 0.0

    # Count weekdays and weekends in the charge period
    weekdays_count = 0
    for d in charge_dates:
        if d.weekday() < 5:
            weekdays_count += 1

    if weekdays_count <= 3:
        # Standard stage: Saturdays and Sundays are excluded
        chargeable_days = weekdays_count
        charges = chargeable_days * 150.0 * container_count
    else:
        # Penal stage: all calendar days in charge period (after waivers) are chargeable.
        # Standard: 3 days @ 150, penal: remaining @ 300
        total_calendar_days = len(charge_dates)
        charges = (3 * 150.0 + (total_calendar_days - 3) * 300.0) * container_count

    return charges

def calculate_detention_charges(gate_out_date, gate_in_date, container_count, waiver_dates):
    # Free time: 7 calendar days starting on Gate-Out.
    # Detention charges start on Gate-Out + 7 days
    detention_start = gate_out_date + timedelta(days=7)
    if gate_in_date < detention_start:
        return 0.0

    charge_dates = []
    curr = detention_start
    while curr <= gate_in_date:
        if curr not in waiver_dates:
            charge_dates.append(curr)
        curr += timedelta(days=1)

    charges = len(charge_dates) * 100.0 * container_count
    return charges

def format_date(d):
    return d.strftime("%Y-%m-%d")

def generate_scenario(item_id, discrepancy_type, r, seed):
    # Generate dates around Oct/Nov 2026
    lading_offset = r.randint(1, 15)
    lading_date = date(2026, 10, lading_offset)

    transit_days = r.randint(10, 15)
    vessel_arrival = lading_date + timedelta(days=transit_days)

    berthing_delay = r.randint(0, 2)
    berthing_date = vessel_arrival + timedelta(days=berthing_delay)

    discharge_delay = r.randint(1, 2)
    atc_date = berthing_date + timedelta(days=discharge_delay)

    # Gate out (pick up) offset: 2 to 14 days after ATC
    gate_out_offset = r.randint(2, 14)
    gate_out_date = atc_date + timedelta(days=gate_out_offset)

    # Gate in (empty return) offset: 3 to 18 days after gate-out
    gate_in_offset = r.randint(3, 18)
    gate_in_date = gate_out_date + timedelta(days=gate_in_offset)

    container_types = ["20ST", "40ST", "40HC"]
    container_type = r.choice(container_types)
    container_count = r.randint(1, 4)

    currency = r.choice(CURRENCIES[:-1])  # Exclude USD for commercial invoices to force conversion
    if discrepancy_type == "NO_DISCREPANCY":
        # Can be any currency including USD
        currency = r.choice(CURRENCIES)

    # Choose primary HS code
    hs_choices = list(HS_TARIFFS.keys())
    primary_hs = r.choice(hs_choices)

    # Set up specific overrides and text details
    waiver_dates_demurrage = set()
    waiver_dates_detention = set()

    email_notes = []
    exchange_rate_override = None
    incoterm_override = None
    hs_override = None
    commercial_invoice_term = r.choice(["FOB", "CIF", "EXW", "CFR"])

    # Base amounts
    qty = r.randint(100, 800)
    unit_price = round(r.uniform(10.0, 150.0), 2)
    if currency == "JPY":
        unit_price = r.randint(1500, 20000)
    cargo_value = round(qty * unit_price, 2)

    freight_itemized = round(r.uniform(800, 2000), 2)
    insurance_itemized = round(r.uniform(50, 200), 2)

    # Generate exchange rates table context
    min_date = lading_date - timedelta(days=5)
    max_date = gate_in_date + timedelta(days=5)
    rates_table = []
    curr_date = min_date
    while curr_date <= max_date:
        rates_table.append({
            "date": curr_date,
            "EUR": get_exchange_rate("EUR", curr_date, seed),
            "GBP": get_exchange_rate("GBP", curr_date, seed),
            "JPY": get_exchange_rate("JPY", curr_date, seed),
            "CAD": get_exchange_rate("CAD", curr_date, seed)
        })
        curr_date += timedelta(days=1)

    # Apply discrepancy specific modifications
    if discrepancy_type == "HS_RECLASSIFICATION":
        # Reclassify from a higher duty / AD rate HS to a lower or vice versa
        if primary_hs == "9403.20":
            hs_override = "9403.60"
            email_notes.append("Broker: Customs inspected the office desks and flagged the wooden decorative panels. They reclassified the item from Metal Office Furniture (HS 9403.20) to Wooden Office Furniture (HS 9403.60) because the wood content is more than 50% of the surface area. Wooden furniture does not have the 15% anti-dumping rate.")
            email_notes.append("Shipper: That makes sense. Let's update our filing to HS 9403.60. The 4.5% rate applies, and we save on the anti-dumping duty.")
        elif primary_hs == "7412.20":
            hs_override = "7415.33"
            email_notes.append("Broker: Customs noted that these copper connectors are threaded and function as screws. We must reclassify from Copper Tube Fittings (HS 7412.20) to Copper Screws/Bolts (HS 7415.33). Please note this adds a 12% anti-dumping duty on top of the 4% base rate.")
            email_notes.append("Shipper: Understood, please apply HS 7415.33 for the final duty payment.")
        else:
            # Laptop to smartphone/router
            hs_override = "8517.18"
            email_notes.append("Broker: We determined that the imported equipment contains internal modems and should be classified under Router/Modem HS 8517.18 (3.0% rate) instead of Laptop HS 8471.30 (0% rate).")
            email_notes.append("Shipper: Confirmed. Reclassify as HS 8517.18.")

    elif discrepancy_type == "INCOTERM_MISMATCH":
        if commercial_invoice_term in ["FOB", "EXW"]:
            incoterm_override = "CIF"
            email_notes.append(f"Broker: The invoice states terms are {commercial_invoice_term}, but the carrier billing files confirm that the seller prepaid all insurance and ocean freight. Under our trade compliance rules, the correct Incoterm for valuation is CIF. Ocean freight was itemized on bills as USD {freight_itemized} and insurance as USD {insurance_itemized}. Please calculate duties based on CIF value.")
            email_notes.append("Shipper: Agree, the broker should file as CIF.")
        else:
            incoterm_override = "FOB"
            email_notes.append(f"Broker: The invoice was issued as {commercial_invoice_term}, but the shipment was sold on Free on Board terms, and we paid the carrier separately. The final customs entry must be filed under FOB terms, meaning we do not add freight or insurance to the transaction value.")
            email_notes.append("Shipper: That is correct. Please declare it as FOB.")

    elif discrepancy_type == "DEMURRAGE_OVERCHARGE":
        # Demurrage waiver for port strike
        strike_start = atc_date + timedelta(days=r.randint(1, 3))
        strike_days = [strike_start, strike_start + timedelta(days=1)]
        for sd in strike_days:
            waiver_dates_demurrage.add(sd)
        strike_days_str = ", ".join([format_date(sd) for sd in strike_days])
        email_notes.append(f"Shipper: We had a port crane outage and strike on {strike_days_str} which prevented us from picking up the container. Did the carrier agree to waive demurrage for those days?")
        email_notes.append(f"Broker: Yes, the carrier issued a formal waiver for demurrage charges on {strike_days_str}. However, their initial invoice still shows charges for those days. We must recalculate the correct carrier demurrage charges excluding those dates.")

    elif discrepancy_type == "CURRENCY_VALUATION_ERROR":
        # Broker used invoice date exchange rate instead of gate-out date exchange rate
        wrong_rate = get_exchange_rate(currency, lading_date, seed)
        correct_rate = get_exchange_rate(currency, gate_out_date, seed)
        exchange_rate_override = correct_rate
        email_notes.append(f"Broker: We noticed the entry was filed using the exchange rate on the lading date ({format_date(lading_date)}) of {wrong_rate} {currency}/USD. However, our trade policy dictates that the exchange rate of the Gate-Out Date ({format_date(gate_out_date)}) must be used.")
        email_notes.append(f"Shipper: Please correct this and recalculate the customs duty using the Gate-Out Date exchange rate of {correct_rate} {currency}/USD.")

    elif discrepancy_type == "NO_DISCREPANCY":
        email_notes.append("Broker: All documents (B/L, Commercial Invoice, Vessel Log) look clean and aligned. The Incoterm and exchange rates are checked and correct.")
        email_notes.append("Shipper: Excellent, let's file as is with no adjustments.")

    # Programmatic Golden Math Engine (The Oracle)
    # 1. Exchange Rate lookup
    active_rate_date = gate_out_date
    rate = get_exchange_rate(currency, active_rate_date, seed)

    # Convert cargo value to USD
    cargo_value_usd = round(cargo_value * rate, 2)

    # Calculate Customs Value
    term = incoterm_override if incoterm_override else commercial_invoice_term

    if term == "CIF":
        # CIF = Cargo + Insurance + Freight
        # If not itemized on invoice, standard defaults apply
        # We'll assume the invoice contains them if they were declared or if CFR/CIF defaults apply
        if discrepancy_type == "INCOTERM_MISMATCH" and incoterm_override == "CIF":
            # Itemized in email
            freight_usd = freight_itemized
            insurance_usd = insurance_itemized
        else:
            # Let's say they are not itemized unless it's a specific test case,
            # so apply default policy addition of 10% and 1.5% respectively
            freight_usd = round(cargo_value_usd * 0.10, 2)
            insurance_usd = round(cargo_value_usd * 0.015, 2)
        customs_value = cargo_value_usd + insurance_usd + freight_usd
    elif term == "FOB":
        customs_value = cargo_value_usd
    elif term == "EXW":
        customs_value = cargo_value_usd + (350.0 * container_count) + 150.0
    elif term == "CFR":
        insurance_usd = round(cargo_value_usd * 0.015, 2)
        customs_value = cargo_value_usd + insurance_usd
    else:
        customs_value = cargo_value_usd

    customs_value = round(customs_value, 2)

    # Calculate Customs Duties
    hs_code = hs_override if hs_override else primary_hs
    hs_info = HS_TARIFFS[hs_code]

    base_duty = round(customs_value * hs_info["rate"], 2)
    ad_duty = round(customs_value * hs_info["ad_rate"], 2)

    hmf = round(customs_value * 0.00125, 2)
    mpf = round(customs_value * 0.003464, 2)
    mpf = max(30.00, min(600.00, mpf))
    mpf = round(mpf, 2)

    total_customs_duty = round(base_duty + ad_duty + hmf + mpf, 2)

    # 2. Carrier Charges
    # Base Ocean Freight
    freight_rates = {"20ST": 1200.0, "40ST": 2000.0, "40HC": 2200.0}
    base_freight = freight_rates[container_type] * container_count

    # Surcharges
    lsf = 150.0 * container_count
    pss = 0.0
    # Peak season is August 1st to October 31st
    if date(2026, 8, 1) <= gate_out_date <= date(2026, 10, 31):
        pss = 250.0 * container_count

    # Demurrage
    demurrage = calculate_demurrage_charges(atc_date, gate_out_date, container_count, waiver_dates_demurrage)

    # Detention
    detention = calculate_detention_charges(gate_out_date, gate_in_date, container_count, waiver_dates_detention)

    total_carrier_charges = round(base_freight + lsf + pss + demurrage + detention, 2)

    # Generate Markdown Assets
    bol_content = f"""# BILL OF LADING
**B/L Number**: BL-{''.join(r.choices("0123456789", k=8))}
**Shipper**: TradeCorp Global Inc.
**Consignee**: Allied Imports LLC (Tax ID: 98-7654321)
**Port of Loading**: Port of Rotterdam, Netherlands
**Port of Discharge**: Port of Newark, NJ, USA
**Vessel Name**: Ocean Ranger V-102
**Lading Date**: {format_date(lading_date)}

## Cargo Description
- **Container Type**: {container_type}
- **Container Count**: {container_count}
- **Gross Weight**: {qty * 12} kg
- **Declared Volume**: {container_count * 30} CBM
- **Description**: {qty} units of {hs_info["desc"]} (HS Code declared: {primary_hs})
"""

    comm_inv_content = f"""# COMMERCIAL INVOICE
**Invoice Number**: INV-{''.join(r.choices("0123456789", k=6))}
**Invoice Date**: {format_date(lading_date - timedelta(days=2))}
**Seller**: Global Manufacture AG, Switzerland
**Buyer**: Allied Imports LLC, USA
**Incoterm**: {commercial_invoice_term}

## Itemized Transactions
| Qty | HS Code | Description | Unit Price ({currency}) | Total Price ({currency}) |
| :--- | :--- | :--- | :---: | :---: |
| {qty} | {primary_hs} | {hs_info["desc"]} | {unit_price} | {cargo_value} |

**Total Invoice Value**: {cargo_value} {currency}
**Terms of Payment**: Net 30 days
"""

    port_log_content = f"""# VESSEL & PORT OPERATION LOG
**Vessel**: Ocean Ranger V-102
**Voyage**: 102E
**Cargo ID**: C-{item_id.upper()}

## Chronology of Operations
- **Actual Time of Anchorage (ATA)**: {format_date(vessel_arrival)} 04:12 EST
- **Actual Time of Berthing (ATB)**: {format_date(berthing_date)} 10:45 EST
- **Discharge Start**: {format_date(berthing_date)} 14:00 EST
- **Actual Time of Completion (ATC)**: {format_date(atc_date)} 16:30 EST
- **Container Gate-Out Date (Pick-up)**: {format_date(gate_out_date)} 09:15 EST
- **Container Gate-In Date (Empty Return)**: {format_date(gate_in_date)} 14:00 EST
"""

    exchange_rates_content = f"""# EXCHANGE RATES LIST
This table lists the daily exchange rates relative to the US Dollar (USD) for the timeframe of the transaction.
To convert foreign currency to USD: $Amount_{{USD}} = Amount_{{FC}} \\times Rate$.

| Date | EUR/USD | GBP/USD | JPY/USD | CAD/USD |
| :--- | :---: | :---: | :---: | :---: |
"""
    for entry in rates_table:
        exchange_rates_content += f"| {format_date(entry['date'])} | {entry['EUR']:.5f} | {entry['GBP']:.5f} | {entry['JPY']:.5f} | {entry['CAD']:.5f} |\n"

    email_content = f"""# EMAIL CORRESPONDENCE - AUDIT LOG
**Subject**: Operations & Custom Clearance Coordination - Item {item_id.upper()}

---
**From**: John Davis (Allied Imports LLC)
**To**: Sarah Jenkins (Trade Brokerage Services)
**Date**: {format_date(lading_date + timedelta(days=2))}

Sarah, we have shipped the cargo under B/L {item_id}. Let's make sure the entry documentation is prepped.

---
**From**: Sarah Jenkins (Trade Brokerage Services)
**To**: John Davis (Allied Imports LLC)
**Date**: {format_date(vessel_arrival + timedelta(days=2))}

John, the vessel has arrived. We are verifying the invoice details.
{email_notes[0] if len(email_notes) > 0 else ""}

---
**From**: John Davis (Allied Imports LLC)
**To**: Sarah Jenkins (Trade Brokerage Services)
**Date**: {format_date(gate_out_date + timedelta(days=1))}

{email_notes[1] if len(email_notes) > 1 else "Thanks for the update. Keep us posted on carrier Gate-Out and return filings."}

---
**From**: Sarah Jenkins (Trade Brokerage Services)
**To**: John Davis (Allied Imports LLC)
**Date**: {format_date(gate_in_date + timedelta(days=1))}

All activities are completed. The container was gated back to the depot. Please find the finalized logs attached for audit purposes.
"""

    gold_answer = {
        "customs_duty_usd": total_customs_duty,
        "carrier_charges_usd": total_carrier_charges,
        "reconciliation_flag": discrepancy_type
    }

    assets = {
        "bill_of_lading.md": bol_content,
        "commercial_invoice.md": comm_inv_content,
        "vessel_port_log.md": port_log_content,
        "exchange_rates.md": exchange_rates_content,
        "email_correspondence.md": email_content
    }

    return gold_answer, assets

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260516)
    parser.add_argument("--out-dir", type=str, default=".")
    args = parser.parse_args()

    r = random.Random(args.seed)

    # Distribute the discrepancy types evenly
    types = [
        "HS_RECLASSIFICATION",
        "INCOTERM_MISMATCH",
        "DEMURRAGE_OVERCHARGE",
        "CURRENCY_VALUATION_ERROR",
        "NO_DISCREPANCY"
    ]

    # 30 items: 6 of each type
    discrepancies = []
    for t in types:
        discrepancies.extend([t] * (args.sample_count // len(types)))
    # Shuffle using the deterministic generator
    r.shuffle(discrepancies)

    gold_rows = []
    items_private_rows = []

    # Create asset subfolders
    solver_bundle_dir = os.path.join(args.out_dir, "solver_bundle")
    assets_dir = os.path.join(solver_bundle_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    for idx in range(args.sample_count):
        item_num = idx + 1
        item_id = f"item_{item_num:03d}"
        discrepancy_type = discrepancies[idx]

        gold_ans, assets = generate_scenario(item_id, discrepancy_type, r, args.seed)

        # Write asset files
        item_assets_dir = os.path.join(assets_dir, item_id)
        os.makedirs(item_assets_dir, exist_ok=True)

        asset_references = {}
        for filename, content in assets.items():
            filepath = os.path.join(item_assets_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)
            asset_references[filename.split(".")[0]] = f"assets/{item_id}/{filename}"

        gold_rows.append({
            "id": item_id,
            "answer": gold_ans
        })

        items_private_rows.append({
            "id": item_id,
            "assets": asset_references,
            "instruction": "Perform full audit and output actual customs_duty_usd, carrier_charges_usd, and reconciliation_flag."
        })

    # Write gold_private_sample.jsonl
    gold_path = os.path.join(args.out_dir, "gold_private_sample.jsonl")
    with open(gold_path, "w") as f:
        for row in gold_rows:
            f.write(json.dumps(row) + "\n")

    # Write solver_bundle/items_private_sample.jsonl
    items_path = os.path.join(solver_bundle_dir, "items_private_sample.jsonl")
    with open(items_path, "w") as f:
        for row in items_private_rows:
            f.write(json.dumps(row) + "\n")

    # Write solver_bundle/SOLVER_MANIFEST.json
    manifest = {
        "benchmark_name": "Maritime Freight & Customs Audit (MFCA)",
        "sample_count": args.sample_count,
        "files": [
            "README.md",
            "trade_policy.md",
            "items_private_sample.jsonl"
        ]
    }
    for row in items_private_rows:
        for filename, rel_path in row["assets"].items():
            manifest["files"].append(rel_path)

    manifest_path = os.path.join(solver_bundle_dir, "SOLVER_MANIFEST.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Successfully generated {args.sample_count} items in {args.out_dir}.")

if __name__ == "__main__":
    main()
