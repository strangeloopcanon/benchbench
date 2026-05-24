#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


REQUIRED_ANSWER_KEYS = {"status", "reason_code", "allowed_cents", "insurer_pays_cents", "patient_owes_cents"}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                row = json.loads(line)
                if sorted(row.keys()) != ["answer", "id"] and "gold" in str(path):
                    raise SystemExit(f"{path}:{n} must contain exactly id and answer")
                rows.append(row)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--gold", required=True)
    args = ap.parse_args()
    items_path = Path(args.items)
    bundle = items_path.parent
    items = read_jsonl(items_path)
    gold = read_jsonl(Path(args.gold))
    item_ids = []
    for n, row in enumerate(items, 1):
        if sorted(row.keys()) != ["asset", "id"]:
            raise SystemExit(f"item row {n} must contain exactly id and asset")
        asset = bundle / row["asset"]
        if not asset.is_file():
            raise SystemExit(f"missing asset for {row['id']}: {row['asset']}")
        text = asset.read_text(encoding="utf-8")
        if row["id"] not in text:
            raise SystemExit(f"asset for {row['id']} does not mention id")
        forbidden = ["gold_private_sample", "answer key", "private_audit", "seed 20260516"]
        low = text.lower()
        if any(token in low for token in forbidden):
            raise SystemExit(f"asset for {row['id']} contains forbidden leakage term")
        item_ids.append(row["id"])
    gold_ids = []
    for n, row in enumerate(gold, 1):
        if sorted(row.keys()) != ["answer", "id"]:
            raise SystemExit(f"gold row {n} must contain exactly id and answer")
        if set(row["answer"].keys()) != REQUIRED_ANSWER_KEYS:
            raise SystemExit(f"gold row {n} answer keys mismatch")
        gold_ids.append(row["id"])
    if sorted(item_ids) != sorted(gold_ids):
        raise SystemExit("item ids and gold ids differ")
    manifest = bundle / "SOLVER_MANIFEST.json"
    readme = bundle / "README.md"
    if not manifest.is_file() or not readme.is_file():
        raise SystemExit("solver bundle missing manifest or README")
    for private_name in ["generator.py", "scorer.py", "verifier.py", "gold_private_sample.jsonl", "validation_report.md", "private_audit_traces.jsonl"]:
        if (bundle / private_name).exists():
            raise SystemExit(f"private file leaked into solver bundle: {private_name}")
    print(f"verified {len(items)} items")


if __name__ == "__main__":
    main()
