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


def extract_id(data: dict) -> str:
    for k in ["id", "item_id", "question_id", "sample_id"]:
        if k in data and data[k] is not None:
            return str(data[k]).strip()
    return ""


def extract_answer(data: dict) -> str:
    for k in ["answer", "prediction", "output", "text", "response", "generated_text", "gold"]:
        if k in data and data[k] is not None:
            return str(data[k]).strip().lower()
    return ""


def main():
    parser = argparse.ArgumentParser(description="RADN Benchmark Scorer")
    parser.add_argument("--gold", "--gold-path", "-g", type=str, required=True, help="Path to gold ground truth jsonl")
    parser.add_argument("--predictions", "--pred", "--predictions-path", "-p", type=str, required=True, help="Path to predictions jsonl")
    parser.add_argument("--out", "--output", "-o", type=str, required=True, help="Path to output score JSON report")
    args = parser.parse_args()

    gold_path = Path(args.gold)
    pred_path = Path(args.predictions)
    out_path = Path(args.out)

    if not gold_path.exists():
        print(f"Error: Gold file not found at {gold_path}", file=sys.stderr)
        sys.exit(1)

    # Load gold answers
    gold_map = {}
    with open(gold_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    g_id = extract_id(data)
                    g_ans = extract_answer(data)
                    if g_id:
                        gold_map[g_id] = g_ans
                except Exception:
                    continue

    total = int(len(gold_map))
    if total == 0:
        print("Error: Gold file contains zero items.", file=sys.stderr)
        sys.exit(1)

    # Load predictions
    pred_map = {}
    if pred_path.exists():
        with open(pred_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        p_id = extract_id(data)
                        p_ans = extract_answer(data)
                        if p_id:
                            pred_map[p_id] = p_ans
                    except Exception:
                        continue

    # Score each item
    correct = 0
    item_results = {}

    for item_id, gold_ans in gold_map.items():
        pred_ans = pred_map.get(item_id, "")
        is_correct = bool(pred_ans and pred_ans == gold_ans)
        if is_correct:
            correct += 1
        item_results[item_id] = {
            "correct": is_correct,
            "gold": gold_ans,
            "prediction": pred_ans
        }

    correct_int = int(correct)
    accuracy_float = float(correct_int / total) if total > 0 else 0.0

    report = {
        "schema_version": 2,
        "benchmark_name": "RADN-Sim",
        "total": total,
        "correct": correct_int,
        "accuracy": accuracy_float,
        "details": item_results
    }

    # Write report
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Scored {total} items: {correct_int}/{total} correct (Accuracy: {accuracy_float:.4f})")
    print(f"Score report saved to {out_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
