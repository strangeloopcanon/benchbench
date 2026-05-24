#!/usr/bin/env python3
"""
Generator for the Construction Progress Payment Certification (CPPC) benchmark.

Each item is a monthly payment application for a construction subcontract.
The solver must determine the correct certified payment amount by applying
the general conditions to item-specific data.

Uses the standard cumulative (AIA G702-style) computation method:
Total Earned to Date → Less Retention → Less Deductions → Plus Tax → Less Previous Payments = Amount Due

CLI: python generator.py --sample-count 30 --seed 20260516 --out-dir .
"""

import argparse
import json
import os
import random
from copy import deepcopy


# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

TRADE_NAMES = [
    "Structural Steel Erection", "Concrete Foundations", "Mechanical HVAC",
    "Electrical Rough-In", "Plumbing & Fire Protection", "Exterior Cladding",
    "Interior Framing & Drywall", "Roofing & Waterproofing", "Site Grading",
    "Elevator Installation", "Glass & Glazing", "Painting & Finishes",
    "Landscaping & Hardscape", "Fire Alarm & Detection", "IT/Low Voltage",
    "Demolition & Abatement", "Masonry", "Flooring & Tile",
    "Millwork & Casework", "Specialties & Accessories",
]

LINE_ITEM_DESCRIPTIONS = [
    "Mobilization & General Conditions",
    "Labor - Journeyman",
    "Labor - Apprentice",
    "Materials - Primary",
    "Materials - Secondary/Fasteners",
    "Equipment Rental",
    "Subcontracted Work",
    "Permits & Fees",
    "Shop Drawings & Submittals",
    "Temporary Protection",
    "Testing & Inspection",
    "Cleanup & Waste Removal",
    "Safety Equipment & Training",
    "Bonds & Insurance Allocation",
    "Overhead & Profit",
]

BACKCHARGE_REASONS = [
    "Failure to protect adjacent work during operations",
    "Cleanup of debris left in common areas",
    "Damage to installed elevator cab finish",
    "Unauthorized use of tower crane after scheduled hours",
    "Repair of punctured waterproofing membrane",
    "Replacement of contaminated ductwork insulation",
    "Emergency repair of damaged fire sprinkler head",
    "Remediation of concrete overpour into adjacent zone",
]

DEFICIENCY_TYPES = [
    "Improper fastener spacing per spec section",
    "Paint color does not match approved sample",
    "Ductwork leakage exceeds SMACNA allowable rate",
    "Concrete slump test failure - batch rejected",
    "Welding inspection failed - incomplete fusion",
    "Pipe slope insufficient per code requirement",
    "Insulation R-value below specification",
    "Grout coverage below 80% mortar bed requirement",
]


# ---------------------------------------------------------------------------
# Calculation engine (mirrors general_conditions rules exactly)
# ---------------------------------------------------------------------------

def round_cents(amount: float) -> int:
    """Round to nearest cent using banker's rounding (round half to even)."""
    return int(round(amount))


def compute_retention_rate(cumulative_percent_complete: float) -> float:
    """
    General Conditions §7.2:
    - Retention is 10% until the Work is 50% complete
    - Retention reduces to 5% after 50% completion
    """
    if cumulative_percent_complete >= 50.0:
        return 0.05
    return 0.10


def compute_change_order_earned(
    co_amount_cents: int,
    co_status: str,
    co_percent_complete: float,
) -> int:
    """
    General Conditions §8.3:
    - Approved COs: bill at actual percent complete × CO amount
    - Pending COs: bill at 50% of (percent complete × CO amount)
    - Disputed COs: bill at 25% of (percent complete × CO amount)
    - Rejected COs: $0
    """
    base = round_cents(co_amount_cents * (co_percent_complete / 100.0))
    if co_status == "approved":
        return base
    elif co_status == "pending":
        return round_cents(base * 0.50)
    elif co_status == "disputed":
        return round_cents(base * 0.25)
    else:  # rejected
        return 0


