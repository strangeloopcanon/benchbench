#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path} line {line_number}: invalid JSON: {exc}") from exc
    return rows


def load_answers(path: Path):
    rows = load_jsonl(path)
    answers = {}
    for row in rows:
        if set(row.keys()) != {"id", "answer"}:
            raise ValueError(f"{path} rows must contain exactly id and answer")
        if row["id"] in answers:
            raise ValueError(f"Duplicate id in {path}: {row['id']}")
        answers[row["id"]] = row["answer"]
    return answers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    gold = load_answers(args.gold)
    predictions = load_answers(args.predictions)

    if set(gold) != set(predictions):
        missing = sorted(set(gold) - set(predictions))
        extra = sorted(set(predictions) - set(gold))
        raise ValueError(f"Prediction ids mismatch. missing={missing} extra={extra}")

    correct = 0
    details = []
    for item_id in sorted(gold):
        is_correct = predictions[item_id] == gold[item_id]
        correct += int(is_correct)
        details.append({
            "id": item_id,
            "gold": gold[item_id],
            "prediction": predictions[item_id],
            "correct": is_correct,
        })

    total = len(gold)
    report = {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "details": details,
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Scored {correct}/{total} correct.")


if __name__ == "__main__":
    main()
