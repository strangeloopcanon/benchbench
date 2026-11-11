#!/usr/bin/env python3
"""Strict exact-match scorer for AuditWeave."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path):
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            try:
                row = json.loads(line)
            except Exception as exc:
                raise SystemExit(f"{path}:{n}: invalid JSON: {exc}")
            if set(row) != {"id", "answer"} or not isinstance(row["id"], str) or not isinstance(row["answer"], str):
                raise SystemExit(f"{path}:{n}: rows require exactly string id and string answer")
            rows.append(row)
    if len({r["id"] for r in rows}) != len(rows):
        raise SystemExit(f"{path}: duplicate id")
    return {r["id"]: r["answer"] for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    gold, pred = load(args.gold), load(args.predictions)
    unknown = sorted(set(pred) - set(gold))
    if unknown:
        raise SystemExit(f"predictions contain unknown ids: {unknown[:3]}")
    correct_ids = sorted(i for i, answer in gold.items() if pred.get(i) == answer)
    total = len(gold)
    correct = len(correct_ids)
    report = {
        "schema_version": 2,
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "missing": len(set(gold) - set(pred)),
        "correct_ids": correct_ids,
    }
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
