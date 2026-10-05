#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import json
import os
import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


POLICY_TEXT = """# ReiFor Policy Excerpt (Public)

This excerpt is the full policy used for these benchmark items.

## Currency + rounding

- Base currency is USD.
- When converting a receipt amount from currency X to USD, use the exchange rate
  from `common/exchange_rates.csv` for the **receipt date** (YYYY-MM-DD).
- Convert as: `usd = round_half_up(amount * rate, 2)` and then to cents.
- `round_half_up` means 0.005 rounds up (e.g., 1.005 -> 1.01).

## Receipt validity

A receipt line is **invalid** (non-reimbursable) if any of the following apply:

- Missing a required field: date, currency code, amount, category.
- The receipt is marked `VOID`, `CANCELLED`, or `DUPLICATE`.
- The receipt appears twice (same merchant + date + currency + amount). Only the first occurrence is eligible.

Exception: if an email contains an explicit approval line of the form:
`APPROVE RECEIPT <receipt_id> [FULL|PARTIAL <usd_cents>]`
then that receipt is reimbursable as approved even if it would otherwise be invalid.

Limits on approvals:
- A FULL approval cannot reimburse a receipt if its **date, currency, or amount**
  fields are missing (because conversion becomes undefined from public evidence).
- A FULL approval cannot override `VOID` or `CANCELLED`.

## Categories and caps (per receipt)

Eligible categories and caps (post-conversion to USD):

- LODGING: cap $260.00 per night. Receipt must indicate number of nights.
  - If `nights=N` is present, cap applies per night: cap = 260.00 * N.
  - If nights is missing, the receipt is invalid unless explicitly approved by email.
- GROUND: cap $90.00 per day (sum of all GROUND receipts on the same date).
- MEALS: cap $75.00 per day (sum of all MEALS receipts on the same date).
- AIR: no cap, but receipt must not be VOID/CANCELLED/DUPLICATE.
- MISC: cap $40.00 per receipt.

## Tips

If a receipt includes a `tip=` field, tips are reimbursable up to **20%** of the
pre-tip base amount on that receipt (after conversion to USD).
Anything above 20% is non-reimbursable unless explicitly approved by email.

## Day definition

All per-day caps use the receipt's local date as written on the receipt line.
"""


def round_half_up_to_cents(x: float) -> int:
    import decimal

    d = decimal.Decimal(str(x)).quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
    return int(d * 100)


def round_half_up_2(x: float) -> float:
    import decimal

    d = decimal.Decimal(str(x)).quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
    return float(d)


@dataclass
class Receipt:
    receipt_id: str
    date: str  # YYYY-MM-DD
    merchant: str
    currency: str
    amount: float  # in receipt currency, includes tip if present
    category: str  # LODGING, GROUND, MEALS, AIR, MISC
    nights: Optional[int] = None  # only for LODGING
    tip: Optional[float] = None  # in receipt currency
    flags: List[str] = None  # e.g., VOID, DUPLICATE
    missing_fields: List[str] = None


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def write_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


def write_jsonl(path: str, rows: List[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def generate_exchange_rates(seed: int) -> Dict[Tuple[str, str], float]:
    rng = random.Random(seed)
    # A small set of currencies; rates vary per date.
    currencies = ["EUR", "GBP", "JPY", "CAD", "AUD"]
    start = dt.date(2026, 4, 1)
    days = 60
    rates: Dict[Tuple[str, str], float] = {}
    base = {"EUR": 1.09, "GBP": 1.27, "JPY": 0.0068, "CAD": 0.73, "AUD": 0.66}
    for i in range(days):
        day = start + dt.timedelta(days=i)
        day_s = day.isoformat()
        for c in currencies:
            jitter = rng.uniform(-0.03, 0.03)
            rate = max(0.0001, base[c] * (1.0 + jitter))
            rates[(day_s, c)] = round_half_up_2(rate)
    return rates


def write_exchange_rates_csv(path: str, rates: Dict[Tuple[str, str], float]) -> None:
    rows = []
    for (d, c), r in sorted(rates.items()):
        rows.append((d, c, f"{r:.2f}" if c != "JPY" else f"{r:.4f}"))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "currency", "usd_per_unit"])
        for d, c, r in rows:
            w.writerow([d, c, r])


def pick_date(rng: random.Random) -> str:
    start = dt.date(2026, 4, 5)
    return (start + dt.timedelta(days=rng.randint(0, 45))).isoformat()


