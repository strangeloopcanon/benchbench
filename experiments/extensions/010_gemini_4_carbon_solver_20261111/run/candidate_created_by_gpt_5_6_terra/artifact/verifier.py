#!/usr/bin/env python3
"""Structural and semantic verifier for a CFPS solver packet and its gold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"{path}:{number}: blank lines are not allowed")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{number}: each row must be an object")
        rows.append(row)
    return rows


def validate_item(item: dict[str, Any]) -> None:
    required = {"schema_version", "id", "task", "permissions", "services", "attacks"}
    if set(item) != required:
        raise ValueError(f"{item.get('id', '<unknown>')}: unexpected item keys")
    if item["schema_version"] != 1 or item["task"] != "cfps-v1":
        raise ValueError(f"{item['id']}: wrong schema/task")
    permissions = item["permissions"]
    if not isinstance(permissions, list) or len(permissions) != 18:
        raise ValueError(f"{item['id']}: expected exactly 18 permissions")
    names = [x.get("name") for x in permissions]
    if names != sorted(names) or len(set(names)) != len(names):
        raise ValueError(f"{item['id']}: permission names must be unique and sorted")
    if any(set(x) != {"name", "revoke_cost"} or not isinstance(x["revoke_cost"], int) or x["revoke_cost"] <= 0 for x in permissions):
        raise ValueError(f"{item['id']}: malformed permission cost")
    name_set = set(names)
    for group_name in ("services", "attacks"):
        groups = item[group_name]
        if not isinstance(groups, list) or not groups:
            raise ValueError(f"{item['id']}: {group_name} must be nonempty")
        for operation in groups:
            if set(operation) != {"name", "channels"} or not operation["channels"]:
                raise ValueError(f"{item['id']}: malformed operation")
            for channel in operation["channels"]:
                if set(channel) != {"name", "recipes"} or not channel["recipes"]:
                    raise ValueError(f"{item['id']}: malformed channel")
                canonical = []
                for recipe in channel["recipes"]:
                    if not isinstance(recipe, list) or not recipe or recipe != sorted(recipe) or len(recipe) != len(set(recipe)) or not set(recipe) <= name_set:
                        raise ValueError(f"{item['id']}: malformed recipe")
                    canonical.append(tuple(recipe))
                if len(canonical) != len(set(canonical)):
                    raise ValueError(f"{item['id']}: duplicate recipes")


def semantic_answer(item: dict[str, Any]) -> str:
    """Independent reference implementation of the public CFPS rules."""
    names = [entry["name"] for entry in item["permissions"]]
    costs = [entry["revoke_cost"] for entry in item["permissions"]]
    index = {name: position for position, name in enumerate(names)}

    def compiled(operations: list[dict[str, Any]]) -> list[list[list[int]]]:
        result = []
        for operation in operations:
            op_channels = []
            for channel in operation["channels"]:
                recipes = []
                for recipe in channel["recipes"]:
                    mask = 0
                    for name in recipe:
                        mask |= 1 << index[name]
                    recipes.append(mask)
                op_channels.append(recipes)
            result.append(op_channels)
        return result

    services = compiled(item["services"])
    attacks = compiled(item["attacks"])

    def allowed(mask: int) -> bool:
        for service in services:
            # An active recipe has no revoked bit. Every service channel needs one.
            if any(not any((recipe & mask) == 0 for recipe in channel) for channel in service):
                return False
        for attack in attacks:
            # At least one attack channel must have every recipe interrupted.
            if not any(all((recipe & mask) != 0 for recipe in channel) for channel in attack):
                return False
        return True

    best: tuple[int, int, tuple[str, ...]] | None = None
    n = len(names)

    def search(position: int, mask: int, cost: int, count: int) -> None:
        nonlocal best
        if best is not None:
            if cost > best[0] or (cost == best[0] and count > best[1]):
                return
        # Service availability is monotone decreasing as additional permissions
        # are revoked, so an already-broken service can never be repaired.
        for service in services:
            if any(not any((recipe & mask) == 0 for recipe in channel) for channel in service):
                return
        if position == n:
            if allowed(mask):
                selected = tuple(names[i] for i in range(n) if mask & (1 << i))
                candidate = (cost, count, selected)
                if best is None or candidate < best:
                    best = candidate
            return
        search(position + 1, mask, cost, count)
        search(position + 1, mask | (1 << position), cost + costs[position], count + 1)

    search(0, 0, 0, 0)
    if best is None:
        raise ValueError(f"{item['id']}: no feasible policy")
    return ",".join(best[2]) if best[2] else "NONE"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate CFPS public items and private gold")
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    args = parser.parse_args()
    items = read_jsonl(args.items)
    gold = read_jsonl(args.gold)
    if not items:
        raise SystemExit("no items")
    ids = [item.get("id") for item in items]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate item id")
    for item in items:
        validate_item(item)
    if any(set(row) != {"id", "answer"} or not isinstance(row["answer"], str) for row in gold):
        raise SystemExit("gold rows must contain exactly id and answer")
    if [row["id"] for row in gold] != ids:
        raise SystemExit("gold IDs must match public item IDs in order")
    recomputed = [semantic_answer(item) for item in items]
    supplied = [row["answer"] for row in gold]
    if recomputed != supplied:
        raise SystemExit("gold does not match the semantic optimum")
    print(json.dumps({"ok": True, "items": len(items), "semantic_gold_checked": len(gold)}))


if __name__ == "__main__":
    main()
