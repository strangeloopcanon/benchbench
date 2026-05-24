#!/usr/bin/env python3
"""
Scorer for CPPC benchmark predictions.

Compares solver predictions to gold answers. An answer is correct if the
predicted integer matches the gold integer exactly.

CLI: python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
"""

import argparse
import json
import sys


def normalize_answer(raw_answer) -> int | None:
    """
    Attempt to normalize a prediction to an integer (cents).
    Accepts: int, float (truncated if .0), or string representations thereof.
    Returns None if the answer cannot be parsed.
    """
    if raw_answer is None:
        return None

    if isinstance(raw_answer, int):
        return raw_answer

    if isinstance(raw_answer, float):
        if raw_answer == int(raw_answer):
            return int(raw_answer)
        return None

    if isinstance(raw_answer, str):
        s = raw_answer.strip().replace(",", "").replace("$", "")
        # Handle negative sign
        try:
            val = float(s)
            # Accept if it's effectively an integer
            if val == int(val):
                return int(val)
            # Also accept if within 0.5 cents (rounding artifact)
            rounded = round(val)
            if abs(val - rounded) < 0.01:
                return rounded
            return None
        except (ValueError, OverflowError):
            return None

    return None


def main():
    parser = argparse.ArgumentParser(description="Score CPPC predictions")
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Load gold
    gold = {}
    with open(args.gold) as f:
        for line in f:
            row = json.loads(line)
            gold[row["id"]] = row["answer"]

    # Load predictions
    predictions = {}
    with open(args.predictions) as f:
        for line in f:
            row = json.loads(line)
            predictions[row["id"]] = row.get("answer")

    # Score
    correct = 0
    total = len(gold)
    details = []

    for item_id in sorted(gold.keys()):
        expected = gold[item_id]
        raw_pred = predictions.get(item_id)
        normalized = normalize_answer(raw_pred)

        is_correct = (normalized is not None and normalized == expected)
        if is_correct:
            correct += 1

        details.append({
            "id": item_id,
            "expected": expected,
            "predicted_raw": raw_pred,
            "predicted_normalized": normalized,
            "correct": is_correct,
        })

    score_report = {
        "correct": correct,
        "total": total,
        "score": f"{correct}/{total}",
        "accuracy": round(correct / total, 4) if total > 0 else 0.0,
        "details": details,
    }

    with open(args.out, "w") as f:
        json.dump(score_report, f, indent=2)

    print(f"Score: {correct}/{total} ({score_report['accuracy']*100:.1f}%)")
    sys.exit(0)


if __name__ == "__main__":
    main()
