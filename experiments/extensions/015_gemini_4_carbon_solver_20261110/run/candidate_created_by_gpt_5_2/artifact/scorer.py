#!/usr/bin/env python3
import argparse
import json


def load_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    gold = {r["id"]: str(r["answer"]).strip() for r in load_jsonl(args.gold)}
    preds = {r["id"]: str(r["answer"]).strip() for r in load_jsonl(args.predictions)}
    correct = sum(preds.get(gid) == gans for gid, gans in gold.items())
    total = len(gold)
    report = {
        "schema_version": 2,
        "total": total,
        "correct": correct,
        "accuracy": correct / max(1, total),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
