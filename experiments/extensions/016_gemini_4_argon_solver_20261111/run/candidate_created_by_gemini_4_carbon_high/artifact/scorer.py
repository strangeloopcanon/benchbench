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


def load_gold_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"gold file not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"gold line {line_no}: invalid JSON ({exc})") from exc
            if not isinstance(obj, dict) or "id" not in obj or "answer" not in obj:
                raise ValueError(f"gold line {line_no}: expected JSON object with 'id' and 'answer'")
            if not isinstance(obj["id"], str) or not obj["id"]:
                raise ValueError(f"gold line {line_no}: 'id' must be a non-empty string")
            rows.append(obj)
    return rows


def extract_pred_value(obj: dict[str, Any]) -> tuple[bool, Any]:
    for key in ("answer", "prediction", "output", "response"):
        if key in obj:
            return True, obj[key]
    return False, None


def score_predictions(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    gold_rows = load_gold_rows(gold_path)
    gold_map: dict[str, int] = {}
    for row in gold_rows:
        item_id = row["id"]
        if item_id in gold_map:
            raise ValueError(f"Duplicate id in gold file: {item_id}")
        ok, parsed = parse_canonical_int(row["answer"])
        if not ok or parsed is None:
            raise ValueError(f"Gold item {item_id} has non-integer answer: {row['answer']!r}")
        gold_map[item_id] = parsed

    if not pred_path.is_file():
        raise FileNotFoundError(f"predictions file not found: {pred_path}")

    pred_map: dict[str, Any] = {}
    duplicate_prediction_ids: list[str] = []
    unexpected_prediction_ids: list[str] = []
    malformed_prediction_ids: list[str] = []

    with pred_path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                malformed_prediction_ids.append(f"<line_{line_no}>")
                continue
            if not isinstance(obj, dict):
                malformed_prediction_ids.append(f"<line_{line_no}>")
                continue
            item_id = obj.get("id")
            if not isinstance(item_id, str) or not item_id:
                malformed_prediction_ids.append(f"<line_{line_no}>")
                continue
            if item_id in pred_map:
                duplicate_prediction_ids.append(item_id)
            has_val, raw_val = extract_pred_value(obj)
            if not has_val:
                malformed_prediction_ids.append(item_id)
                continue
            pred_map[item_id] = raw_val
            if item_id not in gold_map:
                unexpected_prediction_ids.append(item_id)

    total = int(len(gold_map))
    correct = 0
    missing_ids: list[str] = []

    t1_cut = max(1, total // 5) if total > 0 else 0
    t2_cut = max(2, (3 * total) // 5) if total > 0 else 0
    per_tier = {
        "tier1_tractable": {"total": 0, "correct": 0},
        "tier2_intermediate": {"total": 0, "correct": 0},
        "tier3_holonomy": {"total": 0, "correct": 0},
    }

    for idx, (item_id, gold_val) in enumerate(gold_map.items()):
        tier_key = (
            "tier1_tractable"
            if idx < t1_cut
            else ("tier2_intermediate" if idx < t2_cut else "tier3_holonomy")
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

    correct = int(correct)
    accuracy = float(correct / total) if total > 0 else 0.0
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
    parser.add_argument(
        "--gold",
        "-g",
        type=Path,
        default=None,
        help="Path to gold JSONL file.",
    )
    parser.add_argument(
        "--predictions",
        "--pred",
        "--preds",
        "-p",
        dest="predictions",
        type=Path,
        default=None,
        help="Path to predictions JSONL file.",
    )
    parser.add_argument(
        "--items",
        "-i",
        type=Path,
        default=None,
        help="Optional path to items JSONL file.",
    )
    parser.add_argument(
        "--out",
        "--output",
        "-o",
        dest="out",
        type=Path,
        default=None,
        help="Optional path to output score_report.json.",
    )
    parser.add_argument(
        "positional",
        nargs="*",
        type=Path,
        help="Optional positional [gold_path predictions_path [out_path]].",
    )
    args = parser.parse_args()

    gold_path = args.gold
    pred_path = args.predictions
    out_path = args.out

    pos = list(args.positional)
    if gold_path is None and pos:
        gold_path = pos.pop(0)
    if pred_path is None and pos:
        pred_path = pos.pop(0)
    if out_path is None and pos:
        out_path = pos.pop(0)

    if gold_path is None:
        gold_path = Path("gold_private_sample.jsonl")
    if pred_path is None:
        parser.error("the following arguments are required: --predictions")

    report = score_predictions(gold_path, pred_path)
    payload = json.dumps(report, indent=2, sort_keys=False)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload + "\n")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
