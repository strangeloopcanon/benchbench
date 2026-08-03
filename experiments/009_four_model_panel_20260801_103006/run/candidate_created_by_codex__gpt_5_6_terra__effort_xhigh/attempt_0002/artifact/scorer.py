#!/usr/bin/env python3
"""Strict PAL scorer plus a safe obvious-shortcut baseline emitter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    result = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                result.append(json.loads(line))
    return result


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")


def parse_answer(answer: str) -> dict[str, str] | None:
    parts = answer.split(";")
    if len(parts) != 10:
        return None
    parsed: dict[str, str] = {}
    for index, part in enumerate(parts):
        if "=" not in part:
            return None
        key, value = part.split("=", 1)
        if key != f"q{index:02d}" or key in parsed:
            return None
        halves = value.split(">")
        if len(halves) != 2:
            return None
        for half in halves:
            if "@" not in half:
                return None
            decision, source = half.split("@", 1)
            if decision not in {"A", "D"} or not source or any(char.isspace() for char in source):
                return None
        parsed[key] = value
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--emit-default-baseline", type=Path, help="write the all-default-deny weak baseline and exit")
    args = parser.parse_args()
    gold_rows = load_jsonl(args.gold)
    for row in gold_rows:
        if set(row) != {"id", "answer"}:
            raise SystemExit("gold rows must contain exactly id and answer")
        if parse_answer(row["answer"]) is None:
            raise SystemExit(f"invalid gold answer for {row['id']}")
    if args.emit_default_baseline:
        baseline = ";".join(f"q{i:02d}=D@DEFAULT>D@DEFAULT" for i in range(10))
        write_jsonl(args.emit_default_baseline, [{"id": row["id"], "answer": baseline} for row in gold_rows])
        print(f"wrote {len(gold_rows)} default baseline predictions")
        return
    if args.predictions is None or args.out is None:
        raise SystemExit("--predictions and --out are required unless emitting a baseline")
    predictions = load_jsonl(args.predictions)
    prediction_by_id: dict[str, str] = {}
    malformed_rows = 0
    duplicate_ids = 0
    for row in predictions:
        if set(row) != {"id", "answer"} or not isinstance(row.get("id"), str) or not isinstance(row.get("answer"), str):
            malformed_rows += 1
            continue
        if row["id"] in prediction_by_id:
            duplicate_ids += 1
            continue
        prediction_by_id[row["id"]] = row["answer"]
    strict_correct = 0
    component_correct = 0
    components_total = len(gold_rows) * 10
    item_results = []
    for row in gold_rows:
        predicted = prediction_by_id.get(row["id"])
        gold_parts = parse_answer(row["answer"])
        predicted_parts = parse_answer(predicted) if predicted is not None else None
        correct_parts = 0 if predicted_parts is None else sum(predicted_parts[key] == gold_parts[key] for key in gold_parts)
        exact = predicted == row["answer"]
        strict_correct += int(exact)
        component_correct += correct_parts
        item_results.append({"id": row["id"], "exact": exact, "query_components_correct": correct_parts, "query_components_total": 10})
    report = {
        "benchmark": "Patchwork Access Logic (PAL) v1",
        "items": len(gold_rows),
        "strict_score": strict_correct,
        "strict_score_out_of": len(gold_rows),
        "query_provenance_components_correct": component_correct,
        "query_provenance_components_total": components_total,
        "query_provenance_accuracy": component_correct / components_total if components_total else 0.0,
        "missing_item_ids": [row["id"] for row in gold_rows if row["id"] not in prediction_by_id],
        "extra_item_ids": sorted(set(prediction_by_id) - {row["id"] for row in gold_rows}),
        "malformed_prediction_rows": malformed_rows,
        "duplicate_prediction_ids": duplicate_ids,
        "item_results": item_results,
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"strict {strict_correct}/{len(gold_rows)}; components {component_correct}/{components_total}")


if __name__ == "__main__":
    main()
