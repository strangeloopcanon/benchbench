#!/usr/bin/env python3
import os
import json
import argparse

def float_match(pred, gold, tol=0.05):
    try:
        val_pred = float(pred)
        val_gold = float(gold)
        return abs(val_pred - val_gold) <= tol
    except (ValueError, TypeError):
        return False

def string_match(pred, gold):
    if not isinstance(pred, str) or not isinstance(gold, str):
        return False
    return pred.strip().upper() == gold.strip().upper()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=str, required=True)
    parser.add_argument("--predictions", type=str, required=True)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    # 1. Load Gold
    gold_data = {}
    if not os.path.exists(args.gold):
        print(f"Error: Gold file {args.gold} not found.")
        return 1

    with open(args.gold, "r") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                gold_data[data["id"]] = data["answer"]
            except Exception as e:
                print(f"Error parsing gold file line {idx}: {e}")
                return 1

    # 2. Load Predictions
    predictions_data = {}
    if os.path.exists(args.predictions):
        with open(args.predictions, "r") as f:
            for idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Support both nested {"id": "item_001", "answer": {...}}
                    # and flat structures for robustness
                    pred_answer = data.get("answer", data)
                    predictions_data[data["id"]] = pred_answer
                except Exception as e:
                    print(f"Warning parsing predictions file line {idx}: {e}")

    # 3. Grade
    detailed_results = []
    correct_count = 0
    total_count = len(gold_data)

    duty_correct = 0
    charges_correct = 0
    flag_correct = 0

    for item_id, gold_ans in sorted(gold_data.items()):
        pred_ans = predictions_data.get(item_id)

        item_status = {
            "id": item_id,
            "customs_duty": {"gold": gold_ans.get("customs_duty_usd"), "pred": None, "correct": False},
            "carrier_charges": {"gold": gold_ans.get("carrier_charges_usd"), "pred": None, "correct": False},
            "reconciliation_flag": {"gold": gold_ans.get("reconciliation_flag"), "pred": None, "correct": False},
            "item_correct": False
        }

        if isinstance(pred_ans, str):
            try:
                parsed_pred = json.loads(pred_ans)
            except json.JSONDecodeError:
                parsed_pred = None
            pred_ans = parsed_pred if isinstance(parsed_pred, dict) else None

        if isinstance(pred_ans, dict):
            pred_duty = pred_ans.get("customs_duty_usd")
            pred_charges = pred_ans.get("carrier_charges_usd")
            pred_flag = pred_ans.get("reconciliation_flag")

            item_status["customs_duty"]["pred"] = pred_duty
            item_status["carrier_charges"]["pred"] = pred_charges
            item_status["reconciliation_flag"]["pred"] = pred_flag

            # Match checks
            duty_ok = float_match(pred_duty, gold_ans.get("customs_duty_usd"))
            charges_ok = float_match(pred_charges, gold_ans.get("carrier_charges_usd"))
            flag_ok = string_match(pred_flag, gold_ans.get("reconciliation_flag"))

            item_status["customs_duty"]["correct"] = duty_ok
            item_status["carrier_charges"]["correct"] = charges_ok
            item_status["reconciliation_flag"]["correct"] = flag_ok

            if duty_ok:
                duty_correct += 1
            if charges_ok:
                charges_correct += 1
            if flag_ok:
                flag_correct += 1

            if duty_ok and charges_ok and flag_ok:
                item_status["item_correct"] = True
                correct_count += 1
        else:
            # Missing prediction
            pass

        detailed_results.append(item_status)

    # 4. Construct Output Report
    accuracy = correct_count / total_count if total_count > 0 else 0.0
    report = {
        "accuracy": accuracy,
        "correct": correct_count,
        "total": total_count,
        "metrics": {
            "total_items": total_count,
            "correct_items": correct_count,
            "customs_duty_accuracy": duty_correct / total_count if total_count > 0 else 0.0,
            "carrier_charges_accuracy": charges_correct / total_count if total_count > 0 else 0.0,
            "reconciliation_flag_accuracy": flag_correct / total_count if total_count > 0 else 0.0,
        },
        "results": detailed_results
    }

    # Ensure out directory exists
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Scoring completed. Accuracy: {correct_count}/{total_count} ({accuracy:.2%})")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
