#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
from typing import Dict, List, Optional, Tuple


def round_half_up_2(x: float) -> float:
    import decimal

    d = decimal.Decimal(str(x)).quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
    return float(d)


def load_jsonl(path: str) -> List[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_rates(path: str) -> Dict[Tuple[str, str], float]:
    rates: Dict[Tuple[str, str], float] = {}
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rates[(row["date"], row["currency"])] = float(row["usd_per_unit"])
    return rates


def parse_receipt_line(line: str) -> dict:
    # Very permissive parse: key=value tokens separated by '|'
    tokens = [t.strip() for t in line.split("|")]
    out = {}
    for tok in tokens:
        if "=" not in tok:
            continue
        k, v = tok.split("=", 1)
        k = k.strip()
        v = v.strip().strip()
        if v.startswith("\"") and v.endswith("\""):
            v = v[1:-1]
        out[k] = v
    return out


APPROVAL_RE = re.compile(r"APPROVE RECEIPT\\s+(?P<rid>[A-Z0-9_\\-]+)\\s+\\[(?P<mode>FULL|PARTIAL(?:\\s+\\d+)?)\\]")


def compute_receipt_usd_cents(rec: dict, rates: Dict[Tuple[str, str], float]) -> Optional[int]:
    date = rec.get("date")
    ccy = rec.get("ccy")
    amount_s = rec.get("amount")
    cat = rec.get("cat")
    flags = rec.get("flags", "")

    if date in (None, "?", "") or ccy in (None, "?", "") or amount_s in (None, "?", "") or cat in (None, "?", ""):
        return None
    if any(x in flags.split(",") for x in ["VOID", "CANCELLED", "DUPLICATE"]):
        return None
    try:
        amt = float(amount_s)
    except Exception:
        return None

    tip = None
    if "tip" in rec and rec["tip"] not in ("?", ""):
        try:
            tip = float(rec["tip"])
        except Exception:
            tip = None

    if ccy == "USD":
        usd = amt
        base_usd = amt - tip if tip is not None else None
    else:
        rate = rates.get((date, ccy))
        if rate is None:
            return None
        usd = amt * rate
        base_usd = (amt - tip) * rate if tip is not None else None

    usd_cents = int(round_half_up_2(usd) * 100)

    # Lodging needs nights.
    if cat == "LODGING":
        nights = rec.get("nights")
        if nights in (None, "", "?"):
            return None

    # Tip cap: up to 20% of pre-tip base.
    if tip is not None and base_usd is not None:
        base_cents = int(round_half_up_2(base_usd) * 100)
        max_tip_cents = int(round_half_up_2((base_cents / 100.0) * 0.20) * 100)
        tip_cents = usd_cents - base_cents
        if tip_cents > max_tip_cents:
            usd_cents = base_cents + max_tip_cents
    return usd_cents


def adjudicate_from_assets(case_dir: str, common_dir: str) -> int:
    rates = load_rates(os.path.join(common_dir, "exchange_rates.csv"))
    receipts_path = os.path.join(case_dir, "receipts.txt")
    emails_path = os.path.join(case_dir, "emails.txt")

    with open(receipts_path, "r", encoding="utf-8") as f:
        receipt_lines = [ln.strip() for ln in f.readlines() if ln.strip()]
    with open(emails_path, "r", encoding="utf-8") as f:
        emails = f.read()

    approvals: Dict[str, Tuple[str, Optional[int]]] = {}
    for m in APPROVAL_RE.finditer(emails):
        rid = m.group("rid")
        mode = m.group("mode")
        if mode.startswith("FULL"):
            approvals[rid] = ("FULL", None)
        else:
            parts = mode.split()
            if len(parts) == 2 and parts[0] == "PARTIAL":
                approvals[rid] = ("PARTIAL", int(parts[1]))

    parsed = []
    for ln in receipt_lines:
        rec = parse_receipt_line(ln)
        parsed.append(rec)

    # Deduplicate (merchant+date+ccy+amount) keeping first.
    seen = set()
    elig: Dict[str, Optional[int]] = {}
    for rec in parsed:
        rid = rec.get("receipt_id")
        merchant = rec.get("merchant", "")
        date = rec.get("date")
        ccy = rec.get("ccy")
        amount = rec.get("amount")
        key = (merchant, date, ccy, amount)
        is_dup = key in seen
        if not is_dup:
            seen.add(key)
        usd_cents = compute_receipt_usd_cents(rec, rates)
        if usd_cents is None or is_dup:
            elig[rid] = None
        else:
            elig[rid] = usd_cents

    # Apply approvals.
    for rid, (mode, val) in approvals.items():
        if mode == "PARTIAL" and val is not None:
            elig[rid] = val
        elif mode == "FULL":
            rec = next((x for x in parsed if x.get("receipt_id") == rid), None)
            if rec is None:
                continue
            flags = rec.get("flags", "")
            if any(x in flags.split(",") for x in ["VOID", "CANCELLED"]):
                continue
            # FULL approval: compute using available numeric fields, even if other fields were '?'
            # but if core numeric fields are missing, we still cannot reimburse.
            date = rec.get("date")
            ccy = rec.get("ccy")
            amount_s = rec.get("amount")
            if date in (None, "?", "") or ccy in (None, "?", "") or amount_s in (None, "?", ""):
                continue
            try:
                amt = float(amount_s)
            except Exception:
                continue
            if ccy == "USD":
                usd = amt
            else:
                rate = rates.get((date, ccy))
                if rate is None:
                    continue
                usd = amt * rate
            elig[rid] = int(round_half_up_2(usd) * 100)

    total = 0
    per_day: Dict[Tuple[str, str], int] = {}
    for rec in parsed:
        rid = rec.get("receipt_id")
        usd_cents = elig.get(rid)
        if usd_cents is None:
            continue
        cat = rec.get("cat")
        date = rec.get("date")
        if cat == "MISC":
            total += min(usd_cents, 4000)
        elif cat == "LODGING":
            try:
                nights = int(rec.get("nights"))
            except Exception:
                nights = 0
            total += min(usd_cents, 26000 * nights)
        elif cat == "AIR":
            total += usd_cents
        elif cat in ("GROUND", "MEALS"):
            per_day[(date, cat)] = per_day.get((date, cat), 0) + usd_cents

    for (date, cat), sum_cents in per_day.items():
        if cat == "GROUND":
            total += min(sum_cents, 9000)
        else:
            total += min(sum_cents, 7500)
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--gold", required=True)
    args = ap.parse_args()

    items = load_jsonl(args.items)
    gold = {r["id"]: r["answer"] for r in load_jsonl(args.gold)}
    bundle_root = os.path.abspath(os.path.join(os.path.dirname(args.items)))
    common_dir = os.path.join(bundle_root, "common")

    missing = []
    mismatched = []
    for it in items:
        cid = it["id"]
        case_dir = os.path.join(bundle_root, "cases", cid)
        computed = adjudicate_from_assets(case_dir, common_dir)
        g = gold.get(cid)
        if g is None:
            missing.append(cid)
            continue
        if str(computed) != str(g):
            mismatched.append((cid, g, computed))

    if missing:
        raise SystemExit(f"Missing gold rows for: {missing[:5]} (and {max(0, len(missing)-5)} more)")
    if mismatched:
        sample = mismatched[:5]
        msg = "\n".join([f"{cid}: gold={g} computed={c}" for cid, g, c in sample])
        raise SystemExit(f"Gold mismatch on {len(mismatched)} items. Sample:\n{msg}")
    print(f"OK: verified {len(items)} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
