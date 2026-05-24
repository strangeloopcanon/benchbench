import argparse
import json
import os
import random
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


UTC = timezone.utc


def _mkdir_clean(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _dt_iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso_any(s: str) -> datetime:
    # All generated timestamps are ISO-8601 with explicit offset or Z.
    if s.endswith("Z"):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    # Example: 2026-04-12T02:15:00-07:00
    return datetime.fromisoformat(s)


def _minutes_ceil(seconds: float) -> int:
    if seconds <= 0:
        return 0
    return int((seconds + 60 - 1) // 60)


@dataclass(frozen=True)
class ItemConfig:
    item_id: str
    monthly_fee_cents: int
    tier: str  # "STANDARD" | "BUSINESS" | "ENTERPRISE"
    credit_cap_percent: int  # max credit percent per month (contract rider)
    region_scope: str  # "single" | "multi"
    tz_hint: str  # e.g. "America/Los_Angeles (UTC-07:00 during this incident)"
    clock_drift_seconds: int  # monitoring timestamps are off by this many seconds
    maintenance_windows_utc: List[Tuple[datetime, datetime]]
    incidents: List[Dict[str, Any]]


def _tier_sla_threshold_minutes(tier: str) -> int:
    # Public policy: monthly SLA breach threshold (eligible downtime minutes).
    # These are intentionally not "9s math"; they are explicit finite thresholds.
    if tier == "STANDARD":
        return 40
    if tier == "BUSINESS":
        return 20
    if tier == "ENTERPRISE":
        return 10
    raise ValueError(f"unknown tier: {tier}")


def _tier_credit_table(tier: str) -> List[Tuple[int, int]]:
    # Public policy: if eligible downtime >= threshold, credits are:
    # (minutes_at_or_above, credit_percent)
    if tier == "STANDARD":
        return [(40, 10), (80, 25), (160, 50)]
    if tier == "BUSINESS":
        return [(20, 10), (40, 25), (80, 50)]
    if tier == "ENTERPRISE":
        return [(10, 10), (20, 25), (40, 50)]
    raise ValueError(f"unknown tier: {tier}")


def _credit_percent_for_minutes(tier: str, eligible_minutes: int) -> int:
    table = _tier_credit_table(tier)
    pct = 0
    for m, p in table:
        if eligible_minutes >= m:
            pct = max(pct, p)
    return pct


def _apply_exclusions(
    downtime_intervals_utc: List[Tuple[datetime, datetime]],
    maintenance_windows_utc: List[Tuple[datetime, datetime]],
    contract_exclusions_utc: List[Tuple[datetime, datetime]],
) -> List[Tuple[datetime, datetime]]:
    # Subtract exclusions from downtime intervals. All times are UTC.
    exclusions = maintenance_windows_utc + contract_exclusions_utc

    def subtract_interval(interval: Tuple[datetime, datetime], exc: Tuple[datetime, datetime]) -> List[Tuple[datetime, datetime]]:
        a0, a1 = interval
        b0, b1 = exc
        if b1 <= a0 or b0 >= a1:
            return [interval]
        out: List[Tuple[datetime, datetime]] = []
        if b0 > a0:
            out.append((a0, min(b0, a1)))
        if b1 < a1:
            out.append((max(b1, a0), a1))
        return [x for x in out if x[1] > x[0]]

    remaining = downtime_intervals_utc[:]
    for exc in exclusions:
        next_remaining: List[Tuple[datetime, datetime]] = []
        for interval in remaining:
            next_remaining.extend(subtract_interval(interval, exc))
        remaining = next_remaining
        if not remaining:
            break

    # Merge any overlapping/adjacent intervals after subtraction.
    remaining.sort(key=lambda x: x[0])
    merged: List[Tuple[datetime, datetime]] = []
    for s, e in remaining:
        if not merged:
            merged.append((s, e))
            continue
        ps, pe = merged[-1]
        if s <= pe:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def _eligible_minutes_from_intervals(intervals_utc: List[Tuple[datetime, datetime]]) -> int:
    # Public policy: sum durations, then round up to whole minutes per *interval*,
    # then sum (this punishes splitting; makes drift fixes matter).
    total = 0
    for s, e in intervals_utc:
        total += _minutes_ceil((e - s).total_seconds())
    return total


def _make_public_policy_text() -> str:
    return (
        "# NimbusCloud Service Credit Policy (Public)\n\n"
        "This policy defines how to compute eligible downtime and service credits.\n\n"
        "## 1) What counts as downtime\n\n"
        "A downtime interval is any contiguous period where the service is either:\n"
        "- **UNAVAILABLE** (requests fail), or\n"
        "- **SEVERE_DEGRADED** (p95 latency exceeds the contract threshold).\n\n"
        "Periods that are only **DEGRADED** (but not severe) do *not* count.\n\n"
        "### Deriving state from monitoring evidence\n\n"
        "Monitoring logs may contain either explicit `STATE` records or `METRIC` records.\n"
        "If explicit `STATE` records exist, you may use them.\n"
        "If you only have metrics, derive state per region using the contract rider parameters:\n"
        "- `unavailable_error_rate_pct`: if `error_rate_pct >= unavailable_error_rate_pct`, state is UNAVAILABLE.\n"
        "- `severe_p95_ms`: if `p95_ms >= severe_p95_ms` AND `error_rate_pct >= 10`, state is SEVERE_DEGRADED.\n"
        "- Else if `p95_ms >= severe_p95_ms/2`, state is DEGRADED.\n"
        "- Else state is OK.\n\n"
        "## 2) Evidence precedence\n\n"
        "Use the following precedence if sources disagree:\n"
        "1. Internal incident timeline **when it provides explicit start/end timestamps** (and includes a correction note)\n"
        "2. Monitoring log events (after applying clock drift correction)\n"
        "3. Status page updates\n"
        "4. Customer email thread\n\n"
        "If the internal timeline is missing an explicit boundary (for example it says \"use monitoring for exact end\"),\n"
        "then the monitoring log defines the missing boundary.\n\n"
        "## 3) Clock drift correction (monitoring logs)\n\n"
        "Monitoring logs may have a consistent clock drift. If a drift value is provided\n"
        "in the item, *shift every monitoring timestamp by that drift* before using it.\n\n"
        "## 4) Exclusions\n\n"
        "Exclude time that falls within any of:\n"
        "- Published maintenance windows (global policy asset for the item)\n"
        "- Contract rider exclusions (customer-specific)\n\n"
        "Exclusions subtract from downtime even if the service was unavailable.\n\n"
        "## 5) Aggregation and rounding\n\n"
        "Compute downtime as a set of UTC intervals. After applying exclusions:\n"
        "- Merge overlapping/adjacent downtime intervals.\n"
        "- Round **each remaining interval up to whole minutes**.\n"
        "- Sum those rounded minutes to get `eligible_downtime_minutes`.\n\n"
        "## 6) Multi-region scope\n\n"
        "If the contract scope is `multi`, downtime is the union across regions.\n"
        "If the scope is `single`, use only the named region in the contract.\n\n"
        "## 7) SLA breach and credit table\n\n"
        "SLA breach is `eligible_downtime_minutes` >= the tier threshold:\n"
        "- STANDARD: 40 minutes\n"
        "- BUSINESS: 20 minutes\n"
        "- ENTERPRISE: 10 minutes\n\n"
        "Credit percent is determined from eligible minutes (take the highest matching tier band):\n"
        "- STANDARD: >=40 => 10%, >=80 => 25%, >=160 => 50%\n"
        "- BUSINESS: >=20 => 10%, >=40 => 25%, >=80 => 50%\n"
        "- ENTERPRISE: >=10 => 10%, >=20 => 25%, >=40 => 50%\n\n"
        "Apply the customer contract cap: `credit_percent = min(credit_percent, cap_percent)`.\n\n"
        "## 8) Credit calculation\n\n"
        "`credit_usd_cents = floor(monthly_fee_cents * credit_percent / 100)`.\n"
    )


def _make_item_contract_text(cfg: ItemConfig, region: str, contract_exclusions_utc: List[Tuple[datetime, datetime]]) -> str:
    # These per-contract thresholds are public and must be used to interpret monitoring metrics.
    severe_p95_ms = 1200 if cfg.tier == "STANDARD" else (900 if cfg.tier == "BUSINESS" else 700)
    unavailable_error_rate_pct = 80 if cfg.tier != "ENTERPRISE" else 60

    lines = [
        "# Customer Contract Rider (Public)\n",
        f"- Customer tier: **{cfg.tier}**",
        f"- Monthly fee: **${cfg.monthly_fee_cents/100:.2f}** (={cfg.monthly_fee_cents} cents)",
        f"- Scope: **{cfg.region_scope}**",
        f"- Primary region (if scope=single): **{region}**",
        f"- Credit cap (percent): **{cfg.credit_cap_percent}%**\n",
        "## Monitoring interpretation parameters\n",
        f"- severe_p95_ms: **{severe_p95_ms}**",
        f"- unavailable_error_rate_pct: **{unavailable_error_rate_pct}**\n",
        "## Contract exclusions (UTC)\n",
    ]
    if not contract_exclusions_utc:
        lines.append("- (none)\n")
    else:
        for s, e in contract_exclusions_utc:
            lines.append(f"- { _dt_iso_z(s) } to { _dt_iso_z(e) }")
        lines.append("")
    lines.append("## Notes\n- All timestamps in evidence may be in UTC or a local offset; treat ISO offsets as authoritative.\n")
    return "\n".join(lines).strip() + "\n"


def _make_maintenance_text(windows_utc: List[Tuple[datetime, datetime]]) -> str:
    out = ["# Published Maintenance Windows (Public)\n"]
    if not windows_utc:
        out.append("- (none)\n")
    else:
        for s, e in windows_utc:
            out.append(f"- { _dt_iso_z(s) } to { _dt_iso_z(e) }")
        out.append("")
    out.append("Notes: Maintenance windows always exclude downtime.\n")
    return "\n".join(out)


def _make_monitoring_log_text(
    region_events: List[Tuple[str, datetime, str, Dict[str, Any]]],
    tz_hint: str,
    drift_seconds: int,
) -> str:
    # Region events are (region, timestamp_true_utc, kind, payload).
    # kind is "STATE" or "METRIC". Payload shape is specified in the solver packet.
    # The emitted log shows drifted times in a mix of UTC and local offsets.
    header = [
        "# Monitoring Log Export (Public)\n",
        f"tz_hint: {tz_hint}",
        f"clock_drift_seconds: {drift_seconds}",
        "",
        "Format variants (one per line):",
        "1) <timestamp> <region> STATE <state>",
        "2) <timestamp> <region> METRIC {\"p95_ms\": <int>, \"error_rate_pct\": <int>}",
        "",
        "States: OK | DEGRADED | SEVERE_DEGRADED | UNAVAILABLE",
        "",
    ]
    lines = []
    for region, ts_true_utc, kind, payload in region_events:
        ts_drifted = ts_true_utc + timedelta(seconds=drift_seconds)
        # Mix representations to punish naive parsing (still ISO-8601).
        if (ts_true_utc.minute % 2) == 0:
            stamp = _dt_iso_z(ts_drifted)
        else:
            # Example offset -07:00
            offset = timezone(timedelta(hours=-7))
            stamp = ts_drifted.astimezone(offset).isoformat(timespec="seconds")
        if kind == "STATE":
            lines.append(f"{stamp} {region} STATE {payload['state']}")
        elif kind == "METRIC":
            # Occasionally emit as loose key=val text (still machine-readable but annoyingly non-JSON).
            if payload.get("_format") == "kv":
                lines.append(f"{stamp} {region} METRIC p95_ms={payload['p95_ms']} error_rate_pct={payload['error_rate_pct']}")
            else:
                lines.append(f"{stamp} {region} METRIC {json.dumps({'p95_ms': payload['p95_ms'], 'error_rate_pct': payload['error_rate_pct']})}")
        else:
            raise ValueError(f"unknown monitoring kind: {kind}")
    return "\n".join(header + lines).strip() + "\n"


def _make_status_page_text(updates: List[Tuple[datetime, str]]) -> str:
    out = [
        "# Status Page Updates (Public)\n",
        "Notes: times are as-posted; some posts are delayed relative to real events.\n",
        "Format: <timestamp_utc> - <message>\n",
    ]
    for ts, msg in updates:
        out.append(f"{_dt_iso_z(ts)} - {msg}")
    out.append("")
    return "\n".join(out)


def _make_email_thread_text(messages: List[Tuple[str, datetime, str]]) -> str:
    # messages: (from, timestamp, body)
    out = ["From: support@nimbuscloud.example", "Subject: Incident follow-up", ""]
    for frm, ts, body in messages:
        out.append(f"---\nFrom: {frm}\nDate: {_dt_iso_z(ts)}\n\n{body}\n")
    return "\n".join(out).strip() + "\n"


def _make_internal_timeline_text(entries: List[Tuple[datetime, str]], correction_note: str) -> str:
    out = [
        "# Internal Incident Timeline (Public excerpt)\n",
        "This excerpt is considered higher-precedence if it includes a correction note.\n",
        "",
        f"Correction note: {correction_note}",
        "",
        "Format: <timestamp_utc> - <event>\n",
    ]
    for ts, ev in entries:
        out.append(f"{_dt_iso_z(ts)} - {ev}")
    out.append("")
    return "\n".join(out)


def _gen_item(rng: random.Random, idx: int) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    item_id = f"scf_{idx:03d}"

    tier = rng.choice(["STANDARD", "BUSINESS", "ENTERPRISE"])
    monthly_fee_cents = rng.choice([49900, 99900, 149900, 249900, 399900])  # $499..$3999
    credit_cap_percent = rng.choice([10, 25, 50])
    region_scope = rng.choice(["single", "multi"])
    region = rng.choice(["us-west", "us-east", "eu-central"])

    # Make 1-3 contract exclusions and 0-2 maintenance windows, all within a 3-day band.
    base = datetime(2026, rng.randint(1, 4), rng.randint(1, 28), rng.randint(0, 23), rng.choice([0, 15, 30, 45]), tzinfo=UTC)
    maintenance_windows: List[Tuple[datetime, datetime]] = []
    for _ in range(rng.randint(0, 2)):
        s = base + timedelta(hours=rng.randint(0, 24), minutes=rng.randint(0, 30))
        e = s + timedelta(minutes=rng.choice([15, 30, 45, 60]))
        maintenance_windows.append((s, e))
    maintenance_windows.sort(key=lambda x: x[0])

    contract_exclusions: List[Tuple[datetime, datetime]] = []
    for _ in range(rng.randint(1, 3)):
        s = base + timedelta(hours=rng.randint(0, 48), minutes=rng.choice([0, 10, 20, 30, 40, 50]))
        e = s + timedelta(minutes=rng.choice([10, 15, 20, 25, 30, 40]))
        contract_exclusions.append((s, e))
    contract_exclusions.sort(key=lambda x: x[0])

    tz_hint = "America/Los_Angeles (UTC-07:00 during this incident)"
    drift = rng.choice([-120, -60, -30, 0, 45, 90, 180])

    # Generate 2-4 incidents. Each incident creates monitoring state changes; only
    # UNAVAILABLE and SEVERE_DEGRADED count as downtime.
    region_set = [region] if region_scope == "single" else ["us-west", "us-east", "eu-central"]
    incidents: List[Dict[str, Any]] = []
    region_events: List[Tuple[str, datetime, str, Dict[str, Any]]] = []

    for inc_i in range(rng.randint(2, 4)):
        start = base + timedelta(hours=rng.randint(0, 48), minutes=rng.randint(0, 50))
        duration_min = rng.choice([6, 8, 12, 16, 21, 27, 33, 39, 44, 53])
        end = start + timedelta(minutes=duration_min, seconds=rng.randint(0, 50))
        # Incidents have a ramp: DEGRADED -> (maybe) SEVERE_DEGRADED/UNAVAILABLE -> OK.
        kind = rng.choice(["UNAVAILABLE", "SEVERE_DEGRADED"])
        ramp = start + timedelta(minutes=rng.choice([1, 2, 3]), seconds=rng.randint(0, 40))
        settle = end - timedelta(minutes=rng.choice([1, 2, 3]), seconds=rng.randint(0, 40))
        if settle <= ramp:
            settle = ramp + timedelta(minutes=1)

        # Some incidents only affect a subset of regions for multi scope.
        affected = region_set
        if region_scope == "multi" and rng.random() < 0.35:
            affected = rng.sample(region_set, k=rng.choice([1, 2]))

        for r in region_set:
            # Emit state transitions for each region.
            # Use a mixture of explicit STATE and METRIC records to force per-item interpretation.
            # Even when we emit STATE, the monitoring log still requires drift correction and exclusions.
            use_metrics = rng.random() < 0.6
            if use_metrics:
                region_events.append((r, start, "METRIC", {"p95_ms": rng.randint(200, 700), "error_rate_pct": rng.randint(0, 8), "_format": "json"}))
                if r in affected:
                    region_events.append((r, ramp, "METRIC", {"p95_ms": rng.randint(900, 1800), "error_rate_pct": rng.randint(10, 95), "_format": rng.choice(["json", "kv"])}))
                    region_events.append((r, settle, "METRIC", {"p95_ms": rng.randint(500, 1200), "error_rate_pct": rng.randint(0, 15), "_format": rng.choice(["json", "kv"])}))
                else:
                    region_events.append((r, ramp, "METRIC", {"p95_ms": rng.randint(200, 600), "error_rate_pct": rng.randint(0, 6), "_format": rng.choice(["json", "kv"])}))
                    region_events.append((r, settle, "METRIC", {"p95_ms": rng.randint(200, 600), "error_rate_pct": rng.randint(0, 6), "_format": rng.choice(["json", "kv"])}))
                region_events.append((r, end, "METRIC", {"p95_ms": rng.randint(200, 600), "error_rate_pct": rng.randint(0, 5), "_format": rng.choice(["json", "kv"])}))
            else:
                region_events.append((r, start, "STATE", {"state": "DEGRADED" if r in affected else "OK"}))
                region_events.append((r, ramp, "STATE", {"state": kind if r in affected else "OK"}))
                region_events.append((r, settle, "STATE", {"state": "DEGRADED" if r in affected else "OK"}))
                region_events.append((r, end, "STATE", {"state": "OK"}))

        # Gold is derived from monitoring (after drift), not from this coarse envelope.

        incidents.append(
            {
                "start_utc": _dt_iso_z(start),
                "end_utc": _dt_iso_z(end),
                "type": kind,
                "affected_regions": affected,
            }
        )

    # Add noise events that should not count as downtime.
    for _ in range(rng.randint(2, 4)):
        t0 = base + timedelta(hours=rng.randint(0, 48), minutes=rng.randint(0, 59))
        r = rng.choice(region_set)
        region_events.append((r, t0, "METRIC", {"p95_ms": rng.randint(250, 650), "error_rate_pct": rng.randint(0, 9), "_format": rng.choice(["json", "kv"])}))

    region_events.sort(key=lambda x: (x[1], x[0]))

    # Contract thresholds for deriving downtime from metrics.
    severe_p95_ms = 1200 if tier == "STANDARD" else (900 if tier == "BUSINESS" else 700)
    unavailable_error_rate_pct = 80 if tier != "ENTERPRISE" else 60

    # Gold computation:
    # - Parse monitoring events after drift correction to determine per-region downtime
    #   where state in {UNAVAILABLE, SEVERE_DEGRADED}.
    # - Union across regions depending on scope.
    # - Subtract exclusions, then merge and round per interval.
    def derive_state_from_metric(p95_ms: int, error_rate_pct: int) -> str:
        if error_rate_pct >= unavailable_error_rate_pct:
            return "UNAVAILABLE"
        if (p95_ms >= severe_p95_ms) and (error_rate_pct >= 10):
            return "SEVERE_DEGRADED"
        if p95_ms >= (severe_p95_ms // 2):
            return "DEGRADED"
        return "OK"

    # Build per-region state change events (true UTC) from a mix of STATE/METRIC records.
    per_region_events: Dict[str, List[Tuple[datetime, str]]] = {}
    for r, ts_true, kind, payload in region_events:
        if kind == "STATE":
            st = payload["state"]
        else:
            st = derive_state_from_metric(int(payload["p95_ms"]), int(payload["error_rate_pct"]))
        per_region_events.setdefault(r, []).append((ts_true, st))
    for r in per_region_events:
        per_region_events[r].sort(key=lambda x: x[0])

    def intervals_for_region(r: str) -> List[Tuple[datetime, datetime]]:
        evs = per_region_events.get(r, [])
        out: List[Tuple[datetime, datetime]] = []
        cur_state = "OK"
        cur_start: datetime | None = None
        for ts, st in evs:
            if cur_state in {"UNAVAILABLE", "SEVERE_DEGRADED"} and st not in {"UNAVAILABLE", "SEVERE_DEGRADED"}:
                if cur_start is not None and ts > cur_start:
                    out.append((cur_start, ts))
                cur_start = None
            elif cur_state not in {"UNAVAILABLE", "SEVERE_DEGRADED"} and st in {"UNAVAILABLE", "SEVERE_DEGRADED"}:
                cur_start = ts
            cur_state = st
        return out

    if region_scope == "single":
        raw_intervals = intervals_for_region(region)
    else:
        raw_intervals = []
        for r in region_set:
            raw_intervals.extend(intervals_for_region(r))

    raw_intervals.sort(key=lambda x: x[0])
    eligible_intervals = _apply_exclusions(raw_intervals, maintenance_windows, contract_exclusions)
    eligible_minutes = _eligible_minutes_from_intervals(eligible_intervals)

    tier_threshold = _tier_sla_threshold_minutes(tier)
    breached = eligible_minutes >= tier_threshold
    credit_pct_base = _credit_percent_for_minutes(tier, eligible_minutes)
    credit_pct = min(credit_pct_base, credit_cap_percent)
    credit_cents = (monthly_fee_cents * credit_pct) // 100

    gold_answer = {
        "eligible_downtime_minutes": eligible_minutes,
        "sla_breached": bool(breached),
        "credit_percent": int(credit_pct),
        "credit_usd_cents": int(credit_cents),
    }

    # Build solver-visible evidence files.
    # Monitoring log includes drifted times; internal timeline is partial: some incidents
    # have exact boundaries, some explicitly defer to monitoring for the exact end.
    status_updates: List[Tuple[datetime, str]] = []
    internal_entries: List[Tuple[datetime, str]] = []
    email_msgs: List[Tuple[str, datetime, str]] = []

    for inc in incidents:
        s = _parse_iso_any(inc["start_utc"])
        e = _parse_iso_any(inc["end_utc"])
        internal_entries.append((s, f"Incident start noted ({inc['type']})"))
        if rng.random() < 0.55:
            internal_entries.append((e, "Incident resolved; service OK"))
        else:
            # Provide a slightly off end time and a note to defer to monitoring.
            off = e + timedelta(seconds=rng.choice([-90, -60, 60, 120]))
            internal_entries.append((off, "Incident end estimate; use monitoring log for exact end"))
        # Status page is delayed/noisy:
        status_updates.append((s + timedelta(minutes=rng.randint(1, 6)), "Investigating elevated errors in some regions."))
        status_updates.append((e + timedelta(minutes=rng.randint(1, 8)), "Monitoring: mitigation applied; service recovering."))

    # Email thread: may include a wrong local-time estimate; solver should not trust it over higher precedence.
    email_base = base + timedelta(hours=60)
    email_msgs.append(("customer@acme.example", email_base, "Can you confirm whether we qualify for service credits this month?"))
    email_msgs.append(
        (
            "support@nimbuscloud.example",
            email_base + timedelta(minutes=30),
            "We will review monitoring and the incident timeline. Note: posted status times can be delayed.",
        )
    )
    if incidents:
        s0 = _parse_iso_any(incidents[0]["start_utc"])
        e0 = _parse_iso_any(incidents[0]["end_utc"])
        email_msgs.append(
            (
                "support@nimbuscloud.example",
                email_base + timedelta(hours=2),
                f"Initial estimate (may be revised): outage lasted about {(e0 - s0).seconds//60} minutes.",
            )
        )

    correction_note = "Timeline timestamps are UTC and reflect the corrected incident bridge notes."

    # Item JSON points to the evidence files relative to solver_bundle.
    item_public = {
        "id": item_id,
        "task": (
            "Using ONLY the public policy and evidence in this solver bundle, compute the exact answer JSON with keys "
            "`eligible_downtime_minutes`, `sla_breached`, `credit_percent`, `credit_usd_cents`."
        ),
        "assets": {
            "policy": "assets/public_policy.md",
            "contract_rider": f"items/{item_id}/contract_rider.md",
            "maintenance_windows": f"items/{item_id}/maintenance_windows.md",
            "monitoring_log": f"items/{item_id}/monitoring_log.txt",
            "internal_timeline": f"items/{item_id}/internal_timeline.md",
            "status_page": f"items/{item_id}/status_page.md",
            "email_thread": f"items/{item_id}/email_thread.eml",
        },
    }

    item_private_trace = {
        "id": item_id,
        "generator_debug": {
            "tier": tier,
            "monthly_fee_cents": monthly_fee_cents,
            "credit_cap_percent": credit_cap_percent,
            "region_scope": region_scope,
            "primary_region": region,
            "clock_drift_seconds": drift,
            "maintenance_windows_utc": [(_dt_iso_z(s), _dt_iso_z(e)) for s, e in maintenance_windows],
            "contract_exclusions_utc": [(_dt_iso_z(s), _dt_iso_z(e)) for s, e in contract_exclusions],
            "incidents": incidents,
            "eligible_intervals_utc": [(_dt_iso_z(s), _dt_iso_z(e)) for s, e in eligible_intervals],
        },
    }

    item_assets = {
        "policy_text": _make_public_policy_text(),
        "contract_text": _make_item_contract_text(
            ItemConfig(
                item_id=item_id,
                monthly_fee_cents=monthly_fee_cents,
                tier=tier,
                credit_cap_percent=credit_cap_percent,
                region_scope=region_scope,
                tz_hint=tz_hint,
                clock_drift_seconds=drift,
                maintenance_windows_utc=maintenance_windows,
                incidents=incidents,
            ),
            region=region,
            contract_exclusions_utc=contract_exclusions,
        ),
        "maintenance_text": _make_maintenance_text(maintenance_windows),
        "monitoring_text": _make_monitoring_log_text(region_events, tz_hint=tz_hint, drift_seconds=drift),
        "internal_timeline_text": _make_internal_timeline_text(internal_entries, correction_note=correction_note),
        "status_page_text": _make_status_page_text(status_updates),
        "email_thread_text": _make_email_thread_text(email_msgs),
    }

    return item_public, {"id": item_id, "answer": gold_answer}, item_assets | {"private_trace": item_private_trace}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-count", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", type=str, required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    rng = random.Random(args.seed)

    solver_bundle = out_dir / "solver_bundle"
    if solver_bundle.exists():
        shutil.rmtree(solver_bundle)
    _mkdir_clean(solver_bundle / "assets")
    _mkdir_clean(solver_bundle / "items")

    items_public: List[Dict[str, Any]] = []
    gold_rows: List[Dict[str, Any]] = []

    # Write shared policy asset once.
    _write_text(solver_bundle / "assets" / "public_policy.md", _make_public_policy_text())

    for i in range(args.sample_count):
        item_public, gold_row, assets = _gen_item(rng, i)
        items_public.append(item_public)
        gold_rows.append(gold_row)

        item_dir = solver_bundle / "items" / item_public["id"]
        _mkdir_clean(item_dir)
        _write_text(item_dir / "contract_rider.md", assets["contract_text"])
        _write_text(item_dir / "maintenance_windows.md", assets["maintenance_text"])
        _write_text(item_dir / "monitoring_log.txt", assets["monitoring_text"])
        _write_text(item_dir / "internal_timeline.md", assets["internal_timeline_text"])
        _write_text(item_dir / "status_page.md", assets["status_page_text"])
        _write_text(item_dir / "email_thread.eml", assets["email_thread_text"])

    # Private gold sample and private trace are creator-side; do not add to solver_bundle.
    _write_jsonl(out_dir / "gold_private_sample.jsonl", gold_rows)
    _write_jsonl(solver_bundle / "items_private_sample.jsonl", items_public)

    _write_json(
        solver_bundle / "SOLVER_MANIFEST.json",
        {
            "benchmark": "Service Credit Forensics (SCF) v1",
            "items_file": "items_private_sample.jsonl",
            "assets": {
                "public_policy": "assets/public_policy.md"
            },
            "notes": "This bundle contains only solver-visible evidence and rules. It does not contain gold answers or creator-side code.",
        },
    )

    _write_text(
        solver_bundle / "README.md",
        (
            "# SCF Solver Packet\n\n"
            "You may use any tools, but **only** files inside this `solver_bundle/` directory.\n\n"
            "## Task\n\n"
            "For each item in `items_private_sample.jsonl`, read the referenced assets and output a JSON prediction row:\n\n"
            "```\n"
            "{\"id\": \"scf_000\", \"answer\": {\"eligible_downtime_minutes\": 12, \"sla_breached\": false, \"credit_percent\": 0, \"credit_usd_cents\": 0}}\n"
            "```\n\n"
            "## Rules\n\n"
            "The authoritative rules are in `assets/public_policy.md` and the item contract rider.\n"
        ),
    )


if __name__ == "__main__":
    main()
