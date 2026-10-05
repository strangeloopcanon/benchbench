#!/usr/bin/env python3
"""Recompute the preserved Reimbursement Forensics sample with Decimal.

This is an audit of immutable Experiment 004 evidence, not a repaired
benchmark.  It follows the published receipt policy without converting money
through binary floats and reports both changed gold rows and retained-prediction
rescores.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = (
    ROOT
    / "experiments/004_feedback_sweep_20260522_225208/run/candidate_created_by_gpt_5_2"
)
APPROVAL_RE = re.compile(
    r"APPROVE RECEIPT\s+(?P<rid>[A-Z0-9_\-]+)\s+"
    r"\[(?P<mode>FULL|PARTIAL(?:\s+\d+)?)\]"
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_receipt_line(line: str) -> dict[str, str]:
    row: dict[str, str] = {}
    for token in line.split("|"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        row[key.strip()] = value.strip().strip('"')
    return row


def money_to_cents(value: Decimal) -> int:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(rounded * 100)


def load_rates(path: Path) -> dict[tuple[str, str], Decimal]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {
            (row["date"], row["currency"]): Decimal(row["usd_per_unit"])
            for row in csv.DictReader(handle)
        }


def receipt_cents(
    receipt: dict[str, str], rates: dict[tuple[str, str], Decimal]
) -> int | None:
    date = receipt.get("date")
    currency = receipt.get("ccy")
    amount_text = receipt.get("amount")
    category = receipt.get("cat")
    flags = set(receipt.get("flags", "").split(","))
    if any(value in {None, "", "?"} for value in (date, currency, amount_text, category)):
        return None
    if flags & {"VOID", "CANCELLED", "DUPLICATE"}:
        return None
    if category == "LODGING" and receipt.get("nights") in {None, "", "?"}:
        return None

    amount = Decimal(str(amount_text))
    rate = Decimal("1") if currency == "USD" else rates.get((str(date), str(currency)))
    if rate is None:
        return None
    total_cents = money_to_cents(amount * rate)

    tip_text = receipt.get("tip")
    if tip_text not in {None, "", "?"}:
        base_cents = money_to_cents((amount - Decimal(str(tip_text))) * rate)
        max_tip_cents = money_to_cents(Decimal(base_cents) / 100 * Decimal("0.20"))
        total_cents = min(total_cents, base_cents + max_tip_cents)
    return total_cents


def case_total(case_dir: Path, rates: dict[tuple[str, str], Decimal]) -> int:
    receipts = [
        parse_receipt_line(line)
        for line in (case_dir / "receipts.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    emails = (case_dir / "emails.txt").read_text(encoding="utf-8")
    approvals: dict[str, tuple[str, int | None]] = {}
    for match in APPROVAL_RE.finditer(emails):
        mode = match.group("mode")
        approvals[match.group("rid")] = (
            ("FULL", None)
            if mode == "FULL"
            else ("PARTIAL", int(mode.split()[1]))
        )

    seen: set[tuple[str | None, ...]] = set()
    eligible: dict[str | None, int | None] = {}
    for receipt in receipts:
        key = tuple(receipt.get(field) for field in ("merchant", "date", "ccy", "amount"))
        duplicate = key in seen
        seen.add(key)
        eligible[receipt.get("receipt_id")] = None if duplicate else receipt_cents(receipt, rates)

    for receipt_id, (mode, approved_cents) in approvals.items():
        if mode == "PARTIAL":
            eligible[receipt_id] = approved_cents
            continue
        receipt = next((row for row in receipts if row.get("receipt_id") == receipt_id), None)
        if receipt is None:
            continue
        flags = set(receipt.get("flags", "").split(","))
        date, currency, amount_text = (
            receipt.get("date"),
            receipt.get("ccy"),
            receipt.get("amount"),
        )
        if flags & {"VOID", "CANCELLED"} or any(
            value in {None, "", "?"} for value in (date, currency, amount_text)
        ):
            continue
        rate = Decimal("1") if currency == "USD" else rates.get((str(date), str(currency)))
        if rate is not None:
            eligible[receipt_id] = money_to_cents(Decimal(str(amount_text)) * rate)

    total = 0
    per_day: dict[tuple[str | None, str | None], int] = {}
    for receipt in receipts:
        cents = eligible.get(receipt.get("receipt_id"))
        if cents is None:
            continue
        category, date = receipt.get("cat"), receipt.get("date")
        if category == "MISC":
            total += min(cents, 4000)
        elif category == "LODGING":
            total += min(cents, 26000 * int(receipt.get("nights", "0")))
        elif category == "AIR":
            total += cents
        elif category in {"GROUND", "MEALS"}:
            per_day[(date, category)] = per_day.get((date, category), 0) + cents
    for (_date, category), cents in per_day.items():
        total += min(cents, 9000 if category == "GROUND" else 7500)
    return total


ACTUAL_POLICY_APPROVAL_RE = re.compile(
    r"APPROVE RECEIPT\s+(?P<rid>[A-Za-z0-9_\-]+)\s+"
    r"\[(?P<mode>FULL|PARTIAL(?:\s+\d+)?)\]"
)


def actual_policy_case_total(
    case_dir: Path,
    rates: dict[tuple[str, str], Decimal],
    *,
    pre_tip: bool = True,
) -> int:
    """Compute the reimbursable total under the actual policy when email approvals are honored."""
    receipts = [
        parse_receipt_line(line)
        for line in (case_dir / "receipts.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    emails = (case_dir / "emails.txt").read_text(encoding="utf-8")
    approvals: dict[str, tuple[str, int | None]] = {}
    for match in ACTUAL_POLICY_APPROVAL_RE.finditer(emails):
        mode = match.group("mode")
        approvals[match.group("rid")] = (
            ("FULL", None)
            if mode == "FULL"
            else ("PARTIAL", int(mode.split()[1]))
        )

    seen: set[tuple[str | None, ...]] = set()
    eligible: dict[str | None, int | None] = {}
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
            if any(value in {None, "", "?"} for value in (date, currency, amount_text)):
                eligible[rid] = None
                continue
            rate = Decimal("1") if currency == "USD" else rates.get((str(date), str(currency)))
            if rate is None:
                eligible[rid] = None
                continue
            base_cents = money_to_cents(Decimal(str(amount_text)) * rate)
            tip_text = receipt.get("tip")
            tip_cents = (
                money_to_cents(Decimal(str(tip_text)) * rate)
                if pre_tip and tip_text not in {None, "", "?"}
                else 0
            )
            eligible[rid] = base_cents + tip_cents
            continue
        if (
            duplicate
            or (flags & {"DUPLICATE"})
            or any(value in {None, "", "?"} for value in (date, currency, amount_text, category))
        ):
            eligible[rid] = None
            continue
        if category == "LODGING" and receipt.get("nights") in {None, "", "?"}:
            eligible[rid] = None
            continue

        amount = Decimal(str(amount_text))
        rate = Decimal("1") if currency == "USD" else rates.get((str(date), str(currency)))
        if rate is None:
            eligible[rid] = None
            continue
        tip_text = receipt.get("tip")
        if tip_text not in {None, "", "?"}:
            tip = Decimal(str(tip_text))
            if pre_tip:
                base_cents = money_to_cents(amount * rate)
                tip_cents = money_to_cents(tip * rate)
                max_tip_cents = money_to_cents(Decimal(base_cents) / 100 * Decimal("0.20"))
                eligible[rid] = base_cents + min(tip_cents, max_tip_cents)
            else:
                total_cents = money_to_cents(amount * rate)
                base_cents = money_to_cents((amount - tip) * rate)
                max_tip_cents = money_to_cents(Decimal(base_cents) / 100 * Decimal("0.20"))
                eligible[rid] = min(total_cents, base_cents + max_tip_cents)
        else:
            eligible[rid] = money_to_cents(amount * rate)

    total = 0
    per_day: dict[tuple[str | None, str | None], int] = {}
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
            if nights in {None, "", "?"}:
                total += cents
            else:
                total += min(cents, 26000 * int(nights))
        elif category == "AIR":
            total += cents
        elif category in {"GROUND", "MEALS"}:
            per_day[(date, category)] = per_day.get((date, category), 0) + cents
        else:
            total += cents
    for (_date, category), cents in per_day.items():
        total += min(cents, 9000 if category == "GROUND" else 7500)
    return total


def audit(candidate: Path = CANDIDATE) -> dict[str, Any]:
    bundle = candidate / "solver_bundle"
    rates = load_rates(bundle / "common/exchange_rates.csv")
    historical = {row["id"]: int(row["answer"]) for row in read_jsonl(candidate / "gold_private_sample.jsonl")}
    corrected = {
        item_id: case_total(bundle / "cases" / item_id, rates)
        for item_id in historical
    }
    actual_pre_tip = {
        item_id: actual_policy_case_total(bundle / "cases" / item_id, rates, pre_tip=True)
        for item_id in historical
    }
    actual_post_tip = {
        item_id: actual_policy_case_total(bundle / "cases" / item_id, rates, pre_tip=False)
        for item_id in historical
    }
    changed = [
        {"id": item_id, "historical": historical[item_id], "decimal_half_up": corrected[item_id]}
        for item_id in historical
        if historical[item_id] != corrected[item_id]
    ]
    rescores: dict[str, int] = {}
    actual_pre_tip_rescores: dict[str, int] = {}
    actual_post_tip_rescores: dict[str, int] = {}
    for predictions_path in sorted(candidate.glob("predictions_solver_*.jsonl")):
        key = predictions_path.stem.removeprefix("predictions_solver_")
        predictions = {row["id"]: row["answer"] for row in read_jsonl(predictions_path)}
        rescores[key] = sum(
            str(predictions.get(item_id)) == str(answer)
            for item_id, answer in corrected.items()
        )
        actual_pre_tip_rescores[key] = sum(
            str(predictions.get(item_id)) == str(answer)
            for item_id, answer in actual_pre_tip.items()
        )
        actual_post_tip_rescores[key] = sum(
            str(predictions.get(item_id)) == str(answer)
            for item_id, answer in actual_post_tip.items()
        )
    return {
        "changed_gold": changed,
        "retained_prediction_rescores": rescores,
        "actual_policy_pre_tip_rescores": actual_pre_tip_rescores,
        "actual_policy_post_tip_rescores": actual_post_tip_rescores,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    args = parser.parse_args()
    print(json.dumps(audit(args.candidate), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
