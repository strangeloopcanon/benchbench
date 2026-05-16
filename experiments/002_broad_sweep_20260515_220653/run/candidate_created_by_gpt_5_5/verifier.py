#!/usr/bin/env python3
"""Verify Protocol Archaeology package integrity."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


HEX8 = re.compile(r"^[0-9a-f]{8}$")
HEX16 = re.compile(r"^[0-9a-f]{16}$")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def fail(msg: str) -> int:
    print(f"VERIFY_FAIL: {msg}", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--gold", required=True)
    args = ap.parse_args()

    items_path = Path(args.items)
    gold_path = Path(args.gold)
    try:
        items = read_jsonl(items_path)
        gold = read_jsonl(gold_path)
    except Exception as exc:
        return fail(str(exc))

    if not items:
        return fail("no items")
    if len(items) != len(gold):
        return fail(f"item/gold count mismatch: {len(items)} vs {len(gold)}")

    gold_by_id = {}
    for row in gold:
        if set(row) != {"id", "answer"}:
            return fail(f"gold row has wrong keys: {row}")
        if not isinstance(row["id"], str) or not HEX8.fullmatch(row["answer"]):
            return fail(f"bad gold row: {row}")
        if row["id"] in gold_by_id:
            return fail(f"duplicate gold id {row['id']}")
        gold_by_id[row["id"]] = row["answer"]

    for item in items:
        required = {"id", "protocol_note", "answer_format", "examples", "query_packet"}
        if set(item) != required:
            return fail(f"item {item.get('id')} has keys {sorted(item)}")
        if item["id"] not in gold_by_id:
            return fail(f"item id missing from gold: {item['id']}")
        if not HEX16.fullmatch(item["query_packet"]):
            return fail(f"bad query packet for {item['id']}")
        if not isinstance(item["examples"], list) or len(item["examples"]) < 10:
            return fail(f"too few examples for {item['id']}")
        seen_packets = {item["query_packet"]}
        for ex in item["examples"]:
            if set(ex) != {"packet", "response"}:
                return fail(f"bad example keys for {item['id']}: {ex}")
            if not HEX16.fullmatch(ex["packet"]) or not HEX8.fullmatch(ex["response"]):
                return fail(f"bad example hex for {item['id']}: {ex}")
            if ex["packet"] in seen_packets:
                return fail(f"duplicate packet in {item['id']}")
            seen_packets.add(ex["packet"])
            if ex["response"] == gold_by_id[item["id"]]:
                return fail(f"gold answer appears as an example response in {item['id']}")

    print(json.dumps({"status": "ok", "items": len(items), "gold": len(gold)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
