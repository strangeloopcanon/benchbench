#!/usr/bin/env python3
"""Deterministic exact and component scorer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _reject_json_constant(value):
    raise ValueError(f"non-standard JSON constant {value}")


def _object_without_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def load_rows(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{path}:{line_number}: blank line")
            rows.append(json.loads(
                line,
                object_pairs_hook=_object_without_duplicate_keys,
                parse_constant=_reject_json_constant,
            ))
    return rows


def indexed(rows, label):
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{label} rows must be JSON objects")
        if set(row) != {"id", "answer"}:
            raise ValueError(f"{label} rows must contain exactly id and answer")
        if not isinstance(row["id"], str) or not row["id"] or row["id"] in result:
            raise ValueError(f"invalid or duplicate {label} id: {row.get('id')}")
        result[row["id"]] = row["answer"]
    return result


def answer_schema_valid(answer):
    return (
        isinstance(answer, dict)
        and set(answer) == {"record_id", "corrected_tick"}
        and isinstance(answer["record_id"], str)
        and bool(answer["record_id"])
        and type(answer["corrected_tick"]) is int
        and answer["corrected_tick"] >= 0
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    gold = indexed(load_rows(args.gold), "gold")
    predictions = indexed(load_rows(args.predictions), "prediction")
    invalid_gold = [item_id for item_id, answer in gold.items() if not answer_schema_valid(answer)]
    if invalid_gold:
        raise ValueError(f"invalid gold answer schema for ids: {invalid_gold}")
    unknown = sorted(set(predictions) - set(gold))
    if unknown:
        raise ValueError(f"unknown prediction ids: {unknown}")

    exact = record = tick = 0
    per_item = []
    for item_id, expected in gold.items():
        predicted = predictions.get(item_id)
        schema_valid = answer_schema_valid(predicted)
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
