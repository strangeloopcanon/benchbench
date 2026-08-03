#!/usr/bin/env python3
"""Documented weak shortcut: blame the largest raw adjacent counter jump."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    predictions = []
    with Path(args.items).open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            modulus = item["modulus"]
            best = None
            previous = {}
            for record in item["logs"]:
                node = record["node"]
                if node in previous:
                    distance = abs(record["tick"] - previous[node]["tick"])
                    candidate = (distance, record["record_id"], previous[node]["tick"])
                    if best is None or candidate > best:
                        best = candidate
                previous[node] = record
            _, record_id, guessed_tick = best
            predictions.append({
                "id": item["id"],
                "answer": {"record_id": record_id, "corrected_tick": guessed_tick % modulus},
            })
    with Path(args.out).open("w", encoding="utf-8") as handle:
        for row in predictions:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
