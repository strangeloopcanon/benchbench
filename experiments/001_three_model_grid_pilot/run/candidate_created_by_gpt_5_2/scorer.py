#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def _read_jsonl_strict(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise SystemExit(f"{path}:{lineno}: expected object per line")
            rows.append(obj)
    return rows


def _index_id_answer(rows: List[dict], path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for i, r in enumerate(rows):
        got = tuple(sorted(r.keys()))
        if got != ("answer", "id"):
            raise SystemExit(f"{path}:row{i}: expected keys ['answer','id']; got {list(got)}")
        if not isinstance(r["id"], str) or not isinstance(r["answer"], str):
            raise SystemExit(f"{path}:row{i}: id/answer must be strings")
        if r["id"] in out:
            raise SystemExit(f"{path}: duplicate id {r['id']}")
        out[r["id"]] = r["answer"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=str, required=True)
    ap.add_argument("--predictions", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    args = ap.parse_args()

    gold_path = Path(args.gold).resolve()
    pred_path = Path(args.predictions).resolve()
    out_path = Path(args.out).resolve()

    gold_rows = _read_jsonl_strict(gold_path)
    pred_rows = _read_jsonl_strict(pred_path)
    gold = _index_id_answer(gold_rows, gold_path)
    pred = _index_id_answer(pred_rows, pred_path)

    missing = sorted(set(gold.keys()) - set(pred.keys()))
    extra = sorted(set(pred.keys()) - set(gold.keys()))
    if missing:
        raise SystemExit(f"predictions missing {len(missing)} ids (example {missing[0]})")
    if extra:
        raise SystemExit(f"predictions has {len(extra)} extra ids (example {extra[0]})")

    per_item = []
    correct = 0
    for item_id in sorted(gold.keys()):
        g = gold[item_id]
        p = pred[item_id]
        ok = int(p == g)
        correct += ok
        per_item.append({"id": item_id, "gold": g, "pred": p, "correct": ok})

    report = {
        "benchmark_id": "folded_strip_order_v1",
        "total": len(gold),
        "correct": correct,
        "n_items": len(gold),
        "n_correct": correct,
        "accuracy": correct / max(1, len(gold)),
        "exact_match": True,
        "per_item": per_item,
    }
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} (accuracy {report['accuracy']:.3f} = {correct}/{len(gold)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
