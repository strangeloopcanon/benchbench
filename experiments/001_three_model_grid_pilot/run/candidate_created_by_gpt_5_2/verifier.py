#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple


def _read_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{lineno}: invalid JSON: {e}") from e
            if not isinstance(obj, dict):
                raise SystemExit(f"{path}:{lineno}: expected object per line")
            rows.append(obj)
    return rows


def _must_exact_keys(obj: dict, keys: Tuple[str, ...], context: str) -> None:
    got = tuple(sorted(obj.keys()))
    exp = tuple(sorted(keys))
    if got != exp:
        raise SystemExit(f"{context}: expected keys {list(exp)}; got {list(got)}")


def _index_by_id(rows: List[dict], context: str) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for idx, r in enumerate(rows):
        if "id" not in r or not isinstance(r["id"], str):
            raise SystemExit(f"{context}: row {idx} missing string id")
        rid = r["id"]
        if rid in out:
            raise SystemExit(f"{context}: duplicate id {rid}")
        out[rid] = r
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=str, required=True, help="solver_bundle/items_private_sample.jsonl")
    ap.add_argument("--gold", type=str, required=True, help="gold_private_sample.jsonl")
    args = ap.parse_args()

    items_path = Path(args.items).resolve()
    gold_path = Path(args.gold).resolve()
    if not items_path.exists():
        raise SystemExit(f"items file not found: {items_path}")
    if not gold_path.exists():
        raise SystemExit(f"gold file not found: {gold_path}")

    items_rows = _read_jsonl(items_path)
    gold_rows = _read_jsonl(gold_path)

    # Gold: strict contract
    for i, r in enumerate(gold_rows):
        _must_exact_keys(r, ("id", "answer"), f"{gold_path}:row{i}")
        if not isinstance(r["answer"], str):
            raise SystemExit(f"{gold_path}:row{i}: answer must be string")

    # Items: ensure no answer leakage and all paths are relative under solver_bundle.
    for i, r in enumerate(items_rows):
        if "answer" in r:
            raise SystemExit(f"{items_path}:row{i}: items must not contain answer")
        for k in ("id", "path", "prompt"):
            if k not in r:
                raise SystemExit(f"{items_path}:row{i}: missing key {k}")
        if not isinstance(r["id"], str) or not isinstance(r["path"], str) or not isinstance(r["prompt"], str):
            raise SystemExit(f"{items_path}:row{i}: id/path/prompt must be strings")
        rel = Path(r["path"])
        if rel.is_absolute():
            raise SystemExit(f"{items_path}:row{i}: path must be relative to solver_bundle: {r['path']}")
        if ".." in rel.parts:
            raise SystemExit(f"{items_path}:row{i}: path must not contain '..': {r['path']}")
        solver_bundle_dir = items_path.parent
        target = (solver_bundle_dir / rel).resolve()
        try:
            target.relative_to(solver_bundle_dir.resolve())
        except Exception:
            raise SystemExit(f"{items_path}:row{i}: path escapes solver_bundle: {r['path']}")
        if not target.exists():
            raise SystemExit(f"{items_path}:row{i}: referenced file missing: {r['path']}")

    items_by_id = _index_by_id(items_rows, str(items_path))
    gold_by_id = _index_by_id(gold_rows, str(gold_path))

    if set(items_by_id.keys()) != set(gold_by_id.keys()):
        missing_in_gold = sorted(set(items_by_id.keys()) - set(gold_by_id.keys()))
        missing_in_items = sorted(set(gold_by_id.keys()) - set(items_by_id.keys()))
        raise SystemExit(
            "id mismatch between items and gold\n"
            f"missing_in_gold={missing_in_gold[:5]} (n={len(missing_in_gold)})\n"
            f"missing_in_items={missing_in_items[:5]} (n={len(missing_in_items)})"
        )

    print(f"OK: {len(gold_rows)} items; ids match; contracts satisfied; files exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

