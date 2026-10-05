#!/usr/bin/env python3
"""
CloudSLA-Forensics Verifier
Verifies dataset integrity, asset completeness, absence of leakage, schema compliance,
and mathematical consistency between public case files and gold answers.
"""

import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Set, Tuple


def parse_iso(dt_str: str) -> datetime.datetime:
    """Parses ISO 8601 UTC timestamp."""
    dt_str = dt_str.replace("Z", "+00:00")
    return datetime.datetime.fromisoformat(dt_str)


def solve_case_from_public_assets(case_dir: str, contract_framework_rules: Dict[str, Any]) -> int:
    """
    Independent reference solver that reads ONLY the public case files in case_dir
    and evaluates the exact net credit in USD cents using the public CONTRACT_FRAMEWORK rules.
    """
    # 1. Read contract.md
    with open(os.path.join(case_dir, "contract.md"), "r", encoding="utf-8") as f:
        contract_text = f.read()

    # 2. Read billing_statement.json
    with open(os.path.join(case_dir, "billing_statement.json"), "r", encoding="utf-8") as f:
        billing = json.load(f)

    mrc_cents = billing["monthly_recurring_charge_cents"]
    variable_cents = billing.get("variable_usage_charge_cents", 0)
    prior_credits_cents = billing.get("prior_credits_issued_cents", 0)
    cap_pct = billing.get("max_monthly_credit_cap_percent", 50)
    total_period_minutes = billing.get("total_period_minutes", 43200)

    # 3. Read architecture_profile.json
    with open(os.path.join(case_dir, "architecture_profile.json"), "r", encoding="utf-8") as f:
        arch = json.load(f)
    multi_az = arch.get("multi_az_enabled", False)

    # Determine contract tier and addenda from contract text
    is_vip = "MISSION_CRITICAL_VIP" in contract_text
    is_fintech = "HIGH_THROUGHPUT_FINTECH" in contract_text

    if is_vip:
        target_availability = 99.99
        tier_thresholds = [
            (99.95, 99.99, 15),
            (99.90, 99.95, 30),
            (0.0, 99.90, 60),
        ]
        vip_multiplier = 1.5 if multi_az else 1.0
        applies_to_variable = True
    elif is_fintech:
        target_availability = 99.95
        tier_thresholds = [
            (99.90, 99.95, 10),
            (99.50, 99.90, 25),
            (0.0, 99.50, 50),
        ]
        vip_multiplier = 1.25 if multi_az else 1.0
        applies_to_variable = False
    else:
        target_availability = 99.90
        tier_thresholds = [
            (99.50, 99.90, 10),
            (99.00, 99.50, 25),
            (0.0, 99.00, 50),
        ]
        vip_multiplier = 1.0
        applies_to_variable = False

    # 4. Read telemetry_events.json
    with open(os.path.join(case_dir, "telemetry", "telemetry_events.json"), "r", encoding="utf-8") as f:
        telemetry = json.load(f)

    incident_events = telemetry.get("incident_events", [])

    # Base reference date for month (April 2026)
    month_start_dt = parse_iso("2026-04-01T00:00:00Z")

    compensable_intervals: List[Tuple[int, int]] = []

    # Check dossiers
    dossiers_dir = os.path.join(case_dir, "dossiers")

    for inc in incident_events:
        inc_id = inc["incident_id"]
        start_dt = parse_iso(inc["start_time"])
        end_dt = parse_iso(inc["end_time"])
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        start_min = int((start_dt - month_start_dt).total_seconds() / 60)
        end_min = start_min + duration_minutes

        error_rate = inc.get("error_rate_pct", 100.0)
        if error_rate < 5.0:
            # Below threshold -> 0 compensable minutes
            continue

        scenario_type = inc.get("scenario_type", "STANDARD_PROVIDER_OUTAGE")

        # Check for maintenance notice
        maint_dir = os.path.join(dossiers_dir, "maintenance")
        matching_notice = None
        if os.path.exists(maint_dir):
            for fname in os.listdir(maint_dir):
                if fname.endswith(".json"):
                    with open(os.path.join(maint_dir, fname), "r", encoding="utf-8") as f:
                        notice_data = json.load(f)
                        if notice_data.get("service") == inc["service_id"] and notice_data.get("target_window_start") == inc["start_time"]:
                            matching_notice = notice_data
                            break

        # Check for RCA report
        rca_dir = os.path.join(dossiers_dir, "rca")
        matching_rca = None
        if os.path.exists(rca_dir):
            for fname in os.listdir(rca_dir):
                if fname.endswith(".json"):
                    with open(os.path.join(rca_dir, fname), "r", encoding="utf-8") as f:
                        rca_data = json.load(f)
                        if rca_data.get("incident_id") == inc_id:
                            matching_rca = rca_data
                            break

        if matching_notice:
            # Evaluate notice lead time
            notice_sent_dt = parse_iso(matching_notice["notice_sent_at"])
            window_start_dt = parse_iso(matching_notice["target_window_start"])
            lead_hours = (window_start_dt - notice_sent_dt).total_seconds() / 3600.0

            target_window_end_dt = parse_iso(matching_notice["target_window_end"])
            scheduled_min = int((target_window_end_dt - window_start_dt).total_seconds() / 60)

            if lead_hours >= 72.0:
                # Timely notice: scheduled duration is exempt; only overrun is compensable
                if duration_minutes > scheduled_min:
                    overrun_min = duration_minutes - scheduled_min
                    compensable_intervals.append((start_min + scheduled_min, end_min))
            else:
                # Tardy notice: zero exemption; full duration compensable
                compensable_intervals.append((start_min, end_min))

        elif matching_rca:
            # Check customer fault allocation in timeline breakdown
            customer_fault_min = 0
            for phase in matching_rca.get("timeline_breakdown", []):
                if phase.get("attributable_party") == "CUSTOMER":
                    customer_fault_min += phase.get("duration_minutes", 0)
            
            compensable_duration = max(0, duration_minutes - customer_fault_min)
            if compensable_duration > 0:
                compensable_intervals.append((start_min + customer_fault_min, end_min))

        elif scenario_type == "FORCE_MAJEURE_WITH_RTO":
            # 30 min RTO grace
            rto_grace = 30
            if duration_minutes > rto_grace:
                compensable_intervals.append((start_min + rto_grace, end_min))

        else:
            # Full provider outage
            compensable_intervals.append((start_min, end_min))

    # Interval union calculation
    compensable_intervals.sort(key=lambda x: (x[0], x[1]))
    merged = []
    for s, e in compensable_intervals:
        if s >= e:
            continue
        if not merged:
            merged.append((s, e))
        else:
            ps, pe = merged[-1]
            if s <= pe:
                merged[-1] = (ps, max(pe, e))
            else:
                merged.append((s, e))

    total_compensable_minutes = sum(e - s for s, e in merged)

    # Uptime %
    effective_uptime_pct = ((total_period_minutes - total_compensable_minutes) / total_period_minutes) * 100.0

    credit_pct = 0
    for min_u, max_u, pct in tier_thresholds:
        if min_u <= effective_uptime_pct < max_u:
            credit_pct = pct
            break
    if effective_uptime_pct < tier_thresholds[-1][0]:
        credit_pct = tier_thresholds[-1][2]

    base_charge = mrc_cents + variable_cents if applies_to_variable else mrc_cents
    vip_mult_x100 = int(round(vip_multiplier * 100))
    gross_credit = (base_charge * credit_pct * vip_mult_x100 + 5000) // 10000

    max_cap = (mrc_cents * cap_pct) // 100
    capped_credit = min(gross_credit, max_cap)
    net_credit = max(0, capped_credit - prior_credits_cents)

    return net_credit


