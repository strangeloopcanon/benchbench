import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


ANSWER_KEYS = [
    "included_units",
    "earned_royalty_cents",
    "recouped_advance_cents",
    "payable_cents",
]


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_answer(answer: Any) -> Dict[str, int] | None:
    if isinstance(answer, str):
        try:
            answer = json.loads(answer)
        except Exception:
            return None
    if not isinstance(answer, dict):
        return None
    out: Dict[str, int] = {}
    for key in ANSWER_KEYS:
        if key not in answer:
            return None
        value = answer[key]
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            out[key] = value
            continue
        if isinstance(value, str):
            s = value.strip()
            if s.startswith("+"):
                s = s[1:]
            if s.startswith("-"):
                body = s[1:]
                if not body.isdigit():
                    return None
                out[key] = -int(body)
                continue
            if not s.isdigit():
                return None
            out[key] = int(s)
            continue
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
    gold_by_id = {row["id"]: row["answer"] for row in gold_rows}
    pred_by_id: Dict[str, Any] = {}
    for row in pred_rows:
        if sorted(row.keys()) == ["answer", "id"]:
            pred_by_id[row["id"]] = row["answer"]

    details: List[Dict[str, Any]] = []
    correct = 0
    total = len(gold_rows)

    for item_id in sorted(gold_by_id):
        gold_answer = normalize_answer(gold_by_id[item_id])
        pred_answer = normalize_answer(pred_by_id.get(item_id))
        assert gold_answer is not None
        is_correct = pred_answer == gold_answer
        if is_correct:
            correct += 1
        details.append(
            {
                "id": item_id,
                "correct": is_correct,
                "gold": gold_answer,
                "pred": pred_answer,
            }
        )

    report = {
        "benchmark": "Catalog Royalty Forensics (CRF) v1",
        "score": f"{correct}/{total}",
        "correct": correct,
        "total": total,
        "details": details,
    }
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["score"])


if __name__ == "__main__":
    main()
