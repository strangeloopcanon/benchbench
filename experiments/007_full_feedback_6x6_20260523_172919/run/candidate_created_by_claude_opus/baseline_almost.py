#!/usr/bin/env python3
"""
Nearly-correct baseline that implements everything correctly EXCEPT:
- Always uses 10% retention (misses the 50% threshold reduction to 5%)

This tests how sensitive the benchmark is to the retention rule.
"""

import json
from generator import (
    round_cents, compute_change_order_earned,
    compute_stored_materials_credit, compute_liquidated_damages,
    compute_insurance_deduction, compute_tax,
)


def almost_correct_amount(item_data: dict) -> int:
    schedule = item_data["schedule_of_values"]

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

    co_earned_to_date = 0
    for co in item_data.get("change_orders", []):
        co_val = compute_change_order_earned(
            co["amount_cents"], co["status"], co["percent_complete"]
        )
        co_earned_to_date += co_val
        if co.get("is_material", False):
            materials_earned_this_period += co_val

    stored_credit = compute_stored_materials_credit(
        item_data.get("stored_materials", [])
    )

    total_completed_and_stored = total_completed_to_date + co_earned_to_date + stored_credit

    # BUG: Always use 10% retention
    retention_rate = 0.10
    retention_amount = round_cents(total_completed_and_stored * retention_rate)
    net_earned = total_completed_and_stored - retention_amount

    backcharges = sum(bc["amount_cents"] for bc in item_data.get("backcharges", []))
    deficiencies = sum(d["holdback_cents"] for d in item_data.get("deficiencies", []))

    ld_info = item_data.get("liquidated_damages")
    ld_amount = 0
    if ld_info:
        ld_amount = compute_liquidated_damages(
            ld_info["days_behind"], ld_info["daily_rate_cents"],
            ld_info["cap_cents"], ld_info.get("is_excusable", False)
        )

    ins_info = item_data.get("insurance_lapse")
    insurance_deduction = 0
    if ins_info:
        insurance_deduction = compute_insurance_deduction(
            ins_info["lapse_start_day"], ins_info["lapse_end_day"],
            item_data["period_start_day"], item_data["period_end_day"],
            work_earned_this_period + co_earned_to_date,
        )

    tax_amount = compute_tax(
        materials_earned_this_period,
        item_data.get("tax_rate", 0.0),
        item_data.get("tax_exempt", False),
    )

    previous_payments = item_data.get("previous_payments_cents", 0)

    return (net_earned - backcharges - deficiencies - ld_amount
            - insurance_deduction + tax_amount - previous_payments)


def main():
    items = []
    with open("solver_bundle/items_private_sample.jsonl") as f:
        for line in f:
            items.append(json.loads(line))

    with open("predictions_almost.jsonl", "w") as f:
        for item in items:
            answer = almost_correct_amount(item)
            f.write(json.dumps({"id": item["id"], "answer": answer}) + "\n")

    print("Almost-correct baseline written")


if __name__ == "__main__":
    main()
