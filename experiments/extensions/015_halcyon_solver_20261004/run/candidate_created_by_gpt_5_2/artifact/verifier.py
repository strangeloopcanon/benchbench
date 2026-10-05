#!/usr/bin/env python3
import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
import json
import os
import re
from typing import Dict, List, Optional, Tuple

APPROVAL_RE = re.compile(r"APPROVE RECEIPT\s+(?P<rid>[A-Za-z0-9_\-]+)\s+\[(?P<mode>FULL|PARTIAL(?:\s+\d+)?)\]")


def money_to_cents(value: Decimal) -> int:
    return int(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100)


def load_jsonl(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_rates(path: str) -> Dict[Tuple[str, str], Decimal]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return {(row["date"], row["currency"]): Decimal(row["usd_per_unit"]) for row in csv.DictReader(f)}


def parse_receipt_line(line: str) -> dict:
    out = {}
    for token in line.split("|"):
        if "=" not in token:
            continue
        k, v = token.split("=", 1)
        out[k.strip()] = v.strip().strip('"')
    return out


def adjudicate_from_assets(case_dir: str, common_dir: str) -> int:
    rates = load_rates(os.path.join(common_dir, "exchange_rates.csv"))
    with open(os.path.join(case_dir, "receipts.txt"), "r", encoding="utf-8") as f:
        receipts = [parse_receipt_line(ln) for ln in f if ln.strip()]
    with open(os.path.join(case_dir, "emails.txt"), "r", encoding="utf-8") as f:
        emails = f.read()

    approvals: Dict[str, Tuple[str, Optional[int]]] = {}
    for m in APPROVAL_RE.finditer(emails):
        mode = m.group("mode")
        approvals[m.group("rid")] = ("FULL", None) if mode == "FULL" else ("PARTIAL", int(mode.split()[1]))

    seen = set()
    eligible: Dict[Optional[str], Optional[int]] = {}
    for receipt in receipts:
        rid = receipt.get("receipt_id")
        key = tuple(receipt.get(field) for field in ("merchant", "date", "ccy", "amount"))
        duplicate = key in seen
        seen.add(key)
        date, currency, amount_text, category = (
            receipt.get("date"),
            receipt.get("ccy"),
            receipt.get("amount"),
            receipt.get("cat"),
        )
        flags = set(receipt.get("flags", "").split(","))
        if rid in approvals and approvals[rid][0] == "PARTIAL":
            eligible[rid] = approvals[rid][1]
            continue
        if flags & {"VOID", "CANCELLED"}:
            eligible[rid] = None
            continue
        if rid in approvals and approvals[rid][0] == "FULL":
            if any(v in {None, "", "?"} for v in (date, currency, amount_text)):
                eligible[rid] = None
                continue
            rate = Decimal("1") if currency == "USD" else rates.get((str(date), str(currency)))
            if rate is None:
                eligible[rid] = None
                continue
            base_cents = money_to_cents(Decimal(str(amount_text)) * rate)
            tip_text = receipt.get("tip")
            tip_cents = money_to_cents(Decimal(str(tip_text)) * rate) if tip_text not in {None, "", "?"} else 0
            eligible[rid] = base_cents + tip_cents
            continue
        if duplicate or (flags & {"DUPLICATE"}) or any(v in {None, "", "?"} for v in (date, currency, amount_text, category)):
            eligible[rid] = None
            continue
        if category == "LODGING" and receipt.get("nights") in {None, "", "?"}:
            eligible[rid] = None
            continue
        rate = Decimal("1") if currency == "USD" else rates.get((str(date), str(currency)))
        if rate is None:
            eligible[rid] = None
            continue
        amount = Decimal(str(amount_text))
        tip_text = receipt.get("tip")
        if tip_text not in {None, "", "?"}:
            tip = Decimal(str(tip_text))
            base_cents = money_to_cents(amount * rate)
            tip_cents = money_to_cents(tip * rate)
            max_tip_cents = money_to_cents(Decimal(base_cents) / 100 * Decimal("0.20"))
            eligible[rid] = base_cents + min(tip_cents, max_tip_cents)
        else:
            eligible[rid] = money_to_cents(amount * rate)

    total = 0
    per_day: Dict[Tuple[Optional[str], Optional[str]], int] = {}
    for receipt in receipts:
        rid = receipt.get("receipt_id")
        cents = eligible.get(rid)
        if cents is None:
            continue
        category, date = receipt.get("cat"), receipt.get("date")
        if rid in approvals:
            total += cents
        elif category == "MISC":
            total += min(cents, 4000)
        elif category == "LODGING":
            nights = receipt.get("nights")
            total += cents if nights in {None, "", "?"} else min(cents, 26000 * int(nights))
        elif category == "AIR":
            total += cents
        elif category in {"GROUND", "MEALS"}:
            per_day[(date, category)] = per_day.get((date, category), 0) + cents
        else:
            total += cents
    for (_date, category), cents in per_day.items():
        total += min(cents, 9000 if category == "GROUND" else 7500)
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--gold", required=True)
    args = ap.parse_args()

    items = load_jsonl(args.items)
    gold = {r["id"]: r["answer"] for r in load_jsonl(args.gold)}
    bundle_root = os.path.abspath(os.path.dirname(args.items))
    common_dir = os.path.join(bundle_root, "common")

    for it in items:
        cid = it["id"]
        computed = adjudicate_from_assets(os.path.join(bundle_root, "cases", cid), common_dir)
        if str(computed) != str(gold.get(cid)):
            raise SystemExit(f"Mismatch on {cid}: gold={gold.get(cid)} computed={computed}")
    print(f"OK: verified {len(items)} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
