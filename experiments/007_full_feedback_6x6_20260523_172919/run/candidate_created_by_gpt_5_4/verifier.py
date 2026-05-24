import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_ANSWER_KEYS = [
    "included_units",
    "earned_royalty_cents",
    "recouped_advance_cents",
    "payable_cents",
]


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--gold", required=True)
    args = ap.parse_args()

    items_path = Path(args.items)
    gold_path = Path(args.gold)
    items = read_jsonl(items_path)
    gold = read_jsonl(gold_path)

    if len(items) != len(gold):
        fail(f"row-count mismatch: items={len(items)} gold={len(gold)}")

    item_ids = sorted(row.get("id") for row in items)
    gold_ids = sorted(row.get("id") for row in gold)
    if item_ids != gold_ids:
        fail(f"id mismatch: items_only={sorted(set(item_ids) - set(gold_ids))} gold_only={sorted(set(gold_ids) - set(item_ids))}")

    base = items_path.parent.resolve()
    for item in items:
        if "assets" not in item or not isinstance(item["assets"], dict):
            fail(f"item missing assets dict: {item.get('id')}")
        for _, rel in item["assets"].items():
            if not isinstance(rel, str):
                fail(f"asset path must be string: {item.get('id')}")
            target = (base / rel).resolve()
            if base not in target.parents and target != base:
                fail(f"asset escapes solver bundle: {item.get('id')} {rel}")
            if not target.exists():
                fail(f"missing asset: {item.get('id')} {rel}")

    for row in gold:
        if sorted(row.keys()) != ["answer", "id"]:
            fail(f"gold row keys wrong for {row.get('id')}: {sorted(row.keys())}")
        answer = row["answer"]
        if not isinstance(answer, dict):
            fail(f"gold answer must be object for {row['id']}")
        if sorted(answer.keys()) != sorted(EXPECTED_ANSWER_KEYS):
            fail(f"gold answer keys wrong for {row['id']}: {sorted(answer.keys())}")
        for key in EXPECTED_ANSWER_KEYS:
            if not isinstance(answer[key], int):
                fail(f"gold answer field {key} must be int for {row['id']}")

    print("OK: items, assets, and gold answers are consistent.")


if __name__ == "__main__":
    main()
