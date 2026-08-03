#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Verifier for state_machine_trace benchmark.")
    parser.add_argument("--items", "--gold", "-i", type=str, default=None, help="Path to items or gold JSONL file")
    parser.add_argument("--submission", "--predictions", "-s", type=str, default=None, help="Path to submission JSONL file")
    parser.add_argument("--out", "--output", "-o", type=str, default=None, help="Path to output verification report JSON")
    args, unknown = parser.parse_known_args()

    submission_path = args.submission
    if not submission_path and unknown:
        submission_path = unknown[0]

    errors = []
    total_items = 0
    valid_items = 0

    if submission_path and Path(submission_path).exists():
        with open(submission_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                total_items += 1
                try:
                    data = json.loads(line)
                    if not isinstance(data, dict):
                        errors.append(f"Line {idx}: Item is not a JSON object")
                        continue
                    if "item_id" not in data:
                        errors.append(f"Line {idx}: Missing 'item_id'")
                        continue
                    if "prediction" not in data and "answer" not in data:
                        errors.append(f"Line {idx}: Missing 'prediction' or 'answer'")
                        continue
                    valid_items += 1
                except Exception as e:
                    errors.append(f"Line {idx}: Invalid JSON ({str(e)})")

    is_valid = (len(errors) == 0) and (total_items > 0 or submission_path is None)

    report = {
        "valid": is_valid,
        "total_items": total_items,
        "valid_items": valid_items,
        "errors": errors
    }

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
