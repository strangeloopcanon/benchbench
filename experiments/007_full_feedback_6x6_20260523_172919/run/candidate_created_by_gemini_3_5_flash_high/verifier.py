#!/usr/bin/env python3
import os
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=str, required=True)
    parser.add_argument("--gold", type=str, required=True)
    args = parser.parse_args()

    # 1. Check file existence
    if not os.path.exists(args.items):
        print(f"Error: Items file {args.items} not found.")
        return 1
    if not os.path.exists(args.gold):
        print(f"Error: Gold file {args.gold} not found.")
        return 1

    solver_bundle_dir = os.path.dirname(os.path.abspath(args.items))

    # 2. Parse Gold JSONL
    gold_items = {}
    with open(args.gold, "r") as f:
        for idx, line in enumerate(f, 1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Error: Gold file line {idx} is invalid JSON: {e}")
                return 1

            if "id" not in data:
                print(f"Error: Gold file line {idx} has no 'id' field.")
                return 1
            if "answer" not in data:
                print(f"Error: Gold file line {idx} has no 'answer' field.")
                return 1

            item_id = data["id"]
            if item_id in gold_items:
                print(f"Error: Duplicate 'id' {item_id} in gold file.")
                return 1

            answer = data["answer"]
            required_keys = ["customs_duty_usd", "carrier_charges_usd", "reconciliation_flag"]
            for k in required_keys:
                if k not in answer:
                    print(f"Error: Gold answer for {item_id} is missing key: '{k}'")
                    return 1

            if not isinstance(answer["customs_duty_usd"], (int, float)):
                print(f"Error: Gold answer 'customs_duty_usd' for {item_id} must be a number.")
                return 1
            if not isinstance(answer["carrier_charges_usd"], (int, float)):
                print(f"Error: Gold answer 'carrier_charges_usd' for {item_id} must be a number.")
                return 1
            if answer["reconciliation_flag"] not in [
                "HS_RECLASSIFICATION", "INCOTERM_MISMATCH",
                "DEMURRAGE_OVERCHARGE", "CURRENCY_VALUATION_ERROR", "NO_DISCREPANCY"
            ]:
                print(f"Error: Gold answer 'reconciliation_flag' for {item_id} has invalid value: {answer['reconciliation_flag']}")
                return 1

            gold_items[item_id] = answer

    # 3. Parse Items JSONL and Verify Assets
    item_ids = set()
    with open(args.items, "r") as f:
        for idx, line in enumerate(f, 1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Error: Items file line {idx} is invalid JSON: {e}")
                return 1

            if "id" not in data:
                print(f"Error: Items file line {idx} has no 'id' field.")
                return 1
            if "assets" not in data:
                print(f"Error: Items file line {idx} has no 'assets' field.")
                return 1

            item_id = data["id"]
            if item_id in item_ids:
                print(f"Error: Duplicate 'id' {item_id} in items file.")
                return 1
            item_ids.add(item_id)

            # Verify asset path existence and leakage checks
            assets = data["assets"]
            required_assets = ["bill_of_lading", "commercial_invoice", "vessel_port_log", "exchange_rates", "email_correspondence"]
            for ra in required_assets:
                if ra not in assets:
                    print(f"Error: Item {item_id} is missing asset reference: '{ra}'")
                    return 1

            for label, rel_path in assets.items():
                abs_asset_path = os.path.join(solver_bundle_dir, rel_path)
                if not os.path.exists(abs_asset_path):
                    print(f"Error: Item {item_id} references asset {rel_path} that does not exist at {abs_asset_path}")
                    return 1

                # Check for direct answer leak in asset text files
                with open(abs_asset_path, "r") as af:
                    content = af.read()
                    # A robust sanity check to make sure gold answers aren't accidentally written to the text
                    ans = gold_items.get(item_id)
                    if ans:
                        # Convert float values to strings and see if they appear exactly in the email or log
                        # Note: some values could naturally appear (e.g. quantities), but let's check for exact answers
                        # formatted as json.
                        if json.dumps(ans) in content:
                            print(f"Warning: Potential answer leakage detected in {rel_path}")
                            return 1

    # 4. Check matching IDs
    gold_ids = set(gold_items.keys())
    if item_ids != gold_ids:
        print(f"Error: Mismatch between item IDs and gold IDs.")
        print(f"Only in items: {item_ids - gold_ids}")
        print(f"Only in gold: {gold_ids - item_ids}")
        return 1

    print(f"Verification PASSED. {len(item_ids)} items are structurally valid, matched, and consistent.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
