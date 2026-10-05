#!/usr/bin/env python3
import argparse
import json


def load_jsonl(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    gold_rows = load_jsonl(args.gold)
    gold = {r["id"]: str(r["answer"]).strip() for r in gold_rows}

    pred_rows = load_jsonl(args.predictions)
    preds = {r["id"]: str(r["answer"]).strip() for r in pred_rows}

    correct = 0
    missing = 0
    wrong = 0
    per_item = []
    for gid, gans in gold.items():
        pans = preds.get(gid)
        if pans is None:
            missing += 1
            per_item.append({"id": gid, "gold": gans, "pred": None, "correct": False})
            continue
        ok = pans == gans
        if ok:
            correct += 1
        else:
            wrong += 1
        per_item.append({"id": gid, "gold": gans, "pred": pans, "correct": ok})

    report = {
        "score": f"{correct}/{len(gold)}",
        "correct": correct,
        "wrong": wrong,
        "missing": missing,
        "total": len(gold),
        "exact_match": correct / max(1, len(gold)),
        "per_item": per_item,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print(report["score"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
