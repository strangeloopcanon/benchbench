#!/usr/bin/env python3
"""
Verifier for CPPC benchmark items.

Recomputes gold answers from item data and checks consistency.

CLI: python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
"""

import argparse
import json
import sys

from generator import compute_certified_amount


def main():
    parser = argparse.ArgumentParser(description="Verify CPPC benchmark items")
    parser.add_argument("--items", required=True, help="Path to solver items JSONL")
    parser.add_argument("--gold", required=True, help="Path to gold answers JSONL")
    args = parser.parse_args()

    # Load items
    items = {}
    with open(args.items) as f:
        for line in f:
            item = json.loads(line)
            items[item["id"]] = item

    # Load gold
    gold = {}
    with open(args.gold) as f:
        for line in f:
            row = json.loads(line)
            gold[row["id"]] = row["answer"]

    # Verify
    errors = []
    for item_id, item_data in sorted(items.items()):
        if item_id not in gold:
            errors.append(f"{item_id}: missing from gold file")
            continue

        recomputed = compute_certified_amount(item_data)
        expected = gold[item_id]

        if recomputed != expected:
            errors.append(
                f"{item_id}: recomputed={recomputed} vs gold={expected} "
                f"(diff={recomputed - expected})"
            )

    # Check for gold IDs not in items
    for gid in gold:
        if gid not in items:
            errors.append(f"{gid}: in gold but missing from items")

    if errors:
        print(f"VERIFICATION FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print(f"VERIFICATION PASSED: {len(items)} items verified, all gold answers match.")
        sys.exit(0)


if __name__ == "__main__":
    main()
