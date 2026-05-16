#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple


def _read_jsonl_exact_keys(path: Path, required_keys: Tuple[str, str]) -> List[dict]:
    rows: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if set(obj.keys()) != set(required_keys):
                raise SystemExit(f"Row keys must be exactly {set(required_keys)} in {path}: {obj.keys()}")
            rows.append(obj)
    return rows


def _normalize_answer(ans: str) -> str:
    # Parse as JSON array of strings, sort, and dump compactly.
    try:
        arr = json.loads(ans)
    except Exception as e:
        raise ValueError(f"answer is not valid JSON: {e}")
    if not isinstance(arr, list) or not all(isinstance(x, str) for x in arr):
        raise ValueError("answer must be a JSON array of strings")
    arr_sorted = sorted(arr)
    return json.dumps(arr_sorted, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=str, required=True)
    ap.add_argument("--predictions", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    args = ap.parse_args()

    gold_rows = _read_jsonl_exact_keys(Path(args.gold), ("id", "answer"))
    pred_rows = _read_jsonl_exact_keys(Path(args.predictions), ("id", "answer"))

    gold_map: Dict[str, str] = {r["id"]: r["answer"] for r in gold_rows}
    if len(gold_map) != len(gold_rows):
        raise SystemExit("Duplicate gold ids found.")

    pred_map: Dict[str, str] = {r["id"]: r["answer"] for r in pred_rows}
    if len(pred_map) != len(pred_rows):
        raise SystemExit("Duplicate prediction ids found.")

    missing = sorted(set(gold_map.keys()) - set(pred_map.keys()))
    extra = sorted(set(pred_map.keys()) - set(gold_map.keys()))

    correct = 0
    total = len(gold_map)
    per_item: List[dict] = []
    invalid_answers: List[str] = []

    for item_id in sorted(gold_map.keys()):
        if item_id not in pred_map:
            per_item.append({"id": item_id, "correct": False, "reason": "missing_prediction"})
            continue
        gold_norm = _normalize_answer(gold_map[item_id])
        try:
            pred_norm = _normalize_answer(pred_map[item_id])
        except Exception as e:
            invalid_answers.append(item_id)
            per_item.append({"id": item_id, "correct": False, "reason": f"invalid_answer:{e}"})
            continue
        ok = pred_norm == gold_norm
        if ok:
            correct += 1
        per_item.append({"id": item_id, "correct": ok})

    report = {
        "total": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
        "missing_predictions": missing,
        "extra_predictions": extra,
        "invalid_answer_ids": invalid_answers,
        "per_item": per_item,
    }
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"accuracy": report["accuracy"], "correct": correct, "total": total}))


if __name__ == "__main__":
    main()

