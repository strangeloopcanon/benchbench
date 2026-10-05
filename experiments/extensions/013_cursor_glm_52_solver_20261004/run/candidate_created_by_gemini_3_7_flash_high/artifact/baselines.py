#!/usr/bin/env python3
"""
Baseline Solvers for CloudSLA-Forensics
Implements multiple baseline strategies:
1. Gold Identity Baseline (Sanity check)
2. Naive First-Order Sum Baseline (Sums raw downtime, ignores exclusions, caps, and addenda)
3. Direct Telemetry Baseline (Calculates telemetry downtime without reading tickets/RCA/maintenance notices)
4. Heuristic Contract Baseline (Reads contract and telemetry, but ignores deduplication and notice timeliness)
"""

import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List


def parse_iso(dt_str: str) -> datetime.datetime:
    dt_str = dt_str.replace("Z", "+00:00")
    return datetime.datetime.fromisoformat(dt_str)


def solve_naive_first_order(case_dir: str) -> int:
    """
    Naive baseline: Sums all raw incident durations, ignores deduplication,
    ignores maintenance exemptions, assumes basic 10% credit tier.
    """
    with open(os.path.join(case_dir, "billing_statement.json"), "r") as f:
        billing = json.load(f)
    mrc_cents = billing["monthly_recurring_charge_cents"]

    with open(os.path.join(case_dir, "telemetry", "telemetry_events.json"), "r") as f:
        telemetry = json.load(f)

    # Just give 10% credit if any incident occurred
    if len(telemetry.get("incident_events", [])) > 0:
        return (mrc_cents * 10) // 100
    return 0


def solve_direct_telemetry(case_dir: str) -> int:
    """
    Direct Telemetry Baseline:
    Computes downtime purely from telemetry JSON without reading tickets, RCAs, or maintenance notices.
    Assumes standard contract tier and does not account for maintenance notice validity or RCA customer fault.
    """
    with open(os.path.join(case_dir, "billing_statement.json"), "r") as f:
        billing = json.load(f)
    mrc_cents = billing["monthly_recurring_charge_cents"]
    total_minutes = billing.get("total_period_minutes", 43200)

    with open(os.path.join(case_dir, "telemetry", "telemetry_events.json"), "r") as f:
        telemetry = json.load(f)

    total_down = sum(inc.get("duration_minutes", 0) for inc in telemetry.get("incident_events", []))
    uptime_pct = ((total_minutes - total_down) / total_minutes) * 100.0

    credit_pct = 0
    if uptime_pct < 99.0:
        credit_pct = 50
    elif uptime_pct < 99.5:
        credit_pct = 25
    elif uptime_pct < 99.9:
        credit_pct = 10

    gross = (mrc_cents * credit_pct) // 100
    return gross


def main():
    parser = argparse.ArgumentParser(description="Run Baselines on CloudSLA-Forensics")
    parser.add_argument("--items", type=str, default="solver_bundle/items_private_sample.jsonl")
    parser.add_argument("--gold", type=str, default="gold_private_sample.jsonl")
    parser.add_argument("--mode", choices=["gold", "naive", "direct_telemetry"], default="naive")
    parser.add_argument("--out", type=str, default="predictions.jsonl")
    args = parser.parse_args()

    items = []
    with open(args.items, "r") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    solver_bundle_dir = os.path.dirname(os.path.abspath(args.items))

    preds = []
    if args.mode == "gold":
        with open(args.gold, "r") as f:
            for line in f:
                if line.strip():
                    preds.append(json.loads(line))
    else:
        for item in items:
            case_dir = os.path.join(solver_bundle_dir, item["case_directory"])
            if args.mode == "naive":
                ans = solve_naive_first_order(case_dir)
            elif args.mode == "direct_telemetry":
                ans = solve_direct_telemetry(case_dir)
            else:
                ans = 0
            preds.append({"id": item["id"], "answer": ans})

    with open(args.out, "w") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")

    print(f"Generated {len(preds)} predictions using mode '{args.mode}' to {args.out}")


if __name__ == "__main__":
    main()
