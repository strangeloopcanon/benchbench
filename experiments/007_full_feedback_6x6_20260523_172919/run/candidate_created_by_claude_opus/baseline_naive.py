#!/usr/bin/env python3
"""
Weak baseline solver that makes common mistakes:
1. Uses flat 10% retention (ignores 50% threshold reduction to 5%)
2. Gives credit to ALL stored materials (ignores the 3-condition check)
3. Bills ALL change orders at 100% (ignores pending/disputed/rejected status)
4. Ignores insurance deduction entirely
5. Ignores sales tax entirely
6. Does apply backcharges, deficiencies, LDs, and previous payments correctly

This tests whether edge cases matter for scoring.
"""

import json

from generator import round_cents, compute_liquidated_damages


def naive_certified_amount(item_data: dict) -> int:
    schedule = item_data["schedule_of_values"]

    # Cumulative work completed
    total_completed = sum(
        round_cents(line["scheduled_value_cents"] * line["percent_complete_current"] / 100.0)
        for line in schedule
    )

    # Mistake 1: Bill ALL COs at 100% regardless of status
    co_earned = sum(
        round_cents(co["amount_cents"] * co["percent_complete"] / 100.0)
        for co in item_data.get("change_orders", [])
    )

    # Mistake 2: Give credit to ALL stored materials
    stored_credit = sum(
        mat["value_cents"] for mat in item_data.get("stored_materials", [])
    )

    total = total_completed + co_earned + stored_credit

    # Mistake 3: Always use 10% retention (ignore threshold)
    retention = round_cents(total * 0.10)
    net = total - retention

    # Backcharges and deficiencies (correct)
    backcharges = sum(bc["amount_cents"] for bc in item_data.get("backcharges", []))
    deficiencies = sum(d["holdback_cents"] for d in item_data.get("deficiencies", []))

    # LDs (correct)
    ld_info = item_data.get("liquidated_damages")
    ld_amount = 0
    if ld_info:
        ld_amount = compute_liquidated_damages(
            ld_info["days_behind"],
            ld_info["daily_rate_cents"],
            ld_info["cap_cents"],
            ld_info.get("is_excusable", False),
        )

    # Mistake 4: Skip insurance deduction
    # Mistake 5: Skip tax

    previous_payments = item_data.get("previous_payments_cents", 0)

    certified = net - backcharges - deficiencies - ld_amount - previous_payments
    return certified


def main():
    items = []
    with open("solver_bundle/items_private_sample.jsonl") as f:
        for line in f:
            items.append(json.loads(line))

    predictions = []
    for item in items:
        answer = naive_certified_amount(item)
        predictions.append({"id": item["id"], "answer": answer})

    with open("predictions_naive.jsonl", "w") as f:
        for pred in predictions:
            f.write(json.dumps(pred) + "\n")

    print(f"Naive baseline: {len(predictions)} predictions written to predictions_naive.jsonl")


if __name__ == "__main__":
    main()
