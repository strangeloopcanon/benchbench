#!/usr/bin/env python3
"""Deterministic exact and component scorer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_rows(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{path}:{line_number}: blank line")
            rows.append(json.loads(line))
    return rows


def indexed(rows, label):
    result = {}
    for row in rows:
        if set(row) != {"id", "answer"}:
            raise ValueError(f"{label} rows must contain exactly id and answer")
        if not isinstance(row["id"], str) or row["id"] in result:
            raise ValueError(f"invalid or duplicate {label} id: {row.get('id')}")
        result[row["id"]] = row["answer"]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    gold = indexed(load_rows(args.gold), "gold")
    predictions = indexed(load_rows(args.predictions), "prediction")
    unknown = sorted(set(predictions) - set(gold))
    if unknown:
        raise ValueError(f"unknown prediction ids: {unknown}")

    exact = record = tick = 0
    per_item = []
    for item_id, expected in gold.items():
        predicted = predictions.get(item_id)
        schema_valid = isinstance(predicted, dict) and set(predicted) == {
            "record_id", "corrected_tick"
        }
        record_ok = schema_valid and predicted["record_id"] == expected["record_id"]
        tick_ok = schema_valid and predicted["corrected_tick"] == expected["corrected_tick"]
        exact_ok = record_ok and tick_ok
        exact += int(exact_ok)
        record += int(record_ok)
        tick += int(tick_ok)
        per_item.append({
            "id": item_id,
            "exact": exact_ok,
            "record_id_correct": record_ok,
            "corrected_tick_correct": tick_ok,
        })

    total = len(gold)
    report = {
        "benchmark": "counterfeit_clock",
        "exact_score": exact,
        "total": total,
        "accuracy": exact / total if total else 0.0,
        "record_id_accuracy": record / total if total else 0.0,
        "corrected_tick_accuracy": tick / total if total else 0.0,
        "missing_prediction_ids": sorted(set(gold) - set(predictions)),
        "per_item": per_item,
    }
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"exact_score": exact, "total": total, "accuracy": report["accuracy"]}, sort_keys=True))


if __name__ == "__main__":
    main()
