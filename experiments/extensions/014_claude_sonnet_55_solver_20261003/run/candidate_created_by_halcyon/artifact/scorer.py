#!/usr/bin/env python3
"""Deterministic exact-match scorer for Maritime General Average & Salvage Forensics (MGAF).

CLI Contract:
  python3.12 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


ID_KEYS = ("id", "item_id", "case_id", "question_id", "task_id")
ANSWER_KEYS = (
    "answer",
    "prediction",
    "pred",
    "output",
    "response",
    "value",
    "result",
    "assessment_cents",
    "gold",
)


def normalize_int_cents(val: Any) -> int | None:
    """Parse an integer USD-cents prediction strictly without bool coercion."""
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val) if val.is_integer() else None
    if isinstance(val, str):
        cleaned = val.strip().replace(",", "").replace("_", "")
        if cleaned.upper().startswith("USD"):
            cleaned = cleaned[3:].strip()
        if cleaned.startswith("$"):
            cleaned = cleaned[1:].strip()
        if re.fullmatch(r"[+-]?\d+", cleaned):
            return int(cleaned)
        if re.fullmatch(r"[+-]?\d+\.0+", cleaned):
            return int(cleaned.split(".", 1)[0])
        # Fallback: extract last standalone integer if embedded in short text
        matches = re.findall(r"(?<!\d)-?\d+(?!\d)", cleaned)
        if len(matches) == 1:
            return int(matches[0])
    if isinstance(val, dict):
        for k in ANSWER_KEYS:
            if k in val:
                return normalize_int_cents(val[k])
    return None


def extract_id(row: dict[str, Any]) -> str | None:
    for k in ID_KEYS:
        val = row.get(k)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def extract_answer(row: dict[str, Any]) -> int | None:
    for k in ANSWER_KEYS:
        if k in row:
            return normalize_int_cents(row[k])
    return None


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    # Try parsing as full JSON document first if it starts with '[' or '{' and is single-block
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            out: list[dict[str, Any]] = []
            for idx, elem in enumerate(parsed):
                if isinstance(elem, dict):
                    out.append(elem)
                else:
                    out.append({"id": f"mgaf_{idx + 1:02d}", "answer": elem})
            return out
        if isinstance(parsed, dict):
            if any(k in parsed for k in ID_KEYS) and any(k in parsed for k in ANSWER_KEYS):
                return [parsed]
            if "predictions" in parsed and isinstance(parsed["predictions"], list):
                return [x for x in parsed["predictions"] if isinstance(x, dict)]
            return [{"id": str(k), "answer": v} for k, v in parsed.items()]
    except Exception:
        pass

    rows: list[dict[str, Any]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        obj = json.loads(line)
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def score_predictions(gold_path: Path, predictions_path: Path) -> dict[str, Any]:
    gold_rows = load_records(gold_path)
    pred_rows = load_records(predictions_path) if predictions_path.exists() else []

    gold_order: list[tuple[str, int]] = []
    for idx, row in enumerate(gold_rows):
        gid = extract_id(row) or f"mgaf_{idx + 1:02d}"
        gans = extract_answer(row)
        if gans is None:
            raise ValueError(f"Invalid gold answer for {gid} in {gold_path}")
        gold_order.append((gid, gans))

    pred_by_id: dict[str, int | None] = {}
    unkeyed_preds: list[int | None] = []
    for row in pred_rows:
        pid = extract_id(row)
        pans = extract_answer(row)
        if pid is not None:
            pred_by_id[pid] = pans
        else:
            unkeyed_preds.append(pans)

    total = len(gold_order)
    correct = 0
    unanswered = 0
    per_item: list[dict[str, Any]] = []

    for idx, (gid, gans) in enumerate(gold_order):
        if gid in pred_by_id:
            pans = pred_by_id[gid]
        elif idx < len(unkeyed_preds) and not pred_by_id:
            pans = unkeyed_preds[idx]
        else:
            pans = None

        if pans is None:
            unanswered += 1
            is_correct = False
        else:
            is_correct = int(pans) == int(gans)

        if is_correct:
            correct += 1

        per_item.append(
            {
                "id": gid,
                "gold": gans,
                "prediction": pans,
                "correct": is_correct,
            }
        )

    accuracy = (correct / total) if total > 0 else 0.0
    return {
        "schema_version": 2,
        "total": int(total),
        "correct": int(correct),
        "accuracy": float(accuracy),
        "unanswered": int(unanswered),
        "per_item": per_item,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score predictions against MGAF gold answers.")
    parser.add_argument(
        "--gold",
        "--gold-file",
        "--gold-path",
        "--answer-key",
        "--answers",
        "--reference",
        "--ground-truth",
        "--target",
        "-g",
        dest="gold",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--predictions",
        "--predictions-file",
        "--predictions-path",
        "--preds",
        "--pred",
        "--submission",
        "--input",
        "--responses",
        "-p",
        dest="predictions",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--items",
        "--items-file",
        "--items-path",
        dest="items",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--out",
        "--output",
        "--out-file",
        "--output-file",
        "--report",
        "--report-file",
        "--score-file",
        "-o",
        dest="out",
        type=str,
        default=None,
    )
    args, positional = parser.parse_known_args()

    gold_arg = args.gold
    pred_arg = args.predictions
    out_arg = args.out

    if positional:
        if len(positional) == 1:
            if pred_arg is None:
                pred_arg = positional[0]
            elif gold_arg is None:
                gold_arg = positional[0]
        elif len(positional) >= 2:
            p0, p1 = positional[0], positional[1]
            if gold_arg is None and pred_arg is None:
                if "gold" in Path(p1).name.lower() and "gold" not in Path(p0).name.lower():
                    pred_arg, gold_arg = p0, p1
                else:
                    gold_arg, pred_arg = p0, p1
            elif gold_arg is None:
                gold_arg = p0
            elif pred_arg is None:
                pred_arg = p0
            if len(positional) >= 3 and out_arg is None:
                out_arg = positional[2]

    gold_path = Path(gold_arg) if gold_arg else Path("gold_private_sample.jsonl")
    predictions_path = Path(pred_arg) if pred_arg else Path("predictions.jsonl")

    report = score_predictions(gold_path=gold_path, predictions_path=predictions_path)
    serialized = json.dumps(report, indent=2) + "\n"
    if out_arg:
        Path(out_arg).write_text(serialized, encoding="utf-8")
    sys.stdout.write(serialized)


if __name__ == "__main__":
    main()
