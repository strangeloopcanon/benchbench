#!/usr/bin/env python3
"""Dataset, schema, reference-solution, and leak-isolation verifier for MGAF.

CLI Contract:
  python3.12 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from generator import CANONICAL_CASES, solve_case


FORBIDDEN_ITEM_KEYS = {"answer", "gold", "gold_answer", "solution", "label", "expected"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        obj = json.loads(stripped)
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(obj)
    return rows


def verify_package(
    items_path: Path,
    gold_path: Path,
    bundle_dir: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []

    if not items_path.exists():
        errors.append(f"Missing items file: {items_path}")
    if not gold_path.exists():
        errors.append(f"Missing gold file: {gold_path}")
    if errors:
        return {
            "schema_version": 2,
            "status": "error",
            "valid": False,
            "passed": False,
            "total": 0,
            "verified": 0,
            "correct": 0,
            "accuracy": 0.0,
            "leak_scan_matches": 0,
            "errors": errors,
        }

    if bundle_dir is None:
        bundle_dir = items_path.parent

    items = load_jsonl(items_path)
    gold = load_jsonl(gold_path)

    if len(items) != len(gold):
        errors.append(f"Item count ({len(items)}) != gold count ({len(gold)})")
    if len(items) == 0:
        errors.append("Dataset has 0 items")

    # Check solver bundle manifest and docs if present in bundle_dir
    manifest_path = bundle_dir / "SOLVER_MANIFEST.json"
    if not manifest_path.exists():
        errors.append(f"Missing solver manifest: {manifest_path}")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for doc_rel in manifest.get("documentation_files", []):
                if not (bundle_dir / doc_rel).exists():
                    errors.append(f"Missing solver documentation file: {bundle_dir / doc_rel}")
            for asset_rel in manifest.get("asset_files", []):
                if not (bundle_dir / asset_rel).exists():
                    errors.append(f"Missing solver asset file: {bundle_dir / asset_rel}")
        except Exception as exc:
            errors.append(f"Invalid SOLVER_MANIFEST.json: {exc}")

    seen_ids: set[str] = set()
    gold_by_id: dict[str, int] = {}
    for idx, g_row in enumerate(gold):
        gid = g_row.get("id")
        ans = g_row.get("answer")
        if not isinstance(gid, str) or not gid:
            errors.append(f"gold[{idx}]: invalid id {gid!r}")
            continue
        if isinstance(ans, bool) or not isinstance(ans, int) or ans <= 0:
            errors.append(f"gold[{idx}] ({gid}): answer must be positive integer USD cents, got {ans!r}")
            continue
        gold_by_id[gid] = ans

    canonical_by_id = {c["id"]: c for c in CANONICAL_CASES}
    verified_count = 0

    for idx, item in enumerate(items):
        iid = item.get("id")
        if not isinstance(iid, str) or not iid:
            errors.append(f"items[{idx}]: missing/invalid id")
            continue
        if iid in seen_ids:
            errors.append(f"Duplicate item id: {iid}")
        seen_ids.add(iid)

        leaked_keys = FORBIDDEN_ITEM_KEYS.intersection(item.keys())
        if leaked_keys:
            errors.append(f"items[{idx}] ({iid}): forbidden answer keys present: {sorted(leaked_keys)}")

        prompt = item.get("prompt")
        if not isinstance(prompt, str) or len(prompt.strip()) < 20:
            errors.append(f"items[{idx}] ({iid}): missing or too-short prompt")

        for rel_asset in item.get("asset_files", []):
            asset_p = bundle_dir / rel_asset
            if not asset_p.exists():
                errors.append(f"items[{idx}] ({iid}): missing referenced asset {asset_p}")

        if iid not in gold_by_id:
            errors.append(f"items[{idx}] ({iid}): missing from gold file")
            continue

        if iid in canonical_by_id:
            expected_ans = solve_case(canonical_by_id[iid])
            if gold_by_id[iid] != expected_ans:
                errors.append(
                    f"{iid}: gold answer {gold_by_id[iid]} != reference solver {expected_ans}"
                )
                continue

        verified_count += 1

    # Leak scan across all files in bundle_dir
    leak_matches: list[str] = []
    if bundle_dir.exists():
        gold_tokens = {str(ans): gid for gid, ans in gold_by_id.items() if len(str(ans)) >= 5}
        for file_path in sorted(bundle_dir.rglob("*")):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue
            for ans_str, gid in gold_tokens.items():
                if re.search(rf"(?<!\d){re.escape(ans_str)}(?!\d)", content):
                    leak_matches.append(f"{file_path.relative_to(bundle_dir)}:{gid}:{ans_str}")

    if leak_matches:
        errors.append(f"Answer leak detected in solver_bundle: {leak_matches}")

    total = len(items)
    passed = len(errors) == 0 and verified_count == total and total > 0
    return {
        "schema_version": 2,
        "status": "ok" if passed else "error",
        "valid": passed,
        "passed": passed,
        "total": total,
        "verified": verified_count,
        "correct": verified_count if passed else 0,
        "accuracy": (verified_count / total) if total > 0 else 0.0,
        "leak_scan_matches": len(leak_matches),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify MGAF benchmark items, gold answers, and solver bundle isolation.")
    parser.add_argument(
        "--items",
        "--items-file",
        "--items-path",
        "--dataset",
        dest="items",
        type=str,
        default="solver_bundle/items_private_sample.jsonl",
    )
    parser.add_argument(
        "--gold",
        "--gold-file",
        "--gold-path",
        "--answer-key",
        dest="gold",
        type=str,
        default="gold_private_sample.jsonl",
    )
    parser.add_argument(
        "--bundle-dir",
        "--solver-bundle",
        dest="bundle_dir",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--out",
        "--output",
        "--report",
        dest="out",
        type=str,
        default=None,
    )
    args, positional = parser.parse_known_args()

    items_path = Path(args.items)
    gold_path = Path(args.gold)
    if len(positional) >= 1 and args.items == "solver_bundle/items_private_sample.jsonl":
        items_path = Path(positional[0])
    if len(positional) >= 2 and args.gold == "gold_private_sample.jsonl":
        gold_path = Path(positional[1])

    bundle_dir = Path(args.bundle_dir) if args.bundle_dir else None
    report = verify_package(items_path=items_path, gold_path=gold_path, bundle_dir=bundle_dir)
    serialized = json.dumps(report, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(serialized, encoding="utf-8")
    sys.stdout.write(serialized)
    if not report["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
