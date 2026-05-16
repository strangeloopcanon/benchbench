#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from generator import _compute_answer


def _read_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=str, required=True)
    ap.add_argument("--gold", type=str, required=True)
    args = ap.parse_args()

    items_path = Path(args.items)
    gold_path = Path(args.gold)

    items = _read_jsonl(items_path)
    gold = _read_jsonl(gold_path)

    gold_map: Dict[str, str] = {}
    for row in gold:
        if set(row.keys()) != {"id", "answer"}:
            raise SystemExit(f"Gold row keys must be exactly {{id, answer}}: {row.keys()}")
        gold_map[row["id"]] = row["answer"]

    if len(gold_map) != len(gold):
        raise SystemExit("Duplicate gold ids found.")

    for item in items:
        if set(item.keys()) != {"id", "gitignore", "paths"}:
            raise SystemExit(f"Item row keys must be exactly {{id, gitignore, paths}}: {item.keys()}")
        item_id = item["id"]
        if item_id not in gold_map:
            raise SystemExit(f"Item id missing from gold: {item_id}")
        if not isinstance(item["paths"], list) or not all(isinstance(p, str) for p in item["paths"]):
            raise SystemExit(f"Invalid paths list for item {item_id}")

        # Recompute expected answer from solver-visible fields and compare.
        # Treat directory paths by trailing '/' convention in the item payload.
        raw_paths: List[Tuple[str, bool]] = []
        for p in item["paths"]:
            raw_paths.append((p, p.endswith("/")))
        expected = _compute_answer(item["gitignore"], raw_paths)
        if expected != gold_map[item_id]:
            raise SystemExit(
                f"Gold mismatch for id={item_id}: recomputed={expected} gold={gold_map[item_id]}"
            )

    if set(gold_map.keys()) != {i["id"] for i in items}:
        raise SystemExit("Gold ids and item ids do not match exactly.")

    print("OK: items match gold under reference matcher.")


if __name__ == "__main__":
    main()

