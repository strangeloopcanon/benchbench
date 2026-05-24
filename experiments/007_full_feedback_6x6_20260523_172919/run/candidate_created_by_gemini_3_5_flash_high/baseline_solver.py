#!/usr/bin/env python3
import os
import json
import datetime
import re

def extract_number(text, pattern):
    match = re.search(pattern, text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return 0.0
    return 0.0

def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except Exception:
        return None

def main():
    items_path = "solver_bundle/items_private_sample.jsonl"
    out_path = "predictions_baseline.jsonl"

    if not os.path.exists(items_path):
        print(f"Error: {items_path} not found.")
        return 1

    predictions = []

    with open(items_path, "r") as f:
        for line in f:
            data = json.loads(line)
            item_id = data["id"]
            assets = data["assets"]

            # Naive parse of files
            # 1. Parse Bill of Lading
            with open(os.path.join("solver_bundle", assets["bill_of_lading"]), "r") as af:
                bol_text = af.read()
            container_count = extract_number(bol_text, r"Container Count\*\*:\s*(\d+)")
            container_type_match = re.search(r"Container Type\*\*:\s*(\w+)", bol_text)
            container_type = container_type_match.group(1) if container_type_match else "40ST"

            # 2. Parse Commercial Invoice
            with open(os.path.join("solver_bundle", assets["commercial_invoice"]), "r") as af:
                inv_text = af.read()
            invoice_value = extract_number(inv_text, r"Total Invoice Value\*\*:\s*([\d\.,]+)")
            currency_match = re.search(r"Total Invoice Value\*\*:\s*[\d\.,]+\s*(\w+)", inv_text)
            currency = currency_match.group(1) if currency_match else "USD"

            # 3. Parse Port Log
            with open(os.path.join("solver_bundle", assets["vessel_port_log"]), "r") as af:
                log_text = af.read()
            atc_match = re.search(r"Completion \(ATC\)\*\*:\s*([\d-]+)", log_text)
            gate_out_match = re.search(r"Gate-Out Date \(Pick-up\)\*\*:\s*([\d-]+)", log_text)
            gate_in_match = re.search(r"Gate-In Date \(Empty Return\)\*\*:\s*([\d-]+)", log_text)

            atc_date = parse_date(atc_match.group(1)) if atc_match else None
            gate_out_date = parse_date(gate_out_match.group(1)) if gate_out_match else None
            gate_in_date = parse_date(gate_in_match.group(1)) if gate_in_match else None

            # 4. Parse Exchange Rate list to get rate on gate_out_date
            rate = 1.0
            if currency != "USD" and gate_out_match:
                gate_out_str = gate_out_match.group(1).strip()
                with open(os.path.join("solver_bundle", assets["exchange_rates"]), "r") as af:
                    rates_text = af.read()
                # Find matching row
                rate_line = re.search(rf"\| {gate_out_str} \| ([\d\.]+) \| ([\d\.]+) \| ([\d\.]+) \| ([\d\.]+) \|", rates_text)
                if rate_line:
                    if currency == "EUR":
                        rate = float(rate_line.group(1))
                    elif currency == "GBP":
                        rate = float(rate_line.group(2))
                    elif currency == "JPY":
                        rate = float(rate_line.group(3))
                    elif currency == "CAD":
                        rate = float(rate_line.group(4))

            # Naive customs value (ignoring Incoterms adjustments!)
            cargo_value_usd = invoice_value * rate
            customs_value = cargo_value_usd

            # Naive duty rate (always assuming default laptops/phones 2.5% rate if not specified,
            # and ignoring reclassifications in email!)
            duty_rate = 0.03
            base_duty = customs_value * duty_rate
            hmf = customs_value * 0.00125
            mpf = customs_value * 0.003464
            # Naive MPF without caps!
            total_customs_duty = round(base_duty + hmf + mpf, 2)

            # Naive Carrier Charges (ignoring surcharges and weekend policies!)
            freight_rates = {"20ST": 1200.0, "40ST": 2000.0, "40HC": 2200.0}
            base_freight = freight_rates.get(container_type, 2000.0) * container_count
            lsf = 150.0 * container_count

            # Naive demurrage (simply calendar days past ATC + 5, ignoring weekend exclusion!)
            demurrage = 0.0
            if atc_date and gate_out_date:
                free_end = atc_date + datetime.timedelta(days=5)
                if gate_out_date > free_end:
                    days_over = (gate_out_date - free_end).days
                    # Assume flat $150/day standard charge (ignoring penal stage and waivers!)
                    demurrage = days_over * 150.0 * container_count

            # Naive detention (flat days over 7)
            detention = 0.0
            if gate_out_date and gate_in_date:
                free_end = gate_out_date + datetime.timedelta(days=7)
                if gate_in_date > free_end:
                    days_over = (gate_in_date - free_end).days
                    detention = days_over * 100.0 * container_count

            total_carrier_charges = round(base_freight + lsf + demurrage + detention, 2)

            predictions.append({
                "id": item_id,
                "answer": {
                    "customs_duty_usd": total_customs_duty,
                    "carrier_charges_usd": total_carrier_charges,
                    "reconciliation_flag": "NO_DISCREPANCY" # Naive baseline always predicts no discrepancy!
                }
            })

    with open(out_path, "w") as f:
        for row in predictions:
            f.write(json.dumps(row) + "\n")

    print("Baseline solver predictions generated successfully.")

if __name__ == "__main__":
    main()
