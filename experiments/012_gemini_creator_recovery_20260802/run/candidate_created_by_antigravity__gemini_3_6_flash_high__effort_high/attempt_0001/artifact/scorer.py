#!/usr/bin/env python3
"""
Scorer for RADN (Reconfigurable Asynchronous Dataflow Network) Benchmark.
Evaluates predictions against gold ground truth.
Outputs JSON report with schema_version: 2, total, correct, accuracy.
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="RADN Benchmark Scorer")
    parser.add_argument("--gold", type=str, required=True, help="Path to gold ground truth jsonl")
    parser.add_argument("--predictions", type=str, required=True, help="Path to predictions jsonl")
    parser.add_argument("--out", type=str, required=True, help="Path to output score JSON report")
    args = parser.parse_args()

    gold_path = Path(args.gold)
    pred_path = Path(args.predictions)
    out_path = Path(args.out)

    if not gold_path.exists():
        print(f"Error: Gold file not found at {gold_path}", file=sys.stderr)
        sys.exit(1)

    if not pred_path.exists():
        print(f"Error: Predictions file not found at {pred_path}", file=sys.stderr)
        sys.exit(1)

    # Load gold answers
    gold_map = {}
    with open(gold_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                gold_map[data["id"]] = str(data["answer"]).strip().lower()

    total = len(gold_map)
    if total == 0:
        print("Error: Gold file contains zero items.", file=sys.stderr)
        sys.exit(1)

    # Load predictions
    pred_map = {}
    with open(pred_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    pred_map[data["id"]] = str(data["answer"]).strip().lower()
                except Exception:
                    continue

    # Score each item
    correct = 0
    item_results = {}

    for item_id, gold_ans in gold_map.items():
        pred_ans = pred_map.get(item_id, "")
        is_correct = (pred_ans == gold_ans)
        if is_correct:
            correct += 1
        item_results[item_id] = {
            "correct": is_correct,
            "gold": gold_ans,
            "prediction": pred_ans
        }

    accuracy = correct / total if total > 0 else 0.0

    report = {
        "schema_version": 2,
        "benchmark_name": "RADN-Sim",
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "details": item_results
    }

    # Write report
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Scored {total} items: {correct}/{total} correct (Accuracy: {accuracy:.4f})")
    print(f"Score report saved to {out_path}")


if __name__ == "__main__":
    main()
