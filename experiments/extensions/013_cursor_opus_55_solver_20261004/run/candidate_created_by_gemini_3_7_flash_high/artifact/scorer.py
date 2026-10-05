#!/usr/bin/env python3
"""
CloudSLA-Forensics Scorer
Evaluates predictions against ground truth gold answers with robust type normalization,
exact integer cent matching, diagnostic breakdowns, and outputs schema_version 2 report.
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, Optional, Tuple


def normalize_answer(val: Any) -> Optional[int]:
    """
    Normalizes diverse prediction answer formats into exact integer USD cents.
    Handles:
    - int (e.g. 185000)
    - string integer (e.g. "185000")
    - dollar string (e.g. "$1,850.00" -> 185000)
    - float (e.g. 1850.0 -> 185000 if interpreted as dollars, or 185000.0)
    - dict (e.g. {"answer": 185000} or {"net_credit_cents": 185000})
    """
    if val is None:
        return None

    if isinstance(val, int):
        return val

    if isinstance(val, float):
        # Check if it represents cents directly or whole dollars
        if val.is_integer():
            return int(val)
        # Decimal dollars to cents
        return int(round(val * 100))

    if isinstance(val, dict):
        for key in ["net_credit_cents", "answer", "net_credit", "credit_cents", "value"]:
            if key in val:
                return normalize_answer(val[key])
        return None

    if isinstance(val, str):
        cleaned = val.strip().replace(",", "")
        # Check for dollar sign
        if cleaned.startswith("$"):
            cleaned = cleaned[1:].strip()
            try:
                dollars = float(cleaned)
                return int(round(dollars * 100))
            except ValueError:
                pass
        
        # Check if float with decimal dot
        if "." in cleaned:
            try:
                num = float(cleaned)
                # If 2 decimal places, likely dollar float
                parts = cleaned.split(".")
                if len(parts[1]) == 2:
                    return int(round(num * 100))
                if num.is_integer():
                    return int(num)
            except ValueError:
                pass

        # Try direct integer
        try:
            return int(cleaned)
        except ValueError:
            # Extract first continuous integer
            match = re.search(r"\b\d+\b", cleaned)
            if match:
                try:
                    return int(match.group(0))
                except ValueError:
                    pass

    return None


def main():
    parser = argparse.ArgumentParser(description="CloudSLA-Forensics Scorer")
    parser.add_argument("--gold", type=str, required=True, help="Path to gold_private_sample.jsonl")
    parser.add_argument("--predictions", type=str, required=True, help="Path to predictions.jsonl")
    parser.add_argument("--out", type=str, default="score_report.json", help="Path to output score_report.json")
    args = parser.parse_args()

    gold_path = os.path.abspath(args.gold)
    pred_path = os.path.abspath(args.predictions)
    out_path = os.path.abspath(args.out)

    if not os.path.exists(gold_path):
        print(f"Error: Gold file not found: {gold_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(pred_path):
        print(f"Error: Predictions file not found: {pred_path}", file=sys.stderr)
        sys.exit(1)

    # Load gold
    gold_map: Dict[str, int] = {}
    with open(gold_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            gold_map[entry["id"]] = entry["answer"]

    # Load predictions
    pred_map: Dict[str, Any] = {}
    with open(pred_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if "id" in entry:
                    pred_map[entry["id"]] = entry.get("answer")
            except Exception:
                continue

    total = len(gold_map)
    correct = 0
    item_results = []

    for item_id, gold_val in gold_map.items():
        raw_pred = pred_map.get(item_id)
        norm_pred = normalize_answer(raw_pred)

        is_match = (norm_pred is not None and norm_pred == gold_val)
        if is_match:
            correct += 1

        diff = None
        if norm_pred is not None:
            diff = norm_pred - gold_val

        item_results.append({
            "id": item_id,
            "gold_answer_cents": gold_val,
            "pred_raw": raw_pred,
            "pred_normalized_cents": norm_pred,
            "correct": is_match,
            "difference_cents": diff
        })

    accuracy = (correct / total) if total > 0 else 0.0

    score_report = {
        "schema_version": 2,
        "benchmark_name": "CloudSLA-Forensics",
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "matched_ratio": f"{correct}/{total}",
        "details": item_results
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(score_report, f, indent=2)

    print(f"Scoring complete: {correct}/{total} correct ({accuracy:.4f} accuracy).")
    print(f"Score report saved to: {out_path}")


if __name__ == "__main__":
    main()