def make_receipt_text(r: Receipt, rng: random.Random) -> str:
    # Render as messy-but-parseable single line with occasional noise tokens.
    parts = []
    parts.append(f"receipt_id={r.receipt_id}")
    if r.missing_fields and "date" in r.missing_fields:
        parts.append("date=?")
    else:
        parts.append(f"date={r.date}")
    if r.missing_fields and "currency" in r.missing_fields:
        parts.append("ccy=?")
    else:
        parts.append(f"ccy={r.currency}")
    if r.missing_fields and "amount" in r.missing_fields:
        parts.append("amount=?")
    else:
        parts.append(f"amount={r.amount:.2f}")
    if r.missing_fields and "category" in r.missing_fields:
        parts.append("cat=?")
    else:
        parts.append(f"cat={r.category}")
    parts.append(f"merchant=\"{r.merchant}\"")
    if r.nights is not None:
        parts.append(f"nights={r.nights}")
    if r.tip is not None:
        parts.append(f"tip={r.tip:.2f}")
    if r.flags:
        parts.append("flags=" + ",".join(r.flags))

    # Add small noise field occasionally to discourage brittle parsers.
    if rng.random() < 0.35:
        parts.append(f"note=\"{rng.choice(['ok','late_scan','fax_copy','itemized','summary'])}\"")

    # Randomly permute order a bit but keep it one line.
    head = parts[:2]
    tail = parts[2:]
    rng.shuffle(tail)
    return " | ".join(head + tail)


def parse_exchange_rates(path: str) -> Dict[Tuple[str, str], float]:
    rates: Dict[Tuple[str, str], float] = {}
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rates[(row["date"], row["currency"])] = float(row["usd_per_unit"])
    return rates


def compute_usd_cents(
    receipt: Receipt,
    rates: Dict[Tuple[str, str], float],
) -> Optional[int]:
    if receipt.missing_fields and any(k in receipt.missing_fields for k in ["date", "currency", "amount", "category"]):
        return None
    if receipt.flags and any(x in {"VOID", "CANCELLED"} for x in receipt.flags):
        return None
    if receipt.date is None or receipt.currency is None:
        return None
    if receipt.currency == "USD":
        usd = receipt.amount
    else:
        rate = rates.get((receipt.date, receipt.currency))
        if rate is None:
            return None
        usd = receipt.amount * rate
    return int(round_half_up_2(usd) * 100)


def apply_tip_rule(receipt: Receipt, usd_cents_total: int, rates: Dict[Tuple[str, str], float]) -> int:
    if receipt.tip is None:
        return usd_cents_total
    # Pre-tip base amount in receipt currency:
    base_amount = max(0.0, receipt.amount - receipt.tip)
    if receipt.currency == "USD":
        base_usd = base_amount
    else:
        rate = rates[(receipt.date, receipt.currency)]
        base_usd = base_amount * rate
    base_usd_cents = int(round_half_up_2(base_usd) * 100)
    max_tip_cents = int(round_half_up_2((base_usd_cents / 100.0) * 0.20) * 100)
    # Total reimbursable capped by tip allowance.
    tip_cents = usd_cents_total - base_usd_cents
    if tip_cents <= max_tip_cents:
        return usd_cents_total
    return base_usd_cents + max_tip_cents


def _parse_receipt_line(line: str) -> dict:
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


def _compute_receipt_usd_cents_from_rendered(rec: dict, rates: Dict[Tuple[str, str], float]) -> Optional[int]:
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

    if cat == "LODGING":
        nights = rec.get("nights")
        if nights in (None, "", "?"):
            return None

    if tip is not None and base_usd is not None:
        base_cents = int(round_half_up_2(base_usd) * 100)
        max_tip_cents = int(round_half_up_2((base_cents / 100.0) * 0.20) * 100)
        tip_cents = usd_cents - base_cents
        if tip_cents > max_tip_cents:
            usd_cents = base_cents + max_tip_cents
    return usd_cents


