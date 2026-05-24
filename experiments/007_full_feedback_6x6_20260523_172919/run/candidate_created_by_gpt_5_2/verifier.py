import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _fail(msg: str) -> None:
    raise SystemExit(msg)


def _sorted_ids(rows: Iterable[Dict[str, Any]]) -> List[str]:
    return sorted([r.get("id", "") for r in rows])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=str, required=True)
    ap.add_argument("--gold", type=str, required=True)
    args = ap.parse_args()

    items_path = Path(args.items)
    gold_path = Path(args.gold)

    items = _read_jsonl(items_path)
    gold = _read_jsonl(gold_path)

    if not items:
        _fail("no items loaded")
    if not gold:
        _fail("no gold loaded")

    item_ids = _sorted_ids(items)
    gold_ids = _sorted_ids(gold)

    if item_ids != gold_ids:
        missing_in_gold = sorted(set(item_ids) - set(gold_ids))
        missing_in_items = sorted(set(gold_ids) - set(item_ids))
        _fail(
            "item/gold id mismatch\n"
            f"missing_in_gold={missing_in_gold}\n"
            f"missing_in_items={missing_in_items}\n"
        )

    # Validate gold shape.
    for row in gold:
        if sorted(row.keys()) != ["answer", "id"]:
            _fail(f"gold row keys must be exactly ['id','answer']: got {sorted(row.keys())} for id={row.get('id')}")
        ans = row["answer"]
        if not isinstance(ans, dict):
            _fail(f"gold answer must be object for id={row['id']}")
        for k in ["eligible_downtime_minutes", "sla_breached", "credit_percent", "credit_usd_cents"]:
            if k not in ans:
                _fail(f"gold missing key {k} for id={row['id']}")

    # Validate item assets are within solver_bundle.
    base = items_path.parent
    for item in items:
        assets = item.get("assets", {})
        if not isinstance(assets, dict):
            _fail(f"item assets must be object for id={item.get('id')}")
        for name, rel in assets.items():
            if not isinstance(rel, str):
                _fail(f"asset path must be string for id={item.get('id')} asset={name}")
            p = (base / rel).resolve()
            if base.resolve() not in p.parents and p != base.resolve():
                _fail(f"asset escapes solver bundle for id={item.get('id')} asset={name}: {rel}")
            if not p.exists():
                _fail(f"missing asset for id={item.get('id')} asset={name}: {rel}")

    print("OK: items and gold are consistent; all referenced assets exist within solver bundle.")


if __name__ == "__main__":
    main()
