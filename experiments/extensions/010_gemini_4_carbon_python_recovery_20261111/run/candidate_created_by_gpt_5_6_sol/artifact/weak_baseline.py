#!/usr/bin/env python3
"""Obvious shortcut baseline: choose A and trust JSON event order."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auditweave_core import apply_op, event_op, freeze, render_answer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    predictions = []
    with Path(args.items).open(encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            state = freeze(item["initial"])
            for phase in item["phases"]:
                for event in phase["events"]:
                    state = apply_op(state, event_op(event, "A"))
            for op in item["query_ops"]:
                state = apply_op(state, op)
            predictions.append({"id": item["id"], "answer": render_answer("A", state)})
    with Path(args.out).open("w", encoding="utf-8") as f:
        for row in predictions:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"predictions": len(predictions), "policy": "candidate A plus JSON event order; audits and before edges ignored"}))


if __name__ == "__main__":
    main()