def compute_stored_materials_credit(materials: list[dict]) -> int:
    """
    General Conditions §7.4:
    ALL THREE conditions must be met for each material entry:
    1. has_documentation = true
    2. is_protected = true
    3. has_insurance = true
    If any fails, that entry gets $0 credit.
    """
    total = 0
    for mat in materials:
        if (mat.get("has_documentation", False) and
            mat.get("is_protected", False) and
            mat.get("has_insurance", False)):
            total += mat["value_cents"]
    return total


def compute_liquidated_damages(
    days_behind: int,
    daily_rate_cents: int,
    cap_cents: int,
    is_excusable: bool,
) -> int:
    """
    General Conditions §9.1:
    LDs = days_behind × daily_rate, capped at cap_cents.
    If delay is excusable, LDs = $0 regardless.
    """
    if is_excusable:
        return 0
    ld_amount = days_behind * daily_rate_cents
    return min(ld_amount, cap_cents)


def compute_insurance_deduction(
    lapse_start_day: int,
    lapse_end_day: int,
    period_start_day: int,
    period_end_day: int,
    work_earned_this_period_cents: int,
) -> int:
    """
    General Conditions §10.2:
    Deduction = work_earned_this_period × (lapse_days_in_period / total_days_in_period)
    Applies only to work earned, NOT stored materials.
    """
    overlap_start = max(lapse_start_day, period_start_day)
    overlap_end = min(lapse_end_day, period_end_day)
    lapse_days = max(0, overlap_end - overlap_start + 1)
    total_days = period_end_day - period_start_day + 1
    if total_days <= 0 or lapse_days <= 0:
        return 0
    deduction = work_earned_this_period_cents * (lapse_days / total_days)
    return round_cents(deduction)


def compute_tax(
    materials_earned_this_period_cents: int,
    tax_rate: float,
    tax_exempt: bool,
) -> int:
    """
    General Conditions §11.1:
    Tax on materials earned THIS PERIOD only. $0 if tax_exempt.
    """
    if tax_exempt:
        return 0
    return round_cents(materials_earned_this_period_cents * tax_rate)


def compute_certified_amount(item_data: dict) -> int:
    """
    Master computation per General Conditions §7 through §13.

    This uses the CUMULATIVE method (AIA G702-style):
    1. Total Work Completed to Date for each line item
    2. Plus CO Earned to Date
    3. Plus Stored Materials
    4. = Total Completed & Stored to Date
    5. Less Retention (based on cumulative completion %)
    6. = Net Earned to Date
    7. Less Backcharges
    8. Less Deficiency Holdbacks
    9. Less Liquidated Damages
    10. Less Insurance Deduction (prorated on this period's work only)
    11. Plus Sales Tax (on this period's materials only)
    12. Less Previous Payments (prior certified amounts)
    13. = Current Payment Due
    """
    schedule = item_data["schedule_of_values"]

    # Step 1: Total Work Completed to Date (cumulative) for each line item
    total_completed_to_date = 0
    total_completed_previous = 0
    materials_earned_this_period = 0

    for line in schedule:
        completed_current = round_cents(
            line["scheduled_value_cents"] * line["percent_complete_current"] / 100.0
        )
        completed_previous = round_cents(
            line["scheduled_value_cents"] * line["percent_complete_previous"] / 100.0
        )
        total_completed_to_date += completed_current
        total_completed_previous += completed_previous

        if line.get("is_material", False):
            materials_earned_this_period += (completed_current - completed_previous)

    work_earned_this_period = total_completed_to_date - total_completed_previous

    # Step 2: Change Orders earned to date
    co_earned_to_date = 0
    for co in item_data.get("change_orders", []):
        co_val = compute_change_order_earned(
            co["amount_cents"],
            co["status"],
            co["percent_complete"],
        )
        co_earned_to_date += co_val
        if co.get("is_material", False):
            materials_earned_this_period += co_val

    # Step 3: Stored Materials
    stored_credit = compute_stored_materials_credit(
        item_data.get("stored_materials", [])
    )

    # Step 4: Total Completed & Stored to Date
    total_completed_and_stored = total_completed_to_date + co_earned_to_date + stored_credit

    # Step 5: Retention
    cumulative_pct = item_data["cumulative_percent_complete"]
    retention_rate = compute_retention_rate(cumulative_pct)
    retention_amount = round_cents(total_completed_and_stored * retention_rate)

    # Step 6: Net Earned to Date
    net_earned_to_date = total_completed_and_stored - retention_amount

    # Step 7: Backcharges
    backcharges_total = sum(
        bc["amount_cents"] for bc in item_data.get("backcharges", [])
    )

    # Step 8: Deficiency holdbacks
    deficiency_total = sum(
        d["holdback_cents"] for d in item_data.get("deficiencies", [])
    )

    # Step 9: Liquidated damages
    ld_info = item_data.get("liquidated_damages")
    ld_amount = 0
    if ld_info:
        ld_amount = compute_liquidated_damages(
            ld_info["days_behind"],
            ld_info["daily_rate_cents"],
            ld_info["cap_cents"],
            ld_info.get("is_excusable", False),
        )

    # Step 10: Insurance deduction (on this period's work earned only)
    ins_info = item_data.get("insurance_lapse")
    insurance_deduction = 0
    if ins_info:
        insurance_deduction = compute_insurance_deduction(
            ins_info["lapse_start_day"],
            ins_info["lapse_end_day"],
            item_data["period_start_day"],
            item_data["period_end_day"],
            work_earned_this_period + co_earned_to_date,
        )

    # Step 11: Sales tax (on this period's materials only)
    tax_amount = compute_tax(
        materials_earned_this_period,
        item_data.get("tax_rate", 0.0),
        item_data.get("tax_exempt", False),
    )

    # Step 12: Previous payments
    previous_payments = item_data.get("previous_payments_cents", 0)

    # Step 13: Current Payment Due
    certified = (
        net_earned_to_date
        - backcharges_total
        - deficiency_total
        - ld_amount
        - insurance_deduction
        + tax_amount
        - previous_payments
    )

    return certified


