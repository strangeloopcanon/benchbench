#!/usr/bin/env python3
"""
CloudSLA-Forensics Generator
Generates realistic, deterministic, multi-document enterprise cloud SLA arbitration cases,
complete solver bundle with public contract frameworks, incident telemetry, ticket dossiers,
and exact gold settlement answers.
"""

import argparse
import datetime
import json
import os
import random
import shutil
from typing import Any, Dict, List, Tuple


def iso_utc(dt: datetime.datetime) -> str:
    """Format datetime to ISO 8601 UTC string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_case_data(case_idx: int, seed: int) -> Tuple[Dict[str, Any], Dict[str, Any], int, Dict[str, Any]]:
    """
    Generates a single case with full forensic documents and computes the exact gold answer.
    Returns: (item_meta, case_files_dict, gold_answer_cents, audit_trace)
    """
    rng = random.Random(seed + case_idx * 9973)

    case_id = f"case_{case_idx+1:03d}"
    difficulty_tier = 1 + (case_idx // 6)  # 1 to 5

    # Base monthly timing (April 2026 = 30 days = 43,200 minutes)
    month_days = 30
    total_month_minutes = month_days * 24 * 60
    base_date = datetime.datetime(2026, 4, 1, 0, 0, 0)
    month_end_date = base_date + datetime.timedelta(days=month_days)

    # Billing parameters
    # Monthly Recurring Charge (MRC) in cents: between $10,000 and $100,000
    mrc_cents = rng.choice([1200000, 2400000, 3600000, 4800000, 6000000, 7500000, 9000000, 12000000])
    variable_spend_cents = rng.randint(50000, 500000) * 100
    prior_credits_cents = 0
    if difficulty_tier >= 4 and rng.random() < 0.6:
        prior_credits_cents = rng.choice([50000, 100000, 150000, 250000, 500000])

    # Contract tier configuration
    contract_tier_type = "STANDARD_ENTERPRISE"
    if difficulty_tier >= 4:
        contract_tier_type = rng.choice(["STANDARD_ENTERPRISE", "MISSION_CRITICAL_VIP", "HIGH_THROUGHPUT_FINTECH"])

    # Multi-AZ topology configuration
    customer_has_multi_az = True
    if difficulty_tier >= 3 and rng.random() < 0.45:
        customer_has_multi_az = False

    # Contract Terms definition
    if contract_tier_type == "MISSION_CRITICAL_VIP":
        target_availability = 99.99
        tier_thresholds = [
            {"min_uptime": 99.95, "max_uptime": 99.99, "credit_pct": 15},
            {"min_uptime": 99.90, "max_uptime": 99.95, "credit_pct": 30},
            {"min_uptime": 0.0, "max_uptime": 99.90, "credit_pct": 60},
        ]
        cap_pct = 100
        vip_multiplier = 1.5 if customer_has_multi_az else 1.0
        applies_to_variable = True
    elif contract_tier_type == "HIGH_THROUGHPUT_FINTECH":
        target_availability = 99.95
        tier_thresholds = [
            {"min_uptime": 99.90, "max_uptime": 99.95, "credit_pct": 10},
            {"min_uptime": 99.50, "max_uptime": 99.90, "credit_pct": 25},
            {"min_uptime": 0.0, "max_uptime": 99.50, "credit_pct": 50},
        ]
        cap_pct = 75
        vip_multiplier = 1.25 if customer_has_multi_az else 1.0
        applies_to_variable = False
    else:
        target_availability = 99.90
        tier_thresholds = [
            {"min_uptime": 99.50, "max_uptime": 99.90, "credit_pct": 10},
            {"min_uptime": 99.00, "max_uptime": 99.50, "credit_pct": 25},
            {"min_uptime": 0.0, "max_uptime": 99.00, "credit_pct": 50},
        ]
        cap_pct = 50
        vip_multiplier = 1.0
        applies_to_variable = False

    # Number of incident events
    num_incidents = rng.randint(1, 2) if difficulty_tier == 1 else rng.randint(2, 4)
    if difficulty_tier >= 4:
        num_incidents = rng.randint(3, 5)

    services_list = ["core-compute-cluster", "managed-relational-db", "edge-api-gateway", "distributed-object-storage"]

    incidents = []
    tickets = []
    rca_reports = []
    maintenance_notices = []

    # Track intervals for exact ground truth calculation
    # Interval format: (start_minute, end_minute, compensable_fraction, incident_id, reason)
    raw_outage_intervals: List[Tuple[int, int, str]] = []
    deductions_log: List[Dict[str, Any]] = []

    current_day_offset = 2

    for inc_i in range(num_incidents):
        inc_id = f"INC-2026-{100 + case_idx*10 + inc_i}"
        service = rng.choice(services_list)
        
        # Start day within the month
        day = min(28, current_day_offset + rng.randint(1, 5))
        current_day_offset = day
        hour = rng.randint(1, 22)
        minute = rng.randint(0, 50)
        start_dt = base_date + datetime.timedelta(days=day-1, hours=hour, minutes=minute)
        
        duration_minutes = rng.choice([25, 45, 60, 90, 120, 180, 240, 360])
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
        
        start_minute_of_month = (day - 1) * 1440 + hour * 60 + minute
        end_minute_of_month = start_minute_of_month + duration_minutes

        # Decide incident scenario type
        scenario_type = "STANDARD_PROVIDER_OUTAGE"
        if difficulty_tier >= 2 and inc_i == 0 and rng.random() < 0.5:
            scenario_type = "MAINTENANCE_OVERRUN"
        elif difficulty_tier >= 3 and rng.random() < 0.4:
            scenario_type = "PARTIAL_CUSTOMER_FAULT"
        elif difficulty_tier >= 4 and rng.random() < 0.35:
            scenario_type = "FORCE_MAJEURE_WITH_RTO"
        elif difficulty_tier >= 2 and rng.random() < 0.3:
            scenario_type = "BELOW_THRESHOLD_DISTRACTOR"

        error_rate_pct = rng.choice([15.4, 42.0, 78.5, 99.9, 100.0])
        if scenario_type == "BELOW_THRESHOLD_DISTRACTOR":
            error_rate_pct = rng.choice([0.5, 1.2, 2.4, 4.8])  # Threshold is 5.0% or 10.0%

        compensable_minutes = 0
        customer_fault_minutes = 0
        rto_grace_minutes = 0
        maintenance_notice_valid = False

        if scenario_type == "BELOW_THRESHOLD_DISTRACTOR":
            # 0 compensable minutes because error rate is below contract threshold
            compensable_minutes = 0
            tickets.append({
                "ticket_id": inc_id,
                "service": service,
                "title": f"Intermittent latency alerts on {service}",
                "opened_at": iso_utc(start_dt),
                "closed_at": iso_utc(end_dt),
                "reported_by": "Customer DevOps Monitoring",
                "telemetry_error_rate_pct": error_rate_pct,
                "provider_finding": f"Observed error rate was {error_rate_pct}%, which is below the 5.0% Outage threshold defined in Exhibit A §2.1. No compensable downtime accrued.",
                "status": "RESOLVED_NON_SLA_IMPACTING"
            })
            deductions_log.append({
                "incident_id": inc_id,
                "gross_duration_min": duration_minutes,
                "compensable_min": 0,
                "reason": f"Telemetry error rate {error_rate_pct}% did not breach minimum 5.0% threshold"
            })

        elif scenario_type == "MAINTENANCE_OVERRUN":
            # Scheduled maintenance notice
            scheduled_duration = rng.choice([60, 120])
            overrun_minutes = duration_minutes if duration_minutes > scheduled_duration else 30
            duration_minutes = scheduled_duration + overrun_minutes
            end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
            end_minute_of_month = start_minute_of_month + duration_minutes

            # Notice advance time: standard requires >= 72 hours
            # In some cases notice was timely (80h before), in others tardy (48h before)
            notice_is_timely = rng.choice([True, False]) if difficulty_tier >= 3 else True
            notice_lead_hours = rng.randint(75, 120) if notice_is_timely else rng.randint(24, 60)
            notice_dt = start_dt - datetime.timedelta(hours=notice_lead_hours)

            maint_id = f"MAINT-2026-{200 + inc_i}"
            maintenance_notices.append({
                "notice_id": maint_id,
                "service": service,
                "target_window_start": iso_utc(start_dt),
                "target_window_end": iso_utc(start_dt + datetime.timedelta(minutes=scheduled_duration)),
                "notice_sent_at": iso_utc(notice_dt),
                "advance_notice_hours": notice_lead_hours,
                "scope": f"Kernel patch and memory scaling on {service}"
            })

            if notice_is_timely:
                # Scheduled window is exempt; only overrun counts as unscheduled outage
                compensable_minutes = overrun_minutes
                comp_start = start_minute_of_month + scheduled_duration
                comp_end = end_minute_of_month
                raw_outage_intervals.append((comp_start, comp_end, inc_id))
                deductions_log.append({
                    "incident_id": inc_id,
                    "gross_duration_min": duration_minutes,
                    "exempt_maintenance_min": scheduled_duration,
                    "compensable_min": overrun_minutes,
                    "reason": f"Timely notice ({notice_lead_hours}h >= 72h). Scheduled {scheduled_duration}m exempt; {overrun_minutes}m overrun compensable."
                })
            else:
                # Tardy notice fails 72h rule; entire duration is treated as unscheduled outage!
                compensable_minutes = duration_minutes
                raw_outage_intervals.append((start_minute_of_month, end_minute_of_month, inc_id))
                deductions_log.append({
                    "incident_id": inc_id,
                    "gross_duration_min": duration_minutes,
                    "exempt_maintenance_min": 0,
                    "compensable_min": duration_minutes,
                    "reason": f"Tardy notice ({notice_lead_hours}h < 72h rule). Zero exemption granted; full {duration_minutes}m compensable."
                })

            tickets.append({
                "ticket_id": inc_id,
                "service": service,
                "title": f"Maintenance Window Execution & Overrun on {service}",
                "opened_at": iso_utc(start_dt),
                "closed_at": iso_utc(end_dt),
                "reported_by": "Cloud Operations Automated Dispatch",
                "associated_maintenance_id": maint_id,
                "notice_sent_timestamp": iso_utc(notice_dt),
                "scheduled_minutes": scheduled_duration,
                "actual_minutes": duration_minutes,
                "status": "CLOSED"
            })

        elif scenario_type == "PARTIAL_CUSTOMER_FAULT":
            customer_fault_minutes = rng.choice([20, 30, 45, 60])
            if customer_fault_minutes >= duration_minutes:
                customer_fault_minutes = duration_minutes // 2
            
            compensable_minutes = duration_minutes - customer_fault_minutes
            comp_start = start_minute_of_month + customer_fault_minutes
            comp_end = end_minute_of_month
            raw_outage_intervals.append((comp_start, comp_end, inc_id))

            rca_id = f"RCA-2026-{300 + inc_i}"
            rca_reports.append({
                "rca_id": rca_id,
                "incident_id": inc_id,
                "service": service,
                "total_outage_duration_minutes": duration_minutes,
                "timeline_breakdown": [
                    {
                        "phase": "Customer Misconfiguration / Internal Deadlock",
                        "duration_minutes": customer_fault_minutes,
                        "attributable_party": "CUSTOMER",
                        "details": f"Customer deploy script applied malformed connection pool config, causing self-inflicted drop for {customer_fault_minutes} min."
                    },
                    {
                        "phase": "Provider Infrastructure Hypervisor Fault",
                        "duration_minutes": compensable_minutes,
                        "attributable_party": "PROVIDER",
                        "details": f"Underlying host node suffered power rail failure requiring hardware migration for {compensable_minutes} min."
                    }
                ],
                "final_finding": f"Per SLA §5.3, {customer_fault_minutes} min attributable to customer action is excluded. {compensable_minutes} min is provider compensable."
            })

            tickets.append({
                "ticket_id": inc_id,
                "service": service,
                "title": f"Critical degradation and crash loop on {service}",
                "opened_at": iso_utc(start_dt),
                "closed_at": iso_utc(end_dt),
                "reported_by": "Customer Site Reliability Lead",
                "associated_rca": rca_id,
                "telemetry_error_rate_pct": error_rate_pct,
                "status": "CLOSED_WITH_RCA"
            })

            deductions_log.append({
                "incident_id": inc_id,
                "gross_duration_min": duration_minutes,
                "customer_fault_min": customer_fault_minutes,
                "compensable_min": compensable_minutes,
                "reason": f"RCA apportioned {customer_fault_minutes}m to customer error; remaining {compensable_minutes}m compensable."
            })

        elif scenario_type == "FORCE_MAJEURE_WITH_RTO":
            # Contract §6.2: Force majeure power grid / Tier-1 transit cut has 30 min RTO grace period.
            # Time beyond RTO is compensable.
            rto_grace_minutes = 30
            if duration_minutes <= rto_grace_minutes:
                compensable_minutes = 0
            else:
                compensable_minutes = duration_minutes - rto_grace_minutes
                comp_start = start_minute_of_month + rto_grace_minutes
                comp_end = end_minute_of_month
                raw_outage_intervals.append((comp_start, comp_end, inc_id))

            tickets.append({
                "ticket_id": inc_id,
                "service": service,
                "title": f"Upstream Tier-1 Metro Fiber Cut affecting {service}",
                "opened_at": iso_utc(start_dt),
                "closed_at": iso_utc(end_dt),
                "reported_by": "NOC Automated Alert",
                "root_cause_category": "FORCE_MAJEURE_TRANSIT_CUT",
                "upstream_carrier_ticket": "ZAYO-FIBER-88492-CHI",
                "details": f"Regional fiber severed by third-party civil excavation. Provider automated rerouting completed. Duration: {duration_minutes}m. SLA §6.2 grants 30m RTO grace period.",
                "status": "CLOSED"
            })

            deductions_log.append({
                "incident_id": inc_id,
                "gross_duration_min": duration_minutes,
                "rto_grace_min": rto_grace_minutes,
                "compensable_min": compensable_minutes,
                "reason": f"Force Majeure carrier event: {rto_grace_minutes}m RTO grace excluded per §6.2; excess {compensable_minutes}m compensable."
            })

        else:  # STANDARD_PROVIDER_OUTAGE
            compensable_minutes = duration_minutes
            raw_outage_intervals.append((start_minute_of_month, end_minute_of_month, inc_id))

            tickets.append({
                "ticket_id": inc_id,
                "service": service,
                "title": f"Unscheduled Outage on {service} due to storage control plane crash",
                "opened_at": iso_utc(start_dt),
                "closed_at": iso_utc(end_dt),
                "reported_by": "Automated Health Probe",
                "telemetry_error_rate_pct": error_rate_pct,
                "details": f"Storage volume orchestrator deadlocked causing API requests to fail with HTTP 500 for {duration_minutes} minutes.",
                "status": "CLOSED"
            })

            deductions_log.append({
                "incident_id": inc_id,
                "gross_duration_min": duration_minutes,
                "compensable_min": duration_minutes,
                "reason": f"Full unexcused provider outage for {duration_minutes}m."
            })

        incidents.append({
            "incident_id": inc_id,
            "service_id": service,
            "start_time": iso_utc(start_dt),
            "end_time": iso_utc(end_dt),
            "duration_minutes": duration_minutes,
            "error_rate_pct": error_rate_pct,
            "availability_zone": "us-east-1a" if not customer_has_multi_az else rng.choice(["us-east-1a", "us-east-1b", "multi-az-cluster"]),
            "scenario_type": scenario_type
        })

    # Now compute EXACT Net Compensable Outage Minutes by taking the UNION of compensable intervals
    # (Contract Rule: Overlapping outages across services do not double count aggregate monthly downtime minutes)
    raw_outage_intervals.sort(key=lambda x: (x[0], x[1]))
    merged_intervals: List[Tuple[int, int]] = []
    
    for start, end, _ in raw_outage_intervals:
        if start >= end:
            continue
        if not merged_intervals:
            merged_intervals.append((start, end))
        else:
            prev_start, prev_end = merged_intervals[-1]
            if start <= prev_end:
                merged_intervals[-1] = (prev_start, max(prev_end, end))
            else:
                merged_intervals.append((start, end))

    total_compensable_outage_minutes = sum(end - start for start, end in merged_intervals)

    # Effective Uptime Calculation
    # Uptime % = ((total_month_minutes - total_compensable_outage_minutes) / total_month_minutes) * 100.0
    effective_uptime_pct = ((total_month_minutes - total_compensable_outage_minutes) / total_month_minutes) * 100.0

    # Determine Applicable Credit Percentage from Tier Thresholds
    # Contract Rule: Exact boundary matching:
    # e.g., if min_uptime <= effective_uptime_pct < max_uptime
    credit_pct = 0
    for tier in tier_thresholds:
        if tier["min_uptime"] <= effective_uptime_pct < tier["max_uptime"]:
            credit_pct = tier["credit_pct"]
            break
    if effective_uptime_pct < tier_thresholds[-1]["min_uptime"]:
        credit_pct = tier_thresholds[-1]["credit_pct"]

    # Base charge to apply credit against: MRC only vs MRC + Variable
    applicable_base_charge_cents = mrc_cents
    if applies_to_variable:
        applicable_base_charge_cents = mrc_cents + variable_spend_cents

    # Calculate Gross Credit with Multiplier
    # Formula: round(applicable_base_charge_cents * (credit_pct / 100.0) * vip_multiplier)
    # Using integer arithmetic: (applicable_base_charge_cents * credit_pct * int(vip_multiplier * 100) + 5000) // 10000
    vip_multiplier_x100 = int(round(vip_multiplier * 100))
    gross_credit_cents = (applicable_base_charge_cents * credit_pct * vip_multiplier_x100 + 5000) // 10000

    # Monthly Cap Calculation
    max_cap_cents = (mrc_cents * cap_pct) // 100
    capped_credit_cents = min(gross_credit_cents, max_cap_cents)

    # Net Credit Payable after prior issued credits
    net_credit_cents = max(0, capped_credit_cents - prior_credits_cents)

    # Build Audit Trace for full human/verifier audibility
    audit_trace = {
        "case_id": case_id,
        "difficulty_tier": difficulty_tier,
        "contract_tier_type": contract_tier_type,
        "customer_has_multi_az": customer_has_multi_az,
        "total_month_minutes": total_month_minutes,
        "mrc_cents": mrc_cents,
        "variable_spend_cents": variable_spend_cents,
        "prior_credits_cents": prior_credits_cents,
        "raw_incident_count": len(incidents),
        "deductions_log": deductions_log,
        "merged_compensable_intervals": merged_intervals,
        "total_compensable_outage_minutes": total_compensable_outage_minutes,
        "effective_uptime_pct": round(effective_uptime_pct, 6),
        "credit_tier_selected_pct": credit_pct,
        "vip_multiplier": vip_multiplier,
        "gross_credit_cents": gross_credit_cents,
        "cap_pct": cap_pct,
        "max_cap_cents": max_cap_cents,
        "capped_credit_cents": capped_credit_cents,
        "final_net_credit_cents": net_credit_cents
    }

    # Generate Case Artifact Files
    # 1. contract.md
    contract_md = f"""# Master Cloud Services Agreement (MSA) & Service Level Schedule
