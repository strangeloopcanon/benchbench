#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


LABELS = set("KLMNPQ")


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--gold", required=True)
    args = ap.parse_args()
    items = read_jsonl(args.items)
    gold = read_jsonl(args.gold)
    assert len(items) == len(gold) == 30, f"expected 30 rows, got items={len(items)} gold={len(gold)}"
    gold_by_id = {}
    for row in gold:
        assert set(row) == {"id", "answer"}, f"gold row has extra/missing keys: {row}"
        assert isinstance(row["id"], str) and row["id"], row
        assert isinstance(row["answer"], str) and len(row["answer"]) == 4 and set(row["answer"]) <= LABELS, row
        assert row["id"] not in gold_by_id, f"duplicate gold id {row['id']}"
        gold_by_id[row["id"]] = row["answer"]
    seen = set()
    items_path = Path(args.items).resolve()
    solver_dir = items_path.parent
    for row in items:
        assert row.get("id") in gold_by_id, f"item without gold: {row.get('id')}"
        assert row["id"] not in seen, f"duplicate item id {row['id']}"
        seen.add(row["id"])
        rel = row.get("image")
        assert isinstance(rel, str) and rel and not rel.startswith(("/", "../")), f"bad relative image path: {rel}"
        img = solver_dir / rel
        assert img.exists() and img.suffix.lower() == ".png", f"missing png: {rel}"
        joined = json.dumps(row).lower()
        for banned in ["gold", "seed", "trace", "layer_order", "bottom_to_top"]:
            assert banned not in joined, f"solver item leaks banned token {banned}: {row['id']}"
    print(f"VERIFIED {len(items)} items")


if __name__ == "__main__":
    main()