def adjudicate_from_rendered_assets(receipts_text: str, emails_text: str, rates: Dict[Tuple[str, str], float]) -> int:
    approvals: Dict[str, Tuple[str, Optional[int]]] = {}
    for m in APPROVAL_RE.finditer(emails_text):
        rid = m.group("rid")
        mode = m.group("mode")
        if mode.startswith("FULL"):
            approvals[rid] = ("FULL", None)
        else:
            parts = mode.split()
            if len(parts) == 2 and parts[0] == "PARTIAL":
                approvals[rid] = ("PARTIAL", int(parts[1]))

    parsed = []
    for ln in [x for x in receipts_text.splitlines() if x.strip()]:
        parsed.append(_parse_receipt_line(ln))

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
        usd_cents = _compute_receipt_usd_cents_from_rendered(rec, rates)
        if usd_cents is None or is_dup:
            elig[rid] = None
        else:
            elig[rid] = usd_cents

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

    for (_date, cat), sum_cents in per_day.items():
        if cat == "GROUND":
            total += min(sum_cents, 9000)
        else:
            total += min(sum_cents, 7500)
    return total


APPROVAL_RE = re.compile(r"APPROVE RECEIPT\\s+(?P<rid>[A-Z0-9_\\-]+)\\s+\\[(?P<mode>FULL|PARTIAL(?:\\s+\\d+)?)\\]")