**Customer ID:** CUST-{case_idx+1000:04d}  
**Contract Plan Tier:** `{contract_tier_type}`  
**Effective Date:** 2025-01-01  
**Governing Standard:** Master Cloud SLA Framework v4.2

---

## 1. Scope and Availability Targets
The Provider guarantees service availability during each calendar month measurement period.
- **Contracted Target Availability:** {target_availability:.2f}%
- **Measurement Base:** Calendar Month of 30 Days (43,200 Total Minutes).

## 2. Service Credit Schedule
If the Effective Monthly Uptime Percentage falls below the contracted target, the Customer is entitled to the following base service credit percentage:

| Effective Monthly Uptime Range | Base Service Credit (% of MRC) |
| :--- | :--- |
"""
    for tier in tier_thresholds:
        if tier["min_uptime"] == 0.0:
            contract_md += f"| Less than {tier['max_uptime']:.2f}% | {tier['credit_pct']}% |\n"
        else:
            contract_md += f"| {tier['min_uptime']:.2f}% to {tier['max_uptime']:.2f}% | {tier['credit_pct']}% |\n"

    contract_md += f"""
## 3. Maximum Monthly Credit Cap
- Total aggregate service credits in any single calendar billing month shall not exceed **{cap_pct}% of the Monthly Recurring Charge (MRC)**.
- Any interim service credits already issued or refunded during the active billing month must be credited against this final amount.

