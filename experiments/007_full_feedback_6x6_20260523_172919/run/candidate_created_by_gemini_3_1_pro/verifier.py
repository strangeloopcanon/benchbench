import json
import argparse
import os

def verify(items_path, gold_path):
    with open(items_path, 'r') as f:
        items = [json.loads(line) for line in f]

    with open(gold_path, 'r') as f:
        golds = {json.loads(line)["id"]: json.loads(line) for line in f}

    assert len(items) == len(golds), "Mismatch in item counts"

    for item in items:
        item_id = item["id"]
        assert item_id in golds, f"Missing gold for {item_id}"

        folder = item["folder"]
        full_folder_path = os.path.join(os.path.dirname(items_path), folder)

        assert os.path.isdir(full_folder_path), f"Missing folder {full_folder_path}"

        required_files = ["property_data.json", "rent_roll.csv", "expenses_ledger.csv", "communications.txt", "lease_manual.md"]
        for rf in required_files:
            rf_path = os.path.join(full_folder_path, rf)
            assert os.path.isfile(rf_path), f"Missing file {rf_path}"

        gold = golds[item_id]["answer"]
        assert isinstance(gold, dict), f"Gold answer for {item_id} must be a dict"
        for k, v in gold.items():
            assert isinstance(v, int), f"Gold answer values must be ints, found {type(v)} for {k}"

    print("Verification passed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", required=True)
    parser.add_argument("--gold", required=True)
    args = parser.parse_args()
    verify(args.items, args.gold)
