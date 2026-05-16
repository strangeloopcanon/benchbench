#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    gold_rows = read_jsonl(args.gold)
    pred_rows = read_jsonl(args.predictions)
    for row in gold_rows:
        if set(row) != {"id", "answer"}:
            raise SystemExit(f"gold rows must contain exactly id and answer: {row}")
    for row in pred_rows:
        if set(row) != {"id", "answer"}:
            raise SystemExit(f"prediction rows must contain exactly id and answer: {row}")
    gold = {r["id"]: r["answer"] for r in gold_rows}
    preds = {r["id"]: r["answer"] for r in pred_rows}
    details = []
    correct = 0
    for gid, ans in gold.items():
        pred = preds.get(gid)
        ok = pred == ans
        correct += int(ok)
        details.append({"id": gid, "gold": ans, "prediction": pred, "correct": ok})
    report = {
        "total": len(gold),
        "correct": correct,
        "accuracy": correct / len(gold) if gold else 0.0,
        "missing_predictions": sorted(set(gold) - set(preds)),
        "extra_predictions": sorted(set(preds) - set(gold)),
        "details": details,
    }
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"SCORED {correct}/{len(gold)}")


if __name__ == "__main__":
    main()
