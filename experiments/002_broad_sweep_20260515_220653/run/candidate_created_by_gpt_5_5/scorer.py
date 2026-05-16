#!/usr/bin/env python3
"""Score Protocol Archaeology predictions."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HEX8 = re.compile(r"^[0-9a-f]{8}$")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    gold_rows = read_jsonl(Path(args.gold))
    pred_rows = read_jsonl(Path(args.predictions))
    gold = {row["id"]: row["answer"] for row in gold_rows}
    seen = set()
    item_scores = []
    malformed = []

    for row in pred_rows:
        if set(row) != {"id", "answer"}:
            malformed.append({"row": row, "reason": "wrong keys"})
            continue
        if row["id"] in seen:
            malformed.append({"row": row, "reason": "duplicate id"})
            continue
        seen.add(row["id"])
        normalized = row["answer"].strip().lower() if isinstance(row["answer"], str) else ""
        valid = bool(HEX8.fullmatch(normalized))
        correct = valid and gold.get(row["id"]) == normalized
        item_scores.append({"id": row["id"], "correct": bool(correct), "valid": valid})

    missing = sorted(set(gold) - seen)
    extra = sorted(seen - set(gold))
    correct_count = sum(1 for row in item_scores if row["correct"])
    total = len(gold)
    report = {
        "benchmark": "protocol_archaeology",
        "total": total,
        "correct": correct_count,
        "accuracy": correct_count / total if total else 0.0,
        "missing_ids": missing,
        "extra_ids": extra,
        "malformed_count": len(malformed),
        "malformed": malformed[:20],
        "item_scores": sorted(item_scores, key=lambda r: r["id"]),
    }
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("total", "correct", "accuracy", "malformed_count")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
