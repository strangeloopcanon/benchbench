#!/usr/bin/env python3
"""Exact item-level scorer for CFPS predictions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    result = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{path}:{number}: blank line")
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{number}: expected object")
        result.append(value)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Score CFPS predictions exactly")
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    gold = read_jsonl(args.gold)
    predictions = read_jsonl(args.predictions)
    if any(set(row) != {"id", "answer"} or not isinstance(row["id"], str) or not isinstance(row["answer"], str) for row in gold):
        raise SystemExit("malformed gold rows")
    if any(set(row) != {"id", "answer"} or not isinstance(row["id"], str) or not isinstance(row["answer"], str) for row in predictions):
        raise SystemExit("prediction rows must contain exactly id and answer")
    gold_by_id = {row["id"]: row["answer"] for row in gold}
    pred_by_id = {row["id"]: row["answer"] for row in predictions}
    if len(gold_by_id) != len(gold) or len(pred_by_id) != len(predictions):
        raise SystemExit("duplicate IDs are not permitted")
    unknown = sorted(set(pred_by_id) - set(gold_by_id))
    if unknown:
        raise SystemExit("prediction contains unknown IDs: " + ",".join(unknown))
    correct_ids = [row["id"] for row in gold if pred_by_id.get(row["id"]) == row["answer"]]
    report = {
        "schema_version": 2,
        "total": len(gold),
        "correct": len(correct_ids),
        "accuracy": len(correct_ids) / len(gold),
        "missing_prediction_ids": [row["id"] for row in gold if row["id"] not in pred_by_id],
        "correct_ids": correct_ids,
    }
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total": report["total"], "correct": report["correct"], "accuracy": report["accuracy"]}))


if __name__ == "__main__":
    main()
