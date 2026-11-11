#!/usr/bin/env python3
"""Deterministic exact-match scorer for HolonomyWeave."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

INT_RE = re.compile(r"^-?[0-9]+$")


def parse_canonical_int(val: Any) -> tuple[bool, int | None]:
    """Parse an exact integer answer (rejecting booleans and floats)."""
    if isinstance(val, bool):
        return False, None
    if isinstance(val, int):
        return True, val
    if isinstance(val, str):
        s = val.strip()
        if INT_RE.match(s):
            return True, int(s)
    return False, None


def load_jsonl_rows(path: Path, role: str) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"{role} file not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{role} line {line_no}: invalid JSON ({exc})") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"{role} line {line_no}: expected JSON object")
            if set(obj.keys()) != {"id", "answer"}:
                raise ValueError(
                    f"{role} line {line_no}: expected exact keys {{'id', 'answer'}}, got {sorted(obj.keys())}"
                )
            if not isinstance(obj["id"], str) or not obj["id"]:
                raise ValueError(f"{role} line {line_no}: 'id' must be a non-empty string")
            rows.append(obj)
    return rows


def score_predictions(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    gold_rows = load_jsonl_rows(gold_path, "gold")
    gold_map: dict[str, int] = {}
    for row in gold_rows:
        item_id = row["id"]
        if item_id in gold_map:
            raise ValueError(f"Duplicate id in gold file: {item_id}")
        ok, parsed = parse_canonical_int(row["answer"])
        if not ok or parsed is None:
            raise ValueError(f"Gold item {item_id} has non-integer answer: {row['answer']!r}")
        gold_map[item_id] = parsed

    pred_map: dict[str, Any] = {}
    duplicate_prediction_ids: list[str] = []
    unexpected_prediction_ids: list[str] = []
    malformed_prediction_ids: list[str] = []

    if pred_path.is_file():
        with pred_path.open("r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"predictions line {line_no}: invalid JSON ({exc})") from exc
                if not isinstance(obj, dict) or "id" not in obj or "answer" not in obj:
                    raise ValueError(
                        f"predictions line {line_no}: each row must be an object with 'id' and 'answer'"
                    )
                item_id = obj["id"]
                if not isinstance(item_id, str) or not item_id:
                    raise ValueError(f"predictions line {line_no}: 'id' must be a non-empty string")
                if item_id in pred_map:
                    duplicate_prediction_ids.append(item_id)
                pred_map[item_id] = obj["answer"]
                if item_id not in gold_map:
                    unexpected_prediction_ids.append(item_id)
    else:
        raise FileNotFoundError(f"predictions file not found: {pred_path}")

    total = len(gold_map)
    correct = 0
    missing_ids: list[str] = []
    per_tier = {
        "tier1_tractable": {"total": 0, "correct": 0},
        "tier2_intermediate": {"total": 0, "correct": 0},
        "tier3_holonomy": {"total": 0, "correct": 0},
    }

    for idx, (item_id, gold_val) in enumerate(gold_map.items()):
        tier_key = (
            "tier1_tractable"
            if idx < 6
            else ("tier2_intermediate" if idx < 18 else "tier3_holonomy")
        )
        per_tier[tier_key]["total"] += 1
        if item_id not in pred_map:
            missing_ids.append(item_id)
            continue
        ok, pred_val = parse_canonical_int(pred_map[item_id])
        if not ok or pred_val is None:
            malformed_prediction_ids.append(item_id)
            continue
        if pred_val == gold_val:
            correct += 1
            per_tier[tier_key]["correct"] += 1

    accuracy = (correct / total) if total > 0 else 0.0
    return {
        "schema_version": 2,
        "benchmark": "holonomy_weave",
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "missing_count": len(missing_ids),
        "malformed_answer_count": len(malformed_prediction_ids),
        "duplicate_prediction_ids": duplicate_prediction_ids,
        "unexpected_prediction_ids": unexpected_prediction_ids,
        "tier_breakdown": per_tier,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score HolonomyWeave predictions.")
    parser.add_argument("--gold", required=True, type=Path, help="Path to gold JSONL file.")
    parser.add_argument("--predictions", required=True, type=Path, help="Path to predictions JSONL file.")
    parser.add_argument("--out", required=True, type=Path, help="Path to output score_report.json.")
    args = parser.parse_args()

    report = score_predictions(args.gold, args.predictions)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"Scored {report['correct']}/{report['total']} (accuracy={report['accuracy']:.4f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
