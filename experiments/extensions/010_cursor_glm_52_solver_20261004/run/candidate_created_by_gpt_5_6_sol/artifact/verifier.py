#!/usr/bin/env python3
"""Structural, semantic, and identifiability verifier for AuditWeave."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from auditweave_core import REGS, solve_public_item, topological_orders


def load_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            try:
                rows.append(json.loads(line))
            except Exception as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def validate_item(item):
    required = {"id", "initial", "phases", "query_ops", "answer_format"}
    if set(item) != required:
        raise ValueError(f"{item.get('id')}: item keys differ from {sorted(required)}")
    if not re.fullmatch(r"aw-[0-9]{3,}", item["id"]):
        raise ValueError("bad id")
    if set(item["initial"]) != {"v", "bits"} or set(item["initial"]["v"]) != set(REGS):
        raise ValueError(f"{item['id']}: bad initial state")
    if any(type(x) is not int or not 0 <= x < 97 for x in item["initial"]["v"].values()):
        raise ValueError(f"{item['id']}: noncanonical register")
    if len(item["initial"]["bits"]) != 4 or any(x not in (0, 1) for x in item["initial"]["bits"]):
        raise ValueError(f"{item['id']}: bad bits")
    if len(item["phases"]) != 3 or not item["query_ops"]:
        raise ValueError(f"{item['id']}: expected three phases and a query")
    holes = 0
    order_counts = []
    for pidx, phase in enumerate(item["phases"], 1):
        if set(phase) != {"phase", "events", "before", "audits"} or phase["phase"] != pidx:
            raise ValueError(f"{item['id']}: malformed phase")
        if len(phase["events"]) != 6 or not phase["audits"]:
            raise ValueError(f"{item['id']}: phase cardinality")
        ids = [e.get("eid") for e in phase["events"]]
        if len(set(ids)) != 6:
            raise ValueError(f"{item['id']}: duplicate event id")
        order_counts.append(len(topological_orders(phase["events"], phase["before"])))
        for event in phase["events"]:
            if set(event) == {"eid", "candidates"}:
                holes += 1
                if [c.get("label") for c in event["candidates"]] != ["A", "B", "C", "D"]:
                    raise ValueError(f"{item['id']}: bad candidates")
            elif set(event) != {"eid", "op"}:
                raise ValueError(f"{item['id']}: bad event shape")
    if holes != 1:
        raise ValueError(f"{item['id']}: expected one disputed event")
    return order_counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--gold", required=True)
    args = ap.parse_args()
    items = load_jsonl(args.items)
    gold = load_jsonl(args.gold)
    if any(set(row) != {"id", "answer"} for row in gold):
        raise SystemExit("gold rows must contain exactly id and answer")
    if len({x["id"] for x in items}) != len(items) or len({x["id"] for x in gold}) != len(gold):
        raise SystemExit("duplicate ids")
    gold_map = {x["id"]: x["answer"] for x in gold}
    if set(gold_map) != {x["id"] for x in items}:
        raise SystemExit("item/gold id mismatch")
    witness_total = 0
    witness_counts = []
    all_order_counts = []
    for item in items:
        all_order_counts.extend(validate_item(item))
        answers = solve_public_item(item)
        if len(answers) != 1:
            raise SystemExit(f"{item['id']}: {len(answers)} public answers, expected 1")
        expected = next(iter(answers))
        if gold_map[item["id"]] != expected:
            raise SystemExit(f"{item['id']}: gold does not match public derivation")
        item_witnesses = sum(answers.values())
        witness_total += item_witnesses
        witness_counts.append(item_witnesses)
    print(json.dumps({
        "status": "ok",
        "items": len(items),
        "unique_answers": len(items),
        "total_reconstruction_witnesses": witness_total,
        "witnesses_per_item_min": min(witness_counts),
        "witnesses_per_item_max": max(witness_counts),
        "legal_orders_per_phase_min": min(all_order_counts),
        "legal_orders_per_phase_max": max(all_order_counts),
    }))


if __name__ == "__main__":
    main()
