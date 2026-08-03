#!/usr/bin/env python3
"""Structural and unique-solvability verifier for Counterfeit Clock."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reference_core import enumerate_answers, validate_public_item


def _reject_json_constant(value):
    raise ValueError(f"non-standard JSON constant {value}")


def _object_without_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def load_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{path}:{line_number}: blank line")
            rows.append(json.loads(
                line,
                object_pairs_hook=_object_without_duplicate_keys,
                parse_constant=_reject_json_constant,
            ))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", required=True)
    parser.add_argument("--gold", required=True)
    args = parser.parse_args()

    items = load_jsonl(args.items)
    gold_rows = load_jsonl(args.gold)
    items_by_id = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("public item rows must be JSON objects")
        validate_public_item(item)
        if item["id"] in items_by_id:
            raise ValueError(f"duplicate public item id {item['id']}")
        items_by_id[item["id"]] = item

    gold = {}
    for row in gold_rows:
        if not isinstance(row, dict):
            raise ValueError("gold rows must be JSON objects")
        if set(row) != {"id", "answer"}:
            raise ValueError(f"gold row must contain exactly id and answer: {row}")
        if not isinstance(row["id"], str) or not row["id"]:
            raise ValueError("gold id must be a non-empty string")
        if not isinstance(row["answer"], dict) or set(row["answer"]) != {
            "record_id", "corrected_tick"
        }:
            raise ValueError(f"wrong answer schema for {row['id']}")
        answer = row["answer"]
        if not isinstance(answer["record_id"], str) or not answer["record_id"]:
            raise ValueError(f"invalid record_id for {row['id']}")
        if type(answer["corrected_tick"]) is not int:
            raise ValueError(f"invalid corrected_tick for {row['id']}")
        if row["id"] in gold:
            raise ValueError(f"duplicate gold id {row['id']}")
        gold[row["id"]] = answer

    if set(items_by_id) != set(gold):
        raise ValueError("item/gold id sets differ")

    for item_id, answer in gold.items():
        item = items_by_id[item_id]
        if not 0 <= answer["corrected_tick"] < item["modulus"]:
            raise ValueError(f"corrected_tick out of range for {item_id}")
        record_ids = {record["record_id"] for record in item["logs"]}
        if answer["record_id"] not in record_ids:
            raise ValueError(f"gold record_id is not public for {item_id}")

    for item in items:
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