def generate_case(rng: random.Random, case_id: str, rates: Dict[Tuple[str, str], float]) -> Tuple[dict, int, Dict]:
    # Build 6-11 receipts with adversarial edge cases.
    n_receipts = rng.randint(6, 11)
    merchants = [
        "Alpine Hotel",
        "Metro Cab",
        "Sunrise Diner",
        "AeroFly",
        "Corner Mart",
        "Harbor Bistro",
        "CityRail",
        "CloudNine Inn",
        "QuickFuel",
        "Station Cafe",
    ]
    categories = ["LODGING", "GROUND", "MEALS", "AIR", "MISC"]
    currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]

    receipts: List[Receipt] = []
    receipt_ids = []
    base_date = pick_date(rng)
    base_day = dt.date.fromisoformat(base_date)
    for i in range(n_receipts):
        rid = f"{case_id}_R{i+1}"
        receipt_ids.append(rid)
        day = base_day + dt.timedelta(days=rng.randint(0, 3))
        date_s = day.isoformat()
        cat = rng.choice(categories)
        merchant = rng.choice(merchants)
        ccy = rng.choice(currencies)
        if cat == "AIR":
            amount = rng.uniform(120, 820)
        elif cat == "LODGING":
            nights = rng.choice([1, 2, 3])
            amount = rng.uniform(170, 420) * nights
        elif cat == "MEALS":
            amount = rng.uniform(10, 85)
        elif cat == "GROUND":
            amount = rng.uniform(8, 140)
        else:
            amount = rng.uniform(5, 80)

        amount = float(round_half_up_2(amount))
        tip = None
        if cat in {"MEALS"} and rng.random() < 0.5:
            # Sometimes a too-large tip to trigger policy.
            tip_frac = rng.choice([0.1, 0.18, 0.22, 0.35])
            tip = float(round_half_up_2(amount * tip_frac / (1 + tip_frac)))
        flags = []
        missing_fields = []
        nights_val = None
        if cat == "LODGING":
            nights_val = rng.choice([1, 2, 3])
            # Make amount roughly consistent with nights.
            amount = float(round_half_up_2(rng.uniform(150, 390) * nights_val))
            if rng.random() < 0.18:
                # Missing nights is invalid unless approved.
                nights_val = None
        # Inject invalidities.
        if rng.random() < 0.12:
            flags.append(rng.choice(["VOID", "CANCELLED"]))
        if rng.random() < 0.10:
            flags.append("DUPLICATE")
        if rng.random() < 0.18:
            missing_fields.append(rng.choice(["date", "currency", "amount", "category"]))
        receipts.append(
            Receipt(
                receipt_id=rid,
                date=date_s,
                merchant=merchant,
                currency=ccy,
                amount=amount,
                category=cat,
                nights=nights_val,
                tip=tip,
                flags=flags or [],
                missing_fields=missing_fields or [],
            )
        )

    # Force at least one deliberate duplicate pair (not marked DUPLICATE), to require cross-line check.
    if len(receipts) >= 2 and rng.random() < 0.9:
        a, b = rng.sample(range(len(receipts)), 2)
        ra = receipts[a]
        rb = receipts[b]
        rb.merchant = ra.merchant
        rb.date = ra.date
        rb.currency = ra.currency
        rb.amount = ra.amount

    # Create an email thread with 0-2 approvals.
    approvals: Dict[str, Tuple[str, Optional[int]]] = {}
    email_lines = [
        f"Subject: Reimbursement review for {case_id}",
        "",
        "Hi,",
        "I reviewed the attached receipts against the policy excerpt.",
        "",
        "Notes:",
    ]
    approve_count = rng.choice([0, 1, 1, 2])
    to_approve = rng.sample(receipt_ids, approve_count)
    for rid in to_approve:
        mode = rng.choice(["FULL", "PARTIAL"])
        if mode == "FULL":
            approvals[rid] = ("FULL", None)
            email_lines.append(f"- APPROVE RECEIPT {rid} [FULL]")
        else:
            # Choose a plausible partial amount in cents.
            cents = rng.randint(1200, 18000)
            approvals[rid] = ("PARTIAL", cents)
            email_lines.append(f"- APPROVE RECEIPT {rid} [PARTIAL {cents}]")
    email_lines += [
        "",
        "Thanks,",
        rng.choice(["Morgan (Manager)", "Riley (Finance)", "Casey (Ops)"]),
        "",
    ]
    email_text = "\n".join(email_lines)

    # Render receipts as a text exhibit.
    receipt_text_lines = []
    for r in receipts:
        receipt_text_lines.append(make_receipt_text(r, rng))
    receipts_text = "\n".join(receipt_text_lines) + "\n"

    # Compute gold from the rendered public exhibits (the public-evidence path).
    gold_cents = adjudicate_from_rendered_assets(receipts_text, email_text, rates)

    item = {
        "id": case_id,
        "task": "Compute the final reimbursable total under the ReiFor policy, in integer USD cents.",
        "assets": [
            "common/policy.md",
            "common/exchange_rates.csv",
            f"cases/{case_id}/receipts.txt",
            f"cases/{case_id}/emails.txt",
        ],
    }
    private_trace = {
        "approvals": {k: {"mode": v[0], "usd_cents": v[1]} for k, v in approvals.items()},
        "n_receipts": len(receipts),
    }
    return item, gold_cents, {"receipts_text": receipts_text, "emails_text": email_text, "private_trace": private_trace}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-count", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", type=str, required=True)
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    rng = random.Random(args.seed)

    solver_bundle = os.path.join(out_dir, "solver_bundle")
    ensure_dir(os.path.join(solver_bundle, "common"))
    ensure_dir(os.path.join(solver_bundle, "cases"))

    rates = generate_exchange_rates(args.seed + 17)
    write_text(os.path.join(solver_bundle, "common", "policy.md"), POLICY_TEXT)
    write_exchange_rates_csv(os.path.join(solver_bundle, "common", "exchange_rates.csv"), rates)

    items = []
    gold_rows = []
    private_traces = []

    for i in range(args.sample_count):
        case_id = f"reifor_{i:04d}"
        case_dir = os.path.join(solver_bundle, "cases", case_id)
        ensure_dir(case_dir)

        item, gold_cents, payload = generate_case(rng, case_id, rates)
        write_text(os.path.join(case_dir, "receipts.txt"), payload["receipts_text"])
        write_text(os.path.join(case_dir, "emails.txt"), payload["emails_text"])

        items.append(item)
        gold_rows.append({"id": case_id, "answer": str(gold_cents)})
        private_traces.append({"id": case_id, "trace": payload["private_trace"]})

    # Required files.
    write_jsonl(os.path.join(solver_bundle, "items_private_sample.jsonl"), items)
    write_json(
        os.path.join(solver_bundle, "SOLVER_MANIFEST.json"),
        {
            "name": "Reimbursement Forensics (ReiFor)",
            "version": "1.0.0",
            "items_file": "items_private_sample.jsonl",
            "assets_root": ".",
            "prohibited": [
                "gold answers",
                "generator/verifier/scorer code",
                "hidden seeds or private traces",
            ],
        },
    )
    write_text(
        os.path.join(solver_bundle, "README.md"),
        "This solver bundle contains only the solver-visible evidence.\\n"
        "Read `common/policy.md` and `common/exchange_rates.csv`, then for each item open the listed case files.\\n"
        "Return the reimbursable total as integer USD cents.\\n",
    )

    write_jsonl(os.path.join(out_dir, "gold_private_sample.jsonl"), gold_rows)

    # Private audit trace (kept out of solver_bundle).
    write_jsonl(os.path.join(out_dir, "private_generation_trace.jsonl"), private_traces)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
