#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

def normalize_registers(val):
    if isinstance(val, dict):
        try:
            norm_dict = {str(k).strip(): int(v) for k, v in val.items()}
            return json.dumps(norm_dict, sort_keys=True)
        except Exception:
            return str(val)
    if isinstance(val, str):
        val_str = val.strip()
        try:
            parsed = json.loads(val_str)
            if isinstance(parsed, dict):
                norm_dict = {str(k).strip(): int(v) for k, v in parsed.items()}
                return json.dumps(norm_dict, sort_keys=True)
        except Exception:
            pass
        return val_str
    return str(val)

def main():
    parser = argparse.ArgumentParser(description="Scorer for state_machine_trace benchmark.")
    parser.add_argument("--gold", "--ground-truth", "--items", type=str, default="gold_private_sample.jsonl", help="Path to gold JSONL file")
    parser.add_argument("--submission", "--predictions", type=str, default=None, help="Path to submission JSONL file")
    parser.add_argument("--out", "--output", type=str, default=None, help="Path to output score JSON file")
    args, unknown = parser.parse_known_args()

    gold_path = args.gold
    submission_path = args.submission
    out_path = args.out

    # Fallback positional parsing if flags not specified
    if not submission_path and len(unknown) >= 1:
        submission_path = unknown[0]
    if not out_path and len(unknown) >= 2:
        out_path = unknown[1]

    # Load gold items
    gold_map = {}
    if Path(gold_path).exists():
        with open(gold_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    item_id = item.get("item_id")
                    target = item.get("target") or item.get("gold_registers")
                    if item_id:
                        gold_map[item_id] = target
                except Exception:
                    pass

    # Load submission items
    pred_map = {}
    if submission_path and Path(submission_path).exists():
        with open(submission_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    item_id = item.get("item_id")
                    pred = item.get("prediction") if "prediction" in item else item.get("answer")
                    if item_id:
                        pred_map[item_id] = pred
                except Exception:
                    pass

    total = len(gold_map)
    correct = 0
    details = []

    for item_id, gold_target in gold_map.items():
        norm_gold = normalize_registers(gold_target)
        raw_pred = pred_map.get(item_id, None)
        norm_pred = normalize_registers(raw_pred) if raw_pred is not None else None

        is_correct = (raw_pred is not None) and (norm_gold == norm_pred)
        if is_correct:
            correct += 1

        details.append({
            "item_id": item_id,
            "correct": is_correct,
            "gold": norm_gold,
            "prediction": norm_pred
        })

    accuracy = float(correct) / float(total) if total > 0 else 0.0

    result = {
        "schema_version": 2,
        "total": int(total),
        "correct": int(correct),
        "accuracy": float(accuracy),
        "details": details
    }

    if out_path:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