## 4. Special Riders & Addenda
"""
    if contract_tier_type == "MISSION_CRITICAL_VIP":
        contract_md += f"""- **Addendum VIP-1 (Mission Critical Acceleration):** A **1.50x Credit Multiplier** applies to the gross credit calculation, PROVIDED THAT Customer has active Multi-AZ / Multi-Region high availability architecture configured. If Customer operates Single-AZ, standard 1.00x multiplier applies.
- **Addendum VIP-2 (Variable Fee Ingestion):** Service credit percentage applies to the sum of Monthly Recurring Charge (MRC) AND Variable Usage Spend.
"""
    elif contract_tier_type == "HIGH_THROUGHPUT_FINTECH":
        contract_md += f"""- **Addendum FIN-1 (Fintech Performance Rider):** A **1.25x Credit Multiplier** applies to gross credit calculation if Multi-AZ is active (1.00x for Single-AZ).
- **Addendum FIN-2:** Credit applies strictly to Monthly Recurring Charge (MRC) only. Variable bursting charges are excluded.
"""
    else:
        contract_md += f"""- **Standard Terms:** No special multipliers apply (1.00x). Service credit applies strictly to Monthly Recurring Charge (MRC).
"""

    contract_md += """
## 5. Standard Framework Incorporation
All outage criteria, maintenance notification rules (72-hour notice window requirement), RCA fault allocation, Force Majeure RTO grace periods, and interval deduplication rules are governed strictly by `CONTRACT_FRAMEWORK.md`.
"""

    # 2. billing_statement.json
    billing_statement = {
        "invoice_id": f"INV-202604-{case_idx+1000:04d}",
        "customer_id": f"CUST-{case_idx+1000:04d}",
        "billing_period_start": "2026-04-01T00:00:00Z",
        "billing_period_end": "2026-04-30T23:59:59Z",
        "billing_period_days": 30,
        "total_period_minutes": 43200,
        "monthly_recurring_charge_cents": mrc_cents,
        "monthly_recurring_charge_usd": f"${mrc_cents / 100:,.2f}",
        "variable_usage_charge_cents": variable_spend_cents,
        "variable_usage_charge_usd": f"${variable_spend_cents / 100:,.2f}",
        "prior_credits_issued_cents": prior_credits_cents,
        "prior_credits_issued_usd": f"${prior_credits_cents / 100:,.2f}",
        "max_monthly_credit_cap_percent": cap_pct,
        "currency": "USD"
    }

    # 3. architecture_profile.json
    architecture_profile = {
        "customer_id": f"CUST-{case_idx+1000:04d}",
        "deployment_tier": contract_tier_type,
        "multi_az_enabled": customer_has_multi_az,
        "active_regions": ["us-east-1"] if not customer_has_multi_az else ["us-east-1", "us-east-2"],
        "availability_zones": ["us-east-1a"] if not customer_has_multi_az else ["us-east-1a", "us-east-1b"],
        "architecture_audit_notes": "Customer architecture verified by Technical Account Manager." if customer_has_multi_az else "Customer declined Multi-AZ redundant deployment option; operating in Single-AZ mode."
    }

    # 4. telemetry_events.json
    telemetry_events = {
        "case_id": case_id,
        "reporting_period": "2026-04",
        "incident_events": incidents
    }

    # Bundle all files
    case_files = {
        "contract.md": contract_md,
        "billing_statement.json": json.dumps(billing_statement, indent=2),
        "architecture_profile.json": json.dumps(architecture_profile, indent=2),
        "telemetry/telemetry_events.json": json.dumps(telemetry_events, indent=2),
    }

    # Add tickets, maintenance notices, and RCAs
    for ticket in tickets:
        ticket_id = ticket["ticket_id"]
        case_files[f"dossiers/tickets/{ticket_id}.json"] = json.dumps(ticket, indent=2)

    for notice in maintenance_notices:
        notice_id = notice["notice_id"]
        case_files[f"dossiers/maintenance/{notice_id}.json"] = json.dumps(notice, indent=2)

    for rca in rca_reports:
        rca_id = rca["rca_id"]
        case_files[f"dossiers/rca/{rca_id}.json"] = json.dumps(rca, indent=2)

    # Item metadata for solver manifest / items_private_sample.jsonl
    item_meta = {
        "id": case_id,
        "case_directory": f"cases/{case_id}",
        "contract_file": f"cases/{case_id}/contract.md",
        "billing_file": f"cases/{case_id}/billing_statement.json",
        "architecture_file": f"cases/{case_id}/architecture_profile.json",
        "telemetry_file": f"cases/{case_id}/telemetry/telemetry_events.json",
        "dossiers_directory": f"cases/{case_id}/dossiers",
        "question": f"Perform a comprehensive forensic SLA adjudication for {case_id} for the April 2026 billing cycle. Compute the exact final Net Approved Service Credit (in integer USD cents) payable to the customer account after applying all outage qualification criteria, scheduled maintenance notice exemptions, RCA fault deductions, force majeure RTO grace periods, interval deduplications, tier percentages, addendum multipliers, monthly caps, and prior credits. Return answer as an integer amount in USD cents (e.g. 185000 for $1,850.00)."
    }

    return item_meta, case_files, net_credit_cents, audit_trace


def build_contract_framework_md() -> str:
    """Returns the comprehensive public master contract framework document."""
    return """# Master Cloud SLA Legal & Mathematical Framework (v4.2)
