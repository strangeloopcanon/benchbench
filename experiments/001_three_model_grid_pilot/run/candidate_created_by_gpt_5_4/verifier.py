#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path} line {line_number}: invalid JSON: {exc}") from exc
    return rows


def verify_gold_rows(rows):
    ids = set()
    for row in rows:
        if set(row.keys()) != {"id", "answer"}:
            raise ValueError("Gold rows must contain exactly id and answer")
        if row["id"] in ids:
            raise ValueError(f"Duplicate gold id: {row['id']}")
        if row["answer"] not in {"A", "B", "C", "D"}:
            raise ValueError(f"Invalid gold answer for {row['id']}: {row['answer']}")
        ids.add(row["id"])
    return ids


def verify_item_rows(rows, solver_bundle: Path):
    ids = set()
    for row in rows:
        expected = {"id", "image", "prompt"}
        if set(row.keys()) != expected:
            raise ValueError("Item rows must contain exactly id, image, and prompt")
        if row["id"] in ids:
            raise ValueError(f"Duplicate item id: {row['id']}")
        image_path = Path(row["image"])
        if image_path.is_absolute():
            raise ValueError(f"Item {row['id']} uses an absolute image path")
        resolved = solver_bundle / image_path
        if not resolved.exists():
            raise ValueError(f"Item {row['id']} references a missing image: {row['image']}")
        if ".." in image_path.parts:
            raise ValueError(f"Item {row['id']} path escapes solver bundle")
        ids.add(row["id"])
    return ids


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    args = parser.parse_args()

    item_rows = load_jsonl(args.items)
    gold_rows = load_jsonl(args.gold)
    gold_ids = verify_gold_rows(gold_rows)
    item_ids = verify_item_rows(item_rows, args.items.parent)

    if item_ids != gold_ids:
        missing_in_gold = sorted(item_ids - gold_ids)
        missing_in_items = sorted(gold_ids - item_ids)
        raise ValueError(
            "Item/gold id mismatch: "
            f"missing_in_gold={missing_in_gold} missing_in_items={missing_in_items}"
        )

    print(f"Verification passed for {len(item_rows)} items.")


if __name__ == "__main__":
    main()
