#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


KEYS = ["status", "reason_code", "allowed_cents", "insurer_pays_cents", "patient_owes_cents"]
STATUS = {"approved", "denied"}
REASONS = {"OK", "NO_AUTH", "NO_REF", "OON", "NOT_COVERED", "DATE"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def norm(answer: Any) -> dict[str, Any] | None:
    if isinstance(answer, str):
        try:
            answer = json.loads(answer)
        except Exception:
            return None
    if not isinstance(answer, dict):
        return None
    out: dict[str, Any] = {}
    for key in KEYS:
        if key not in answer:
            return None
    status = str(answer["status"]).strip().lower()
    reason = str(answer["reason_code"]).strip().upper()
    if status not in STATUS or reason not in REASONS:
        return None
    out["status"] = status
    out["reason_code"] = reason
    for key in KEYS[2:]:
        value = answer[key]
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            out[key] = value
        elif isinstance(value, str):
            s = value.strip().replace(",", "")
            if s.startswith("$"):
                return None
            sign = -1 if s.startswith("-") else 1
            if s[:1] in "+-":
                s = s[1:]
            if not s.isdigit():
                return None
            out[key] = sign * int(s)
        else:
            return None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    gold_rows = read_jsonl(Path(args.gold))
    pred_rows = read_jsonl(Path(args.predictions))
    gold_by_id = {r["id"]: r["answer"] for r in gold_rows if sorted(r.keys()) == ["answer", "id"]}
    pred_by_id = {r["id"]: r["answer"] for r in pred_rows if sorted(r.keys()) == ["answer", "id"]}
    details = []
    correct = 0
    for item_id in sorted(gold_by_id):
        g = norm(gold_by_id[item_id])
        p = norm(pred_by_id.get(item_id))
        assert g is not None
        ok = p == g
        correct += int(ok)
        details.append({"id": item_id, "correct": ok, "gold": g, "pred": p})
    report = {
        "benchmark": "Prior Authorization Forensics (PAF) v1",
        "score": f"{correct}/{len(gold_by_id)}",
        "correct": correct,
        "total": len(gold_by_id),
        "details": details,
    }
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["score"])


if __name__ == "__main__":
    main()