**Publication Reference:** CloudSLA-Standard-2026.4  
**Applicability:** Universal adjudication standard for all Cloud Infrastructure SLA arbitration cases.

---

## 1. Core Principles & Definitions
This document sets forth the authoritative, unambiguous mathematical and procedural rules for calculating service credit entitlements under Cloud Services Master Agreements.

### 1.1 Measurement Period
- All evaluations are conducted over a standard monthly billing period.
- For a 30-day billing month (e.g. April 2026), the Total Available Period is:
  $$\\text{Total Period Minutes } (M_{\\text{total}}) = 30 \\times 24 \\times 60 = 43,200 \\text{ minutes}$$

### 1.2 Outage Qualification Criteria
An incident event qualifies as an **Unscheduled Outage Event** if and only if:
1. The observed API error rate is $\\ge 5.0\\%$ or service is entirely unavailable. Incidents with error rate $< 5.0\\%$ are classified as non-breaching telemetry fluctuations and accrue **0 minutes** of compensable downtime.
2. The event is not fully excused by the exclusions set forth in Section 2.

---

## 2. Exclusions and Deductions from Outage Time

### 2.1 Scheduled Maintenance Windows
- **Timely Notice Rule:** Maintenance is exempt from downtime calculations **IF AND ONLY IF** formal written notice was transmitted $\\ge 72$ hours prior to the scheduled window start timestamp (`notice_sent_at` $\\le$ `target_window_start` $- 72\\text{h}$).
- **Tardy Notice Penalty:** If notice was sent $< 72$ hours prior, the notice is invalid, and **100% of the maintenance duration counts as unscheduled outage**.
- **Overrun Rule:** For timely notices, the scheduled window is exempt. However, any time elapsed beyond the scheduled window duration is an **Unscheduled Maintenance Overrun** and is fully compensable.

