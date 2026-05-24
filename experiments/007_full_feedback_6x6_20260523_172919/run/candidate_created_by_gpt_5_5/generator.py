#!/usr/bin/env python3
import argparse
import json
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SERVICES = {
    "MRI_LUMBAR": {"label": "Lumbar spine MRI without contrast", "base": 185000, "auth": True, "ref": False, "coins": 20, "copay": 0, "ded": True, "code": "72148"},
    "PT_EVAL": {"label": "Physical therapy initial evaluation", "base": 31000, "auth": False, "ref": True, "coins": 10, "copay": 3500, "ded": False, "code": "97161"},
    "SLEEP_STUDY": {"label": "Attended diagnostic sleep study", "base": 142000, "auth": True, "ref": True, "coins": 15, "copay": 0, "ded": True, "code": "95810"},
    "DERM_EXCISION": {"label": "Dermatology benign lesion excision", "base": 76000, "auth": False, "ref": True, "coins": 20, "copay": 4500, "ded": False, "code": "11402"},
    "INFUSION": {"label": "Specialty drug infusion, first hour", "base": 224000, "auth": True, "ref": False, "coins": 25, "copay": 0, "ded": True, "code": "96413"},
    "URGENT_XRAY": {"label": "Urgent care ankle x-ray", "base": 28000, "auth": False, "ref": False, "coins": 0, "copay": 7000, "ded": False, "code": "73610"},
}

PLANS = {
    "HMO_SILVER": {"name": "HMO Silver", "oop_max": 420000, "deductible": 90000, "oon_mult": None, "ref_required": True},
    "PPO_GOLD": {"name": "PPO Gold", "oop_max": 300000, "deductible": 50000, "oon_mult": 0.55, "ref_required": False},
    "EPO_PLUS": {"name": "EPO Plus", "oop_max": 360000, "deductible": 70000, "oon_mult": None, "ref_required": False},
}

DENIALS = {
    "OK": "approved",
    "NO_AUTH": "denied_missing_or_invalid_authorization",
    "NO_REF": "denied_missing_or_invalid_referral",
    "OON": "denied_out_of_network_not_allowed",
    "NOT_COVERED": "denied_noncovered_service",
    "DATE": "denied_service_outside_valid_window",
}


def money(cents: int) -> str:
    return f"${cents // 100}.{cents % 100:02d}"


def jdump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


@dataclass
class Item:
    id: str
    answer: dict[str, Any]
    dossier: str
    visible: dict[str, Any]
    trace: dict[str, Any]


def adjudicate(plan_key: str, service_key: str, in_network: bool, auth_ok: bool, ref_ok: bool,
               date_ok: bool, rider: str, prior_oop: int, prior_ded: int) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = PLANS[plan_key]
    svc = SERVICES[service_key].copy()
    if rider == "auth_waiver":
        svc["auth"] = False
    if rider == "ref_waiver":
        svc["ref"] = False
    if rider == "noncovered_infusion" and service_key == "INFUSION":
        return ({"status": "denied", "reason_code": "NOT_COVERED", "allowed_cents": 0, "insurer_pays_cents": 0, "patient_owes_cents": 0},
                {"rule": "rider excluded infusion"})
    if not date_ok:
        return ({"status": "denied", "reason_code": "DATE", "allowed_cents": 0, "insurer_pays_cents": 0, "patient_owes_cents": 0},
                {"rule": "service outside document window"})
    if (not in_network) and plan["oon_mult"] is None:
        return ({"status": "denied", "reason_code": "OON", "allowed_cents": 0, "insurer_pays_cents": 0, "patient_owes_cents": 0},
                {"rule": "out-of-network not allowed"})
    if svc["auth"] and not auth_ok:
        return ({"status": "denied", "reason_code": "NO_AUTH", "allowed_cents": 0, "insurer_pays_cents": 0, "patient_owes_cents": 0},
                {"rule": "authorization required"})
    if plan["ref_required"] and svc["ref"] and not ref_ok:
        return ({"status": "denied", "reason_code": "NO_REF", "allowed_cents": 0, "insurer_pays_cents": 0, "patient_owes_cents": 0},
                {"rule": "referral required"})

    allowed = svc["base"]
    if not in_network:
        allowed = int(round(allowed * plan["oon_mult"] / 100.0)) * 100
    patient = 0
    remaining_ded = max(0, plan["deductible"] - prior_ded)
    if svc["ded"] and remaining_ded:
        ded_applied = min(remaining_ded, allowed)
        patient += ded_applied
        allowed_after_ded = allowed - ded_applied
    else:
        ded_applied = 0
        allowed_after_ded = allowed
    if svc["copay"]:
        patient += min(svc["copay"], allowed_after_ded)
        coins_base = max(0, allowed_after_ded - svc["copay"])
    else:
        coins_base = allowed_after_ded
    patient += int(round(coins_base * svc["coins"] / 100.0))
    remaining_oop = max(0, plan["oop_max"] - prior_oop)
    patient = min(patient, remaining_oop)
    insurer = allowed - patient
    return ({"status": "approved", "reason_code": "OK", "allowed_cents": allowed, "insurer_pays_cents": insurer, "patient_owes_cents": patient},
            {"allowed": allowed, "ded_applied": ded_applied, "remaining_oop": remaining_oop, "service": svc})


