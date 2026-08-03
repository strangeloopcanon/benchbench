#!/usr/bin/env python3
"""Structural and unique-solvability verifier for Counterfeit Clock."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reference_core import enumerate_answers, validate_public_item


def load_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{path}:{line_number}: blank line")
            rows.append(json.loads(line))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", required=True)
    parser.add_argument("--gold", required=True)
    args = parser.parse_args()

    items = load_jsonl(args.items)
    gold_rows = load_jsonl(args.gold)
    gold = {}
    for row in gold_rows:
        if set(row) != {"id", "answer"}:
            raise ValueError(f"gold row must contain exactly id and answer: {row}")
        if set(row["answer"]) != {"record_id", "corrected_tick"}:
            raise ValueError(f"wrong answer schema for {row['id']}")
        if row["id"] in gold:
            raise ValueError(f"duplicate gold id {row['id']}")
        gold[row["id"]] = row["answer"]

    item_ids = [item.get("id") for item in items]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("duplicate public item id")
    if set(item_ids) != set(gold):
        raise ValueError("item/gold id sets differ")

    for item in items:
        validate_public_item(item)
        answers = enumerate_answers(item, stop_after=2)
        if len(answers) != 1:
            raise ValueError(f"{item['id']}: expected 1 identifiable answer, got {len(answers)}+")
        record_id, corrected_tick = next(iter(answers))
        derived = {"record_id": record_id, "corrected_tick": corrected_tick}
        if derived != gold[item["id"]]:
            raise ValueError(f"{item['id']}: public constraints disagree with gold")

    print(json.dumps({
        "status": "ok",
        "items": len(items),
        "gold_schema": "exact",
        "publicly_identifiable": len(items),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