### 2.2 Customer-Attributable Fault (RCA Allocation)
- When an official Root Cause Analysis (RCA) determines that a portion of an incident was caused by Customer misconfiguration, malformed scripts, or unannounced load spikes, that specific customer-attributable duration ($M_{\\text{cust}}$) is deducted from the incident duration:
  $$M_{\\text{compensable}} = M_{\\text{gross}} - M_{\\text{cust}}$$

### 2.3 Force Majeure & Third-Party Transit Cuts (RTO Grace Period)
- For documented Force Majeure events (e.g. Tier-1 transit carrier metro fiber cuts, utility grid power loss), the Provider is granted an **RTO Grace Period of 30 minutes**.
- If total event duration is $\\le 30$ minutes, compensable downtime is **0**.
- If total event duration exceeds 30 minutes, compensable downtime equals the excess duration:
  $$M_{\\text{compensable}} = M_{\\text{gross}} - 30$$

---

## 3. Incident Deduplication (Union of Outage Intervals)
- In multi-service or multi-incident deployments, outages across different services (or multiple concurrent incidents) during overlapping timestamps **must not be double-counted**.
- The Total Compensable Outage Minutes ($M_{\\text{outage}}$) is the exact measure of the **union of all compensable intervals**:
  $$M_{\\text{outage}} = \\left| \\bigcup_{i} [\\text{start}_i, \\text{end}_i] \\right|$$

