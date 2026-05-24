import json
import random
import os
import csv
import argparse

def generate_items(sample_count, seed, out_dir):
    random.seed(seed)

    solver_bundle_dir = os.path.join(out_dir, "solver_bundle")
    items_dir = os.path.join(solver_bundle_dir, "items")
    os.makedirs(items_dir, exist_ok=True)

    items_private_sample = []
    gold_private_sample = []

    tenant_names = ["Tenant A", "Tenant B", "Tenant C", "Tenant D", "Tenant E", "Tenant F", "Tenant G"]

    for i in range(sample_count):
        item_id = f"item_{str(i).zfill(3)}"
        item_path = os.path.join(items_dir, item_id)
        os.makedirs(item_path, exist_ok=True)

        total_sqft = random.choice([10000, 12000, 15000, 20000, 25000])
        num_suites = random.randint(4, 7)

        suite_sizes = []
        remaining = total_sqft
        for j in range(num_suites - 1):
            size = random.randint(1, max(1, remaining // 200)) * 100
            if size == 0: size = 500
            suite_sizes.append(size)
            remaining -= size
        suite_sizes.append(remaining)

        suites = {f"{101+j}": size for j, size in enumerate(suite_sizes)}

        num_tenants = random.randint(3, 5)
        active_tenants = random.sample(tenant_names, num_tenants)

        occupancy = []
        available_suites = list(suites.keys())
        random.shuffle(available_suites)

        rent_roll_csv = [["Tenant", "Suite", "Start_Day", "End_Day"]]

        for j, t in enumerate(active_tenants):
            if j < len(available_suites):
                s = available_suites[j]
                start = random.choice([1, 1, 1, random.randint(2, 100)])
                end = random.choice([365, 365, 365, random.randint(200, 364)])
                occupancy.append({"tenant": t, "suite": s, "start": start, "end": end})
                rent_roll_csv.append([t, s, start, end])

        emails = []
        direct_charges_gold = {t: 0 for t in active_tenants}
        caps = {}

        # Expansions
        if random.random() < 0.6:
            assigned_suites = [o["suite"] for o in occupancy]
            unassigned = [s for s in suites if s not in assigned_suites]
            if unassigned:
                t = random.choice(active_tenants)
                s = random.choice(unassigned)
                start = random.randint(50, 200)
                end = 365
                occupancy.append({"tenant": t, "suite": s, "start": start, "end": end})

                templates = [
                    f"{t} has expanded into Suite {s} starting on Day {start}. They will occupy this suite until the end of the year.",
                    f"Update the rent roll: {t} took over Suite {s} on Day {start}.",
                    f"Effective Day {start}, {t} added Suite {s} to their lease for the remainder of the year.",
                    f"Please note {t} is leasing Suite {s} as of Day {start}."
                ]
                msg = random.choice(templates)
                emails.append(f"From: Leasing\nTo: Accounting\nDate: Day {start-2}\nSubject: Expansion\n{msg}")

        # Caps
        if random.random() < 0.7:
            t = random.choice(active_tenants)
            cap = random.randint(400, 1500)
            caps[t] = cap

            templates = [
                f"Please note that {t} has a negotiated CAM Cap of {cap} cents per sq ft per year. Apply this to their final calculation.",
                f"{t} secured a cap on CAM at {cap} cents per sq ft per year.",
                f"For {t}, their base CAM is capped at {cap} cents per square foot annually.",
                f"Do not charge {t} more than their CAM cap of {cap} cents per sq ft per year."
            ]
            msg = random.choice(templates)
            emails.append(f"From: Property Manager\nTo: Accounting\nDate: Day 10\nSubject: CAM Cap\n{msg}")

        expense_types = [
            ("Routine landscaping", "OpEx", 50000, 150000),
            ("Monthly cleaning", "OpEx", 80000, 200000),
            ("Snow removal", "OpEx", 20000, 60000),
            ("Common area utilities", "OpEx", 150000, 300000),
            ("Minor plumbing repair", "OpEx", 30000, 90000),
            ("HVAC filter replacement", "OpEx", 40000, 80000),
            ("Security patrol", "OpEx", 100000, 250000),
            ("Roof replacement", "CapEx", 600000, 1500000),
            ("HVAC unit installation", "CapEx", 500000, 900000),
            ("Parking lot repaving", "CapEx", 700000, 1200000),
            ("Property tax late fee", "Excluded", 10000, 50000),
            ("Legal fee for eviction", "Excluded", 150000, 400000),
            ("Landlord penalty for code violation", "Excluded", 20000, 80000)
        ]

        num_expenses = random.randint(15, 25)
        expenses = []

        for _ in range(num_expenses):
            day = random.randint(1, 365)
            desc_base, etype, min_amt, max_amt = random.choice(expense_types)
            amount = random.randint(min_amt, max_amt)

            # Trap: exactly 500,000 cents
            if random.random() < 0.05 and etype == "OpEx":
                amount = 500000
                etype = "CapEx"

            expenses.append({"day": day, "amount": amount, "desc": f"{desc_base} {random.randint(100,999)}", "type": etype})

        expenses.sort(key=lambda x: x["day"])

        for exp in expenses:
            if exp["type"] == "OpEx" and random.random() < 0.15:
                t = random.choice(active_tenants)
                templates = [
                    f"The expense on Day {exp['day']} for '{exp['desc']}' ({exp['amount']} cents) was caused by {t}. Reclassify this as a Direct Charge to {t} instead of OpEx.",
                    f"Please bill the '{exp['desc']}' (Day {exp['day']}) directly to {t}. They are responsible for it. Do not put it in the main OpEx pool.",
                    f"Regarding the {exp['amount']} cents spent on '{exp['desc']}' on Day {exp['day']}: {t} is at fault. This is a direct charge to them.",
                    f"Accounting, ensure that {t} pays the full {exp['amount']} cents for the Day {exp['day']} '{exp['desc']}'. It's not a shared expense."
                ]
                msg = random.choice(templates)
                emails.append(f"From: Maintenance\nTo: Accounting\nDate: Day {exp['day'] + 2}\nSubject: Direct Charge\n{msg}")
                exp["type"] = "Direct"
                exp["direct_tenant"] = t

            elif exp["type"] == "OpEx" and random.random() < 0.1:
                templates = [
                    f"The expense on Day {exp['day']} for '{exp['desc']}' should be considered a capital improvement. Exclude it from the OpEx pool.",
                    f"Correction: '{exp['desc']}' on Day {exp['day']} is a CapEx. Remove from OpEx.",
                    f"We decided to capitalize the '{exp['desc']}' cost from Day {exp['day']}. It is excluded.",
                    f"The {exp['amount']} cents for '{exp['desc']}' (Day {exp['day']}) is actually a capital expense."
                ]
                msg = random.choice(templates)
                emails.append(f"From: Management\nTo: Accounting\nDate: Day {exp['day'] + 5}\nSubject: Reclassification\n{msg}")
                exp["type"] = "CapEx"

        random.shuffle(emails)

        # Calculate Gold
        base_pool = sum(e["amount"] for e in expenses if e["type"] == "OpEx")
        mgmt_fee = base_pool * 5 // 100
        total_pool = base_pool + mgmt_fee

        bldg_sqft_days = total_sqft * 365

        tenant_sqft_days = {t: 0 for t in active_tenants}
        for occ in occupancy:
            days = occ["end"] - occ["start"] + 1
            sqft = suites[occ["suite"]]
            tenant_sqft_days[occ["tenant"]] += sqft * days

        for e in expenses:
            if e["type"] == "Direct":
                direct_charges_gold[e["direct_tenant"]] += e["amount"]

        final_charges = {}
        for t in active_tenants:
            base_charge = (total_pool * tenant_sqft_days[t]) // bldg_sqft_days
            if t in caps:
                max_charge = (caps[t] * tenant_sqft_days[t]) // 365
                base_charge = min(base_charge, max_charge)

            final_charges[t] = base_charge + direct_charges_gold[t]

        # Write files
        with open(os.path.join(item_path, "property_data.json"), "w") as f:
            json.dump({"total_building_sqft": total_sqft, "suites": suites}, f, indent=2)

        with open(os.path.join(item_path, "rent_roll.csv"), "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rent_roll_csv)

        with open(os.path.join(item_path, "expenses_ledger.csv"), "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Day", "Amount_Cents", "Description"])
            for e in expenses:
                writer.writerow([e["day"], e["amount"], e["desc"]])

        with open(os.path.join(item_path, "communications.txt"), "w") as f:
            f.write("\n\n".join(emails) if emails else "No emails.")

        lease_manual = """# Commercial Lease CAM Reconciliation Manual

## 1. Operating Expenses (OpEx) Pool
The Annual OpEx Pool is the sum of all allowable operating expenses incurred during the year 2025 (Day 1 to Day 365).
Allowable expenses include:
- Routine maintenance, cleaning, landscaping, and security.
- Minor repairs (any repair costing strictly less than 500,000 cents).
- Utility bills for common areas.

Excluded expenses (DO NOT add to the OpEx Pool):
- Capital Expenses (CapEx), defined as any improvement, replacement, or repair costing 500,000 cents or more.
- Landlord's late fees, penalties, or legal fees.
- Direct Charges (expenses explicitly attributed to a specific tenant's negligence or direct request in the communications).

## 2. Property Management Fee
After summing the allowable expenses to find the Base OpEx Pool, a Property Management Fee is added.
The fee is exactly 5% (0.05) of the Base OpEx Pool.
USE INTEGER MATH ONLY. Do not use floats.
Property Management Fee = (Base OpEx Pool * 5) // 100
Total OpEx Pool = Base OpEx Pool + Property Management Fee

## 3. Tenant Pro-Rata Share
A tenant's share of the Total OpEx Pool is based on their "Occupancy Fraction".
Occupancy Fraction = (Tenant's Total Square-Foot-Days) / (Total Building SqFt * 365)

Total Building SqFt is defined in property_data.json.
A tenant's Total Square-Foot-Days is the sum of (SqFt occupied * number of days occupied at that SqFt).
Day counting is inclusive. Occupying a suite from Day 10 to Day 20 means 11 days of occupancy (20 - 10 + 1).
If a tenant expands into another suite, their Total Square-Foot-Days is the sum of the Square-Foot-Days for all their suites.
Building SqFt-Days = Total Building SqFt * 365.

Base CAM Charge = (Total OpEx Pool * Tenant's Total Square-Foot-Days) // Building SqFt-Days

## 4. Direct Charges
If a tenant has any Direct Charges identified in the communications, add the full amount of those Direct Charges to their Base CAM Charge.

## 5. CAM Caps
Some tenants may have a negotiated CAM Cap, expressed in cents per square foot per year.
The CAM Cap applies to the tenant's entire occupancy. Calculate the Max Base Charge as:
Max Base Charge = (Cap * Tenant's Total Square-Foot-Days) // 365
If the calculated Base CAM Charge exceeds the Max Base Charge, reduce the Base CAM Charge to the Max Base Charge.
Direct Charges are NOT subject to the CAM Cap and are added AFTER applying the cap.

Final CAM Charge = (Capped Base CAM Charge) + Direct Charges

**Final Output Instructions**: Return the exact integer amount in cents for each tenant listed in the initial rent roll.
"""
        with open(os.path.join(item_path, "lease_manual.md"), "w") as f:
            f.write(lease_manual)

        # Add to sample lists
        items_private_sample.append({
            "id": item_id,
            "folder": f"items/{item_id}",
            "question": f"Calculate the Final CAM Charge for all active tenants in {item_id}, in cents."
        })
        gold_private_sample.append({
            "id": item_id,
            "answer": final_charges
        })

    with open(os.path.join(solver_bundle_dir, "items_private_sample.jsonl"), "w") as f:
        for item in items_private_sample:
            f.write(json.dumps(item) + "\n")

    with open(os.path.join(out_dir, "gold_private_sample.jsonl"), "w") as f:
        for item in gold_private_sample:
            f.write(json.dumps(item) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260516)
    parser.add_argument("--out-dir", type=str, default=".")
    args = parser.parse_args()

    generate_items(args.sample_count, args.seed, args.out_dir)
