import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


REQUIRED_KEYS = ["eligible_downtime_minutes", "sla_breached", "credit_percent", "credit_usd_cents"]


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _normalize_answer(a: Any) -> Dict[str, Any] | None:
    if isinstance(a, str):
        a = a.strip()
        try:
            a = json.loads(a)
        except Exception:
            return None
    if not isinstance(a, dict):
        return None

    out: Dict[str, Any] = {}
    for k in REQUIRED_KEYS:
        if k not in a:
            return None
        out[k] = a[k]

    # Normalize booleans for sla_breached
    sb = out["sla_breached"]
    if isinstance(sb, bool):
        pass
    elif isinstance(sb, str):
        s = sb.strip().lower()
        if s in {"true", "yes", "y", "1"}:
            out["sla_breached"] = True
        elif s in {"false", "no", "n", "0"}:
            out["sla_breached"] = False
        else:
            return None
    elif isinstance(sb, int):
        out["sla_breached"] = bool(sb)
    else:
        return None

    # Normalize ints
    for k in ["eligible_downtime_minutes", "credit_percent", "credit_usd_cents"]:
        v = out[k]
        if isinstance(v, bool):
            return None
        if isinstance(v, (int,)):
            out[k] = int(v)
        elif isinstance(v, str):
            s = v.strip()
            if s.startswith("+"):
                s = s[1:]
            if not s or any(c not in "0123456789" for c in s):
                return None
            out[k] = int(s)
        else:
            return None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=str, required=True)
    ap.add_argument("--predictions", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    args = ap.parse_args()

    gold_rows = _read_jsonl(Path(args.gold))
    pred_rows = _read_jsonl(Path(args.predictions))

    gold_by_id: Dict[str, Dict[str, Any]] = {r["id"]: r["answer"] for r in gold_rows}
    pred_by_id: Dict[str, Any] = {}
    for r in pred_rows:
        if sorted(r.keys()) != ["answer", "id"]:
            continue
        pred_by_id[r["id"]] = r["answer"]

    results: List[Dict[str, Any]] = []
    correct = 0
    total = len(gold_by_id)

    for item_id, gold in sorted(gold_by_id.items()):
        raw_pred = pred_by_id.get(item_id, None)
        norm_pred = _normalize_answer(raw_pred)
        norm_gold = _normalize_answer(gold)
        assert norm_gold is not None

        is_correct = norm_pred == norm_gold
        if is_correct:
            correct += 1

        results.append(
            {
                "id": item_id,
                "correct": bool(is_correct),
                "gold": norm_gold,
                "pred": norm_pred,
            }
        )

    report = {
        "benchmark": "Service Credit Forensics (SCF) v1",
        "score": f"{correct}/{total}",
        "correct": correct,
        "total": total,
        "details": results,
    }

    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["score"])


if __name__ == "__main__":
    main()