---

## 4. Uptime Percentage Calculation
The Effective Monthly Uptime Percentage ($U$) is calculated as:
$$U = \\frac{M_{\\text{total}} - M_{\\text{outage}}}{M_{\\text{total}}} \\times 100.0$$

---

## 5. Credit Schedule & Financial Adjudication

### 5.1 Base Credit Tier Lookup
Evaluate $U$ against the Contract Schedule table:
- Match the tier where $\\text{min\\_uptime} \\le U < \\text{max\\_uptime}$.
- If $U \\ge \\text{Contract Target}$, Base Credit Percentage $C = 0\\%$.

### 5.2 Addenda Multipliers & Eligibility
- If the Contract includes an Addendum with a VIP Multiplier ($M_{\\text{vip}}$):
  - Check whether Customer satisfies the architectural prerequisite (e.g. `multi_az_enabled == true`).
  - If satisfied, apply $M_{\\text{vip}}$ (e.g. 1.50x or 1.25x).
  - If prerequisite is not satisfied (e.g. Single-AZ deployment), $M_{\\text{vip}} = 1.00$.

### 5.3 Applicable Base Charge
- **Standard Contracts:** Credit applies to Monthly Recurring Charge (MRC) only.
- **Variable Spend Addendum (e.g. VIP-2):** Credit applies to $\\text{MRC} + \\text{Variable Usage Charge}$.