def make_item(rng: random.Random, idx: int) -> Item:
    item_id = f"PAF-{idx:03d}"
    plan_key = rng.choice(list(PLANS))
    service_key = rng.choice(list(SERVICES))
    in_network = rng.random() > 0.23
    auth_ok = rng.random() > 0.28
    ref_ok = rng.random() > 0.30
    date_ok = rng.random() > 0.12
    rider = rng.choice(["none", "none", "none", "auth_waiver", "ref_waiver", "noncovered_infusion"])
    prior_oop = rng.randrange(0, 360000, 2500)
    prior_ded = rng.randrange(0, 100000, 5000)
    presets = {
        1: {"plan_key": "HMO_SILVER", "service_key": "PT_EVAL", "in_network": True, "auth_ok": True, "ref_ok": False, "date_ok": True, "rider": "none"},
        2: {"plan_key": "PPO_GOLD", "service_key": "MRI_LUMBAR", "in_network": True, "auth_ok": False, "ref_ok": True, "date_ok": True, "rider": "none"},
        3: {"plan_key": "EPO_PLUS", "service_key": "DERM_EXCISION", "in_network": False, "auth_ok": True, "ref_ok": True, "date_ok": True, "rider": "none"},
        4: {"plan_key": "PPO_GOLD", "service_key": "INFUSION", "in_network": True, "auth_ok": True, "ref_ok": True, "date_ok": True, "rider": "noncovered_infusion"},
        5: {"plan_key": "HMO_SILVER", "service_key": "SLEEP_STUDY", "in_network": True, "auth_ok": True, "ref_ok": True, "date_ok": False, "rider": "none"},
        6: {"plan_key": "PPO_GOLD", "service_key": "MRI_LUMBAR", "in_network": False, "auth_ok": True, "ref_ok": True, "date_ok": True, "rider": "auth_waiver"},
    }
    if idx in presets:
        preset = presets[idx]
        plan_key = preset["plan_key"]
        service_key = preset["service_key"]
        in_network = preset["in_network"]
        auth_ok = preset["auth_ok"]
        ref_ok = preset["ref_ok"]
        date_ok = preset["date_ok"]
        rider = preset["rider"]
    ans, trace = adjudicate(plan_key, service_key, in_network, auth_ok, ref_ok, date_ok, rider, prior_oop, prior_ded)
    plan = PLANS[plan_key]
    svc = SERVICES[service_key]
    member = f"M{rng.randrange(10000,99999)}"
    svc_date = f"2026-0{rng.randint(1,5)}-{rng.randint(10,28):02d}" if date_ok else f"2026-07-{rng.randint(1,20):02d}"
    auth_id = f"A-{rng.randrange(100000,999999)}" if auth_ok else ""
    ref_id = f"R-{rng.randrange(100000,999999)}" if ref_ok else ""
    provider_status = "in network" if in_network else "out of network"
    rider_text = {
        "none": "No special rider changes apply to this member for the service category.",
        "auth_waiver": "Member rider RW-14 waives prior authorization for radiology, sleep, and infusion services when the ordering clinician documents conservative treatment or medical necessity.",
        "ref_waiver": "Member rider RW-22 waives primary-care referral requirements for therapy, sleep medicine, and dermatology visits.",
        "noncovered_infusion": "Member rider RX-9 excludes office-administered specialty drug infusion from medical benefits unless a separate pharmacy approval letter is present. No pharmacy approval letter is in this packet.",
    }[rider]
    dossier = f"""# Claim Dossier {item_id}

## Member and plan card
- Member id: {member}
- Plan: {plan['name']} ({plan_key})
- Accumulators before this claim: deductible met {money(prior_ded)}; out-of-pocket met {money(prior_oop)}.
- Current benefit year documents are valid for services from 2026-01-01 through 2026-06-30.

## Benefit manual excerpts
- HMO Silver and EPO Plus do not pay out-of-network non-emergency services. PPO Gold pays out-of-network allowed amount at 55 percent of the in-network schedule.
- If a service is denied, report zero allowed amount, zero insurer payment, and zero patient responsibility for this benchmark.
- For approved claims, patient responsibility is deductible first when the service row says deductible applies, then copay, then coinsurance. The out-of-pocket maximum caps patient responsibility.
- HMO Silver requires a primary-care referral when both the plan requires referrals and the service row marks referral required. PPO Gold and EPO Plus do not have plan-level referral requirements.

## Service schedule excerpt
| service_key | CPT | description | in-network allowed | prior auth? | referral? | deductible? | copay | coinsurance |
|---|---|---|---:|---|---|---|---:|---:|
| {service_key} | {svc['code']} | {svc['label']} | {money(svc['base'])} | {'yes' if svc['auth'] else 'no'} | {'yes' if svc['ref'] else 'no'} | {'yes' if svc['ded'] else 'no'} | {money(svc['copay'])} | {svc['coins']}% |

## Member rider
{rider_text}

## Provider directory note
The rendering provider listed for this claim is marked **{provider_status}** for {plan['name']} on the service date. Directory notes say urgent care emergency exceptions do not apply unless the claim is emergency-coded; this claim is not emergency-coded.

## Utilization and referral correspondence
- Prior authorization letter: {'approved, id ' + auth_id + ', valid for the listed service during the benefit-year document window' if auth_ok else 'no matching approved authorization appears in the packet'}
- Primary-care referral: {'approved, id ' + ref_id + ', valid for the listed service during the benefit-year document window' if ref_ok else 'no matching approved referral appears in the packet'}
- Service-date check: {'the claim date falls inside the current benefit-year document window' if date_ok else 'the claim date is after 2026-06-30, and no later benefit manual is included'}

## Claim line
Claim line CL-{idx:03d}: service date {svc_date}; service_key {service_key}; CPT {svc['code']}; billed by rendering provider above.

Return exactly one JSON object for this item with keys:
`status`, `reason_code`, `allowed_cents`, `insurer_pays_cents`, `patient_owes_cents`.
"""
    return Item(item_id, ans, dossier, {"id": item_id, "asset": f"dossiers/{item_id}.md"}, {"inputs": {
        "plan": plan_key, "service": service_key, "in_network": in_network, "auth_ok": auth_ok,
        "ref_ok": ref_ok, "date_ok": date_ok, "rider": rider, "prior_oop": prior_oop, "prior_ded": prior_ded
    }, "trace": trace})


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-count", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260516)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    out = Path(args.out_dir)
    bundle = out / "solver_bundle"
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / "dossiers").mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    items = [make_item(rng, i + 1) for i in range(args.sample_count)]
    write_jsonl(out / "gold_private_sample.jsonl", [{"id": it.id, "answer": it.answer} for it in items])
    write_jsonl(bundle / "items_private_sample.jsonl", [it.visible for it in items])
    write_jsonl(out / "private_audit_traces.jsonl", [{"id": it.id, **it.trace} for it in items])
    for it in items:
        (bundle / it.visible["asset"]).write_text(it.dossier, encoding="utf-8")
    manifest = {
        "benchmark": "Prior Authorization Forensics (PAF) v1",
        "item_file": "items_private_sample.jsonl",
        "assets": "dossiers/*.md",
        "prediction_format": {"id": "string", "answer": {"status": "approved|denied", "reason_code": "OK|NO_AUTH|NO_REF|OON|NOT_COVERED|DATE", "allowed_cents": "integer", "insurer_pays_cents": "integer", "patient_owes_cents": "integer"}},
        "notes": "All answer-determining rules and evidence are in the dossier files. Do not infer from file order.",
    }
    (bundle / "SOLVER_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    packet = """# Prior Authorization Forensics (PAF) v1 Solver Packet

You are given 30 fictional health-insurance claim dossiers. For each id in
`items_private_sample.jsonl`, open the referenced Markdown dossier under
`dossiers/` and adjudicate the single claim line.

Return one JSONL prediction row per item:

```json
{"id":"PAF-001","answer":{"status":"approved","reason_code":"OK","allowed_cents":12345,"insurer_pays_cents":10000,"patient_owes_cents":2345}}
```

Allowed reason codes are `OK`, `NO_AUTH`, `NO_REF`, `OON`, `NOT_COVERED`, and
`DATE`. If the claim is denied, the benchmark convention is zero allowed,
zero insurer payment, and zero patient responsibility. Cents are integer cents,
with no dollar signs or commas.

The dossiers intentionally include only excerpts needed for each claim. The
task is to reconcile plan type, service schedule, riders, network status,
authorization/referral correspondence, document dates, and accumulators.
"""
    (bundle / "README.md").write_text(packet, encoding="utf-8")
    print(f"generated {len(items)} items in {out}")


if __name__ == "__main__":
    main()
