#!/usr/bin/env python3
"""
Weak baseline: sum all non-VOID/CANCELLED receipts converted to USD, ignoring:
- missing-field invalidation
- duplicates
- category caps
- tip caps
- lodging nights requirement
- approval overrides

This is intentionally naive and should score poorly.
"""

import argparse
import csv
import json
import os


def round_half_up_2(x: float) -> float:
    import decimal

    d = decimal.Decimal(str(x)).quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
    return float(d)


def load_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def load_rates(path: str):
    rates = {}
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rates[(row["date"], row["currency"])] = float(row["usd_per_unit"])
    return rates


def parse_receipt_line(line: str) -> dict:
    tokens = [t.strip() for t in line.split("|")]
    out = {}
    for tok in tokens:
        if "=" not in tok:
            continue
        k, v = tok.split("=", 1)
        k = k.strip()
        v = v.strip()
        if v.startswith("\"") and v.endswith("\""):
            v = v[1:-1]
        out[k] = v
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    bundle_root = os.path.abspath(os.path.dirname(args.items))
    rates = load_rates(os.path.join(bundle_root, "common", "exchange_rates.csv"))

    preds = []
    for it in load_jsonl(args.items):
        cid = it["id"]
        receipts_path = os.path.join(bundle_root, "cases", cid, "receipts.txt")
        total = 0
        with open(receipts_path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                rec = parse_receipt_line(ln)
                flags = rec.get("flags", "")
                if "VOID" in flags or "CANCELLED" in flags:
                    continue
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
                total += int(round_half_up_2(usd) * 100)
        preds.append({"id": cid, "answer": str(total)})

    with open(args.out, "w", encoding="utf-8") as f:
        for r in preds:
            f.write(json.dumps(r) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