### 5.4 Gross Credit Calculation
$$\\text{Credit}_{\\text{gross}} = \\text{round}\\left( \\text{Applicable Base Charge} \\times \\frac{C}{100} \\times M_{\\text{vip}} \\right)$$
*(Standard rounding to nearest integer cent: half-way values round up).*

### 5.5 Monthly Cap and Prior Issued Credits
1. **Apply Cap:**
   $$\\text{Credit}_{\\text{capped}} = \\min\\left( \\text{Credit}_{\\text{gross}}, \\text{MRC} \\times \\frac{\\text{Max Cap \\%}}{100} \\right)$$
2. **Subtract Prior Credits:**
   $$\\text{Credit}_{\\text{net}} = \\max\\left( 0, \\text{Credit}_{\\text{capped}} - \\text{Prior Credits Issued} \\right)$$

The final result $\\text{Credit}_{\\text{net}}$ is the exact integer USD cents payable.
"""


def main():
    parser = argparse.ArgumentParser(description="CloudSLA-Forensics Generator")
    parser.add_argument("--sample-count", type=int, default=30, help="Number of items to generate")
    parser.add_argument("--seed", type=int, default=20260516, help="Random seed")
    parser.add_argument("--out-dir", type=str, default=".", help="Output directory")
    args = parser.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    solver_bundle_dir = os.path.join(out_dir, "solver_bundle")
    cases_dir = os.path.join(solver_bundle_dir, "cases")

    # Clean existing generated structures if any
    if os.path.exists(solver_bundle_dir):
        shutil.rmtree(solver_bundle_dir)
    os.makedirs(cases_dir, exist_ok=True)

    items_list = []
    gold_list = []
    audit_traces = []

    # Write Master Contract Framework into solver_bundle
    contract_framework_content = build_contract_framework_md()
    with open(os.path.join(solver_bundle_dir, "CONTRACT_FRAMEWORK.md"), "w", encoding="utf-8") as f:
        f.write(contract_framework_content)

    # Generate each case
    for i in range(args.sample_count):
        item_meta, case_files, gold_cents, audit_trace = generate_case_data(i, args.seed)
        items_list.append(item_meta)
        gold_list.append({"id": item_meta["id"], "answer": gold_cents})
        audit_traces.append(audit_trace)

        # Write case files
        case_dir = os.path.join(solver_bundle_dir, item_meta["case_directory"])
        os.makedirs(case_dir, exist_ok=True)

        for rel_path, file_content in case_files.items():
            full_path = os.path.join(case_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_content)

    # Write solver_bundle/items_private_sample.jsonl
    items_path = os.path.join(solver_bundle_dir, "items_private_sample.jsonl")
    with open(items_path, "w", encoding="utf-8") as f:
        for item in items_list:
            f.write(json.dumps(item) + "\n")

    # Write solver_bundle/SOLVER_MANIFEST.json
    manifest = {
        "benchmark_name": "CloudSLA-Forensics",
        "version": "1.0.0",
        "description": "Forensic enterprise cloud SLA breach and service credit arbitration benchmark.",
        "item_count": len(items_list),
        "items_file": "items_private_sample.jsonl",
        "contract_framework": "CONTRACT_FRAMEWORK.md",
        "cases_directory": "cases",
        "answer_schema": {
            "type": "integer",
            "description": "Exact Net Approved Service Credit payable in USD cents (e.g. 185000 for $1,850.00)."
        }
    }
    with open(os.path.join(solver_bundle_dir, "SOLVER_MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Write solver_bundle/README.md and solver_bundle/solver_packet.md
    solver_readme = """# CloudSLA-Forensics Solver Packet

