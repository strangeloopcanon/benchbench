import json
import argparse

def score(gold_path, predictions_path, out_path):
    with open(gold_path, 'r') as f:
        golds = {}
        for line in f:
            obj = json.loads(line)
            golds[obj["id"]] = obj["answer"]

    preds = {}
    if predictions_path:
        with open(predictions_path, 'r') as f:
            for line in f:
                obj = json.loads(line)
                pred = obj.get("answer", obj.get("prediction", {}))
                if isinstance(pred, str):
                    try:
                        parsed = json.loads(pred)
                    except json.JSONDecodeError:
                        parsed = {}
                    pred = parsed if isinstance(parsed, dict) else {}
                preds[obj["id"]] = pred if isinstance(pred, dict) else {}

    total_tenants = 0
    correct_tenants = 0
    correct_items = 0

    for item_id, gold_dict in golds.items():
        pred_dict = preds.get(item_id, {})
        item_correct = True
        for tenant, gold_val in gold_dict.items():
            total_tenants += 1
            # Exact match on cents
            if str(pred_dict.get(tenant, "")) == str(gold_val):
                correct_tenants += 1
            else:
                item_correct = False
        if item_correct and set(pred_dict) == set(gold_dict):
            correct_items += 1

    # Scale to 0.0-1.0
    total_items = len(golds)
    final_score = (correct_items / total_items) if total_items > 0 else 0.0

    report = {
        "total": total_items,
        "correct": correct_items,
        "accuracy": final_score,
        "metrics": {
            "total_items": total_items,
            "correct_items": correct_items,
            "total_tenants_evaluated": total_tenants,
            "correct_tenants": correct_tenants,
            "accuracy": correct_tenants / total_tenants if total_tenants > 0 else 0
        }
    }

    with open(out_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Scored {correct_items}/{total_items} items correct; {correct_tenants}/{total_tenants} tenant values correct.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    score(args.gold, args.predictions, args.out)