def check_leakage(solver_bundle_dir: str) -> List[str]:
    """Scans solver bundle to ensure no answer files, gold references, or private traces exist."""
    forbidden_terms = [
        "gold_private_sample",
        "gold_cents",
        "final_net_credit_cents",
        "private_audit_trace",
        "oracle_solver"
    ]
    leakage_issues = []

    for root, _, files in os.walk(solver_bundle_dir):
        for f in files:
            full_p = os.path.join(root, f)
            if f in ["gold_private_sample.jsonl", "verifier.py", "scorer.py", "validation_report.md", "failure_modes.md"]:
                leakage_issues.append(f"Forbidden root file found inside solver bundle: {f}")
                continue

            try:
                with open(full_p, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                    for term in forbidden_terms:
                        if term in content:
                            leakage_issues.append(f"Potential leakage term '{term}' in {full_p}")
            except Exception as e:
                leakage_issues.append(f"Could not read {full_p}: {e}")

    return leakage_issues


def main():
    parser = argparse.ArgumentParser(description="CloudSLA-Forensics Verifier")
    parser.add_argument("--items", type=str, required=True, help="Path to items_private_sample.jsonl")
    parser.add_argument("--gold", type=str, required=True, help="Path to gold_private_sample.jsonl")
    args = parser.parse_args()

    items_path = os.path.abspath(args.items)
    gold_path = os.path.abspath(args.gold)

    if not os.path.exists(items_path):
        print(f"[FAIL] Items file not found: {items_path}")
        sys.exit(1)
    if not os.path.exists(gold_path):
        print(f"[FAIL] Gold file not found: {gold_path}")
        sys.exit(1)

    solver_bundle_dir = os.path.dirname(items_path)

    # 1. Load Items
    items = []
    with open(items_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                items.append(data)
            except Exception as e:
                print(f"[FAIL] Malformed JSON in items at line {line_num}: {e}")
                sys.exit(1)

    # 2. Load Gold
    gold = []
    with open(gold_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                gold.append(data)
            except Exception as e:
                print(f"[FAIL] Malformed JSON in gold at line {line_num}: {e}")
                sys.exit(1)

    print(f"[CHECK 1] Count Check: Items count = {len(items)}, Gold count = {len(gold)}")
    if len(items) != len(gold):
        print(f"[FAIL] Count mismatch between items ({len(items)}) and gold ({len(gold)})")
        sys.exit(1)

    # 3. ID Matching and Schema Check
    gold_dict = {}
    for g in gold:
        if "id" not in g or "answer" not in g:
            print(f"[FAIL] Gold row missing 'id' or 'answer': {g}")
            sys.exit(1)
        if not isinstance(g["answer"], int) or g["answer"] < 0:
            print(f"[FAIL] Gold answer must be non-negative integer: {g}")
            sys.exit(1)
        gold_dict[g["id"]] = g["answer"]

    # 4. Verify all asset files exist for each item
    for item in items:
        item_id = item.get("id")
        if item_id not in gold_dict:
            print(f"[FAIL] Item ID {item_id} not found in gold dataset")
            sys.exit(1)

        case_dir = os.path.join(solver_bundle_dir, item["case_directory"])
        if not os.path.isdir(case_dir):
            print(f"[FAIL] Case directory does not exist: {case_dir}")
            sys.exit(1)

        for req_key in ["contract_file", "billing_file", "architecture_file", "telemetry_file"]:
            req_rel = item.get(req_key)
            if not req_rel:
                print(f"[FAIL] Item {item_id} missing reference key {req_key}")
                sys.exit(1)
            req_full = os.path.join(solver_bundle_dir, req_rel)
            if not os.path.exists(req_full) or os.path.getsize(req_full) == 0:
                print(f"[FAIL] Asset file missing or empty: {req_full}")
                sys.exit(1)

    print("[PASS] Asset existence and schema check passed.")

    # 5. Check Leakage
    leakage = check_leakage(solver_bundle_dir)
    if leakage:
        print("[FAIL] Leakage detected in solver bundle:")
        for leak in leakage:
            print(f"  - {leak}")
        sys.exit(1)
    print("[PASS] Zero leakage verified in solver bundle.")

    # 6. Re-solve cases independently and verify exact match against gold answers
    mismatches = []
    for item in items:
        item_id = item["id"]
        case_dir = os.path.join(solver_bundle_dir, item["case_directory"])
        derived_answer = solve_case_from_public_assets(case_dir, {})
        expected_answer = gold_dict[item_id]
        if derived_answer != expected_answer:
            mismatches.append((item_id, derived_answer, expected_answer))

    if mismatches:
        print(f"[FAIL] Mathematical re-derivation mismatches on {len(mismatches)} items:")
        for item_id, derived, expected in mismatches:
            print(f"  - {item_id}: Derived={derived}, Expected Gold={expected}")
        sys.exit(1)

    print(f"[PASS] 100% Mathematical verification passed ({len(items)}/{len(items)} items independently confirmed).")
    print("\n[SUCCESS] Benchmark verification fully passed. Ready for evaluation.")
    sys.exit(0)


if __name__ == "__main__":
    main()
