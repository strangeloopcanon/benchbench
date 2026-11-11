#!/usr/bin/env python3
"""Scorer for the Consolidation Point benchmark.

Usage:
    python3 scorer.py --gold gold_private_sample.jsonl \
                      --predictions predictions.jsonl \
                      --out score_report.json

Grading is exact match on a normalised integer.  Normalisation strips
whitespace, thousands separators, an optional currency marker and an optional
trailing unit word, and canonicalises the sign and any leading zeros.  It never
changes the numeric value.  A missing, duplicated or unparseable prediction
scores zero for that item.
"""

import argparse
import json
import re
import sys

INTEGERISH = re.compile(r"^[+-]?[0-9]+(?:\.0*)?$")
UNIT_SUFFIXES = ("marks", "mark")


def normalize_answer(value):
    """Canonicalise an answer for exact-match comparison."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return repr(value)
    text = str(value).strip()
    text = text.replace(",", "").replace("_", "")
    text = re.sub(r"\s+", "", text)
    lowered = text.lower()
    for suffix in UNIT_SUFFIXES:
        if lowered.endswith(suffix) and len(lowered) > len(suffix):
            text = text[: len(text) - len(suffix)]
            break
    text = text.lstrip("$")
    if INTEGERISH.match(text):
        if "." in text:
            text = text.split(".", 1)[0]
        negative = text.startswith("-")
        digits = text[1:] if text[0] in "+-" else text
        digits = digits.lstrip("0")
        if digits == "":
            digits = "0"
        if negative and digits != "0":
            return "-" + digits
        return digits
    return text.lower()


def read_jsonl(path, label):
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                except ValueError as exc:
                    raise SystemExit(
                        "ERROR: %s line %d is not valid JSON: %s" % (label, number, exc)
                    )
                if not isinstance(obj, dict):
                    raise SystemExit(
                        "ERROR: %s line %d is not a JSON object" % (label, number)
                    )
                rows.append(obj)
    except IOError as exc:
        raise SystemExit("ERROR: cannot read %s (%s): %s" % (label, path, exc))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score Consolidation Point predictions.")
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out", default="score_report.json")
    args = parser.parse_args(argv)

    gold_rows = read_jsonl(args.gold, "gold")
    pred_rows = read_jsonl(args.predictions, "predictions")

    gold = {}
    gold_order = []
    for row in gold_rows:
        item_id = row.get("id")
        if item_id is None:
            raise SystemExit("ERROR: a gold row has no id")
        item_id = str(item_id)
        if item_id in gold:
            raise SystemExit("ERROR: duplicate gold id: " + item_id)
        gold[item_id] = normalize_answer(row.get("answer"))
        gold_order.append(item_id)

    predictions = {}
    duplicate_pred_ids = []
    for row in pred_rows:
        item_id = row.get("id")
        if item_id is None:
            continue
        item_id = str(item_id)
        if item_id in predictions:
            duplicate_pred_ids.append(item_id)
        predictions[item_id] = normalize_answer(row.get("answer"))

    duplicate_pred_ids = sorted(set(duplicate_pred_ids))
    unknown_pred_ids = sorted(set(predictions) - set(gold))
    missing_ids = [item_id for item_id in gold_order if item_id not in predictions]

    per_item = []
    correct = 0
    for item_id in gold_order:
        expected = gold[item_id]
        got = predictions.get(item_id)
        is_missing = got is None
        # A duplicated prediction id is treated as unresolved and scores zero.
        is_correct = (
            (not is_missing)
            and (item_id not in duplicate_pred_ids)
            and got == expected
        )
        if is_correct:
            correct += 1
        per_item.append(
            {
                "id": item_id,
                "expected": expected,
                "predicted": "" if is_missing else got,
                "missing": is_missing,
                "correct": is_correct,
            }
        )

    total = len(gold_order)
    accuracy = (correct / total) if total else 0.0

    report = {
        "schema_version": 2,
        "benchmark": "Consolidation Point",
        "benchmark_id": "consolidation-point-v1",
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "incorrect": total - correct,
        "missing_predictions": len(missing_ids),
        "missing_ids": missing_ids,
        "duplicate_prediction_ids": duplicate_pred_ids,
        "unknown_prediction_ids": unknown_pred_ids,
        "gold_file": args.gold,
        "predictions_file": args.predictions,
        "per_item": per_item,
    }

    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    sys.stdout.write(
        "score: %d/%d correct (accuracy %.4f)\n" % (correct, total, accuracy)
    )
    if missing_ids:
        sys.stdout.write("missing predictions for %d item(s)\n" % len(missing_ids))
    if unknown_pred_ids:
        sys.stdout.write("ignored %d unknown prediction id(s)\n" % len(unknown_pred_ids))
    sys.stdout.write("report written to %s\n" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