## Benchmark Overview
CloudSLA-Forensics evaluates an agent's capability to perform forensic financial and technical arbitration on complex enterprise cloud Service Level Agreement (SLA) claims.

For each case, you are provided with:
1. `contract.md`: The governing Master Service Agreement, Availability Target, Tier Credit Schedule, and custom Addenda.
2. `billing_statement.json`: The monthly billing summary with Monthly Recurring Charges (MRC), variable charges, prior issued credits, and maximum credit cap.
3. `architecture_profile.json`: Deployment details (e.g. Multi-AZ vs Single-AZ status).
4. `telemetry/telemetry_events.json`: Telemetry logs of detected incident events.
5. `dossiers/`: Incident support tickets, Root Cause Analysis (RCA) reports, and maintenance window notices.

All rules, notice deadlines, RCA fault allocations, force majeure RTO grace periods, interval deduplications, tier math, and cap deductions are strictly governed by `CONTRACT_FRAMEWORK.md`.

## Task Instructions
For each case in `items_private_sample.jsonl`:
1. Read the contract terms and incident dossiers.
2. Calculate the exact Net Approved Service Credit (in integer USD cents) payable to the customer.
3. Format predictions as a JSON Lines file where each line has `{"id": "<case_id>", "answer": <integer_cents>}`.
"""
    with open(os.path.join(solver_bundle_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(solver_readme)
    with open(os.path.join(solver_bundle_dir, "solver_packet.md"), "w", encoding="utf-8") as f:
        f.write(solver_readme)

    # Write root gold_private_sample.jsonl
    gold_path = os.path.join(out_dir, "gold_private_sample.jsonl")
    with open(gold_path, "w", encoding="utf-8") as f:
        for gold_item in gold_list:
            f.write(json.dumps(gold_item) + "\n")

    print(f"Successfully generated {len(items_list)} items.")
    print(f"Solver bundle written to: {solver_bundle_dir}")
    print(f"Gold answers written to: {gold_path}")


if __name__ == "__main__":
    main()