# ---------------------------------------------------------------------------
# Item generation
# ---------------------------------------------------------------------------

def generate_schedule_of_values(rng: random.Random, num_lines: int) -> list[dict]:
    """Generate a realistic schedule of values."""
    available_descs = rng.sample(LINE_ITEM_DESCRIPTIONS, min(num_lines, len(LINE_ITEM_DESCRIPTIONS)))
    lines = []

    for i, desc in enumerate(available_descs):
        is_material = "Material" in desc
        value = rng.randint(8000_00, 95000_00)  # $8k - $95k in cents
        prev_pct = rng.choice([0, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80])
        increment = rng.choice([5, 8, 10, 12, 15, 18, 20, 22, 25])
        curr_pct = min(100, prev_pct + increment)

        lines.append({
            "line_number": i + 1,
            "description": desc,
            "scheduled_value_cents": value,
            "percent_complete_previous": prev_pct,
            "percent_complete_current": curr_pct,
            "is_material": is_material,
        })
    return lines


def generate_change_orders(rng: random.Random, n: int) -> list[dict]:
    """Generate change orders with various statuses."""
    statuses = ["approved", "approved", "pending", "disputed", "rejected"]
    cos = []
    for i in range(n):
        status = rng.choice(statuses)
        amount = rng.randint(3000_00, 40000_00)
        pct = rng.choice([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        is_material = rng.random() < 0.3

        cos.append({
            "co_number": i + 1,
            "description": f"CO-{i+1}: Scope modification",
            "amount_cents": amount,
            "status": status,
            "percent_complete": pct,
            "is_material": is_material,
        })
    return cos


def generate_stored_materials(rng: random.Random, n: int) -> list[dict]:
    """Generate stored materials entries with varying documentation status."""
    materials = []
    for i in range(n):
        value = rng.randint(2000_00, 30000_00)
        has_doc = rng.random() < 0.7
        is_prot = rng.random() < 0.8
        has_ins = rng.random() < 0.75

        materials.append({
            "description": f"Stored material batch {i+1}",
            "value_cents": value,
            "has_documentation": has_doc,
            "is_protected": is_prot,
            "has_insurance": has_ins,
        })
    return materials


def generate_backcharges(rng: random.Random, n: int) -> list[dict]:
    """Generate backcharge entries."""
    reasons = rng.sample(BACKCHARGE_REASONS, min(n, len(BACKCHARGE_REASONS)))
    return [
        {"description": reason, "amount_cents": rng.randint(250_00, 4500_00)}
        for reason in reasons
    ]


def generate_deficiencies(rng: random.Random, n: int) -> list[dict]:
    """Generate deficiency holdback entries."""
    types = rng.sample(DEFICIENCY_TYPES, min(n, len(DEFICIENCY_TYPES)))
    return [
        {"description": dtype, "holdback_cents": rng.randint(500_00, 8000_00)}
        for dtype in types
    ]


def generate_liquidated_damages(rng: random.Random, contract_value: int) -> dict:
    """Generate LD parameters."""
    days_behind = rng.randint(2, 20)
    daily_rate = rng.randint(150_00, 600_00)
    cap_pct = rng.uniform(0.03, 0.08)
    cap = round_cents(contract_value * cap_pct)
    is_excusable = rng.random() < 0.3

    return {
        "days_behind": days_behind,
        "daily_rate_cents": daily_rate,
        "cap_cents": cap,
        "is_excusable": is_excusable,
    }


def generate_insurance_lapse(rng: random.Random, period_start: int, period_end: int) -> dict:
    """Generate an insurance lapse window that overlaps the billing period."""
    lapse_start = rng.randint(period_start - 5, period_start + 15)
    lapse_duration = rng.randint(3, 10)
    lapse_end = lapse_start + lapse_duration
    return {
        "lapse_start_day": lapse_start,
        "lapse_end_day": lapse_end,
    }


def compute_previous_payments(
    schedule: list[dict],
    change_orders: list[dict],
    stored_prior: int,
    prev_cumulative_pct: float,
) -> int:
    """
    Compute what previous payments would have been:
    Prior Total Completed = sum(val * prev_pct / 100)
    Plus CO earned (use 80% of current CO earned as proxy for prior period earned)
    Plus prior stored materials
    Less prior retention
    """
    prior_completed = sum(
        round_cents(line["scheduled_value_cents"] * line["percent_complete_previous"] / 100.0)
        for line in schedule
    )
    prior_cos = sum(
        round_cents(compute_change_order_earned(
            co["amount_cents"], co["status"],
            max(0, co["percent_complete"] - 10)  # prior period had ~10% less CO progress
        ))
        for co in change_orders
    )
    prior_total = prior_completed + prior_cos + stored_prior
    prior_ret_rate = compute_retention_rate(prev_cumulative_pct)
    prior_retention = round_cents(prior_total * prior_ret_rate)
    return prior_total - prior_retention


def generate_item(rng: random.Random, item_id: str, difficulty: str) -> dict:
    """Generate a single benchmark item at the specified difficulty level."""
    trade = rng.choice(TRADE_NAMES)

    if difficulty == "easy":
        num_lines = rng.randint(3, 4)
        num_cos = rng.randint(0, 1)
        num_stored = rng.randint(0, 1)
        num_backcharges = 0
        num_deficiencies = 0
        has_ld = False
        has_insurance_lapse = False
    elif difficulty == "medium":
        num_lines = rng.randint(4, 6)
        num_cos = rng.randint(1, 2)
        num_stored = rng.randint(0, 2)
        num_backcharges = rng.randint(0, 1)
        num_deficiencies = rng.randint(0, 1)
        has_ld = rng.random() < 0.4
        has_insurance_lapse = False
    else:  # hard
        num_lines = rng.randint(5, 7)
        num_cos = rng.randint(2, 3)
        num_stored = rng.randint(1, 3)
        num_backcharges = rng.randint(1, 2)
        num_deficiencies = rng.randint(1, 2)
        has_ld = rng.random() < 0.6
        has_insurance_lapse = rng.random() < 0.5

    schedule = generate_schedule_of_values(rng, num_lines)
    contract_value = sum(line["scheduled_value_cents"] for line in schedule)

    # Cumulative completion = weighted average of current percentages
    weighted_complete = sum(
        line["scheduled_value_cents"] * line["percent_complete_current"]
        for line in schedule
    )
    cumulative_pct = round(weighted_complete / contract_value, 1) if contract_value > 0 else 0.0

    # Previous cumulative (weighted average of previous percentages)
    weighted_prev = sum(
        line["scheduled_value_cents"] * line["percent_complete_previous"]
        for line in schedule
    )
    prev_cumulative_pct = round(weighted_prev / contract_value, 1) if contract_value > 0 else 0.0

    change_orders = generate_change_orders(rng, num_cos) if num_cos > 0 else []
    stored_materials = generate_stored_materials(rng, num_stored) if num_stored > 0 else []
    backcharges = generate_backcharges(rng, num_backcharges) if num_backcharges > 0 else []
    deficiencies = generate_deficiencies(rng, num_deficiencies) if num_deficiencies > 0 else []

    period_start = 1
    period_end = 30

    # Compute realistic previous payments
    previous_payments = compute_previous_payments(
        schedule, change_orders, 0, prev_cumulative_pct
    )

    tax_rate = rng.choice([0.0, 0.04, 0.05, 0.06, 0.065, 0.07, 0.075, 0.08, 0.0825, 0.09])
    tax_exempt = rng.random() < 0.2

    item = {
        "id": item_id,
        "trade": trade,
        "project_name": f"Project {item_id.split('_')[1]}",
        "billing_period": f"Period ending Day {period_end}",
        "period_start_day": period_start,
        "period_end_day": period_end,
        "schedule_of_values": schedule,
        "change_orders": change_orders,
        "stored_materials": stored_materials,
        "backcharges": backcharges,
        "deficiencies": deficiencies,
        "cumulative_percent_complete": cumulative_pct,
        "previous_payments_cents": previous_payments,
        "tax_rate": tax_rate,
        "tax_exempt": tax_exempt,
        "difficulty": difficulty,
    }

    if has_ld:
        item["liquidated_damages"] = generate_liquidated_damages(rng, contract_value)
    if has_insurance_lapse:
        item["insurance_lapse"] = generate_insurance_lapse(rng, period_start, period_end)

    return item


def generate_items(seed: int, count: int) -> list[tuple[dict, int]]:
    """Generate items and their gold answers."""
    rng = random.Random(seed)

    difficulties = []
    easy_count = count // 3
    hard_count = count // 3
    medium_count = count - easy_count - hard_count
    difficulties.extend(["easy"] * easy_count)
    difficulties.extend(["medium"] * medium_count)
    difficulties.extend(["hard"] * hard_count)
    rng.shuffle(difficulties)

    results = []
    for i in range(count):
        item_id = f"cppc_{i+1:03d}"
        item = generate_item(rng, item_id, difficulties[i])
        answer = compute_certified_amount(item)
        results.append((item, answer))

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate CPPC benchmark items")
    parser.add_argument("--sample-count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260516)
    parser.add_argument("--out-dir", type=str, default=".")
    args = parser.parse_args()

    results = generate_items(args.seed, args.sample_count)

    gold_path = os.path.join(args.out_dir, "gold_private_sample.jsonl")
    with open(gold_path, "w") as f:
        for item, answer in results:
            f.write(json.dumps({"id": item["id"], "answer": answer}) + "\n")

    solver_dir = os.path.join(args.out_dir, "solver_bundle")
    os.makedirs(solver_dir, exist_ok=True)
    items_path = os.path.join(solver_dir, "items_private_sample.jsonl")
    with open(items_path, "w") as f:
        for item, _ in results:
            solver_item = deepcopy(item)
            solver_item.pop("difficulty", None)
            f.write(json.dumps(solver_item) + "\n")

    print(f"Generated {args.sample_count} items (seed={args.seed})")
    print(f"  Gold answers: {gold_path}")
    print(f"  Solver items: {items_path}")


if __name__ == "__main__":
    main()
