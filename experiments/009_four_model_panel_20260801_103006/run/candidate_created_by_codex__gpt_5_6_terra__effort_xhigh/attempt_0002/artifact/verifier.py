#!/usr/bin/env python3
"""Structural and semantic verifier for a PAL item/gold pair."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}")
                if not isinstance(value, dict):
                    raise SystemExit(f"{path}:{line_number}: each row must be an object")
                rows.append(value)
    return rows


def require_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    if set(value) != expected:
        raise SystemExit(f"{where}: expected keys {sorted(expected)}, got {sorted(value)}")


# This is deliberately a separate, compact evaluator rather than an import from
# generator.py.  It makes the verification pass meaningful against an accidental
# generator-side semantic regression.
def usable(row: dict[str, Any], moment: int, device: str) -> bool:
    return row["active"] and row["start"] <= moment <= row["end"] and ("*" in row["devices"] or device in row["devices"])


def resource_index(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in policy["resources"]}


def member(policy: dict[str, Any], principal: str, wanted: str, moment: int, device: str) -> bool:
    reached = {
        row["group"]
        for row in policy["memberships"]
        if row["principal"] == principal and usable(row, moment, device)
    }
    pending = list(reached)
    while pending:
        child = pending.pop()
        for link in policy["links"]:
            if link["child"] == child and usable(link, moment, device) and link["parent"] not in reached:
                reached.add(link["parent"])
                pending.append(link["parent"])
    return wanted in reached


def below(resources: dict[str, dict[str, Any]], node: str, ancestor: str) -> bool:
    while node is not None:
        if node == ancestor:
            return True
        node = resources[node]["parent"]
    return False


def level(resources: dict[str, dict[str, Any]], node: str) -> int:
    result = 0
    while resources[node]["parent"] is not None:
        result += 1
        node = resources[node]["parent"]
    return result


def semantic_decision(policy: dict[str, Any], query: dict[str, Any]) -> tuple[str, str]:
    resources = resource_index(policy)
    tags = set(resources[query["resource"]]["tags"])
    options: list[tuple[tuple[int, int, int], dict[str, Any]]] = []
    for position, rule in enumerate(policy["rules"]):
        if not usable(rule, query["time"], query["device"]):
            continue
        if rule["action"] not in ("*", query["action"]):
            continue
        if rule["subject_type"] == "P":
            if rule["subject"] != query["principal"]:
                continue
        elif not member(policy, query["principal"], rule["subject"], query["time"], query["device"]):
            continue
        if rule["scope_mode"] == "SELF":
            if rule["scope"] != query["resource"]:
                continue
        elif not below(resources, query["resource"], rule["scope"]):
            continue
        if not set(rule["all_tags"]).issubset(tags):
            continue
        if rule["any_tags"] and not tags.intersection(rule["any_tags"]):
            continue
        if tags.intersection(rule["forbid_tags"]):
            continue
        options.append(((rule["priority"], level(resources, rule["scope"]), position), rule))
    if not options:
        return "D", "DEFAULT"
    winner = max(options, key=lambda option: option[0])[1]
    return ("A" if winner["effect"] == "ALLOW" else "D"), winner["id"]


def patched_copy(base: dict[str, Any], patches: list[dict[str, Any]]) -> dict[str, Any]:
    # JSON round-trip makes a clear deep copy while retaining JSON types only.
    policy = json.loads(json.dumps(base))
    collections = {"rule_field": "rules", "membership_field": "memberships", "link_field": "links"}
    for patch in patches:
        if patch["op"] in collections:
            record = next(row for row in policy[collections[patch["op"]]] if row["id"] == patch["target"])
            record[patch["field"]] = patch["value"]
        elif patch["op"] == "tag":
            record = next(row for row in policy["resources"] if row["id"] == patch["target"])
            if patch["present"] and patch["tag"] not in record["tags"]:
                record["tags"].append(patch["tag"])
                record["tags"].sort()
            if not patch["present"]:
                record["tags"] = [tag for tag in record["tags"] if tag != patch["tag"]]
    return policy


def recompute_answer(item: dict[str, Any]) -> str:
    after = patched_copy(item["base_policy"], item["patches"])
    parts = []
    for query in item["queries"]:
        old_decision, old_rule = semantic_decision(item["base_policy"], query)
        new_decision, new_rule = semantic_decision(after, query)
        parts.append(f"{query['id']}={old_decision}@{old_rule}>{new_decision}@{new_rule}")
    return ";".join(parts)


def check_item(item: dict[str, Any]) -> None:
    require_keys(item, {"id", "task", "base_policy", "patches", "queries"}, item.get("id", "item"))
    if not isinstance(item["id"], str) or not item["id"].startswith("pal-"):
        raise SystemExit("item has an invalid id")
    policy = item["base_policy"]
    required = {"principals", "groups", "resources", "memberships", "links", "rules"}
    if set(policy) != required:
        raise SystemExit(f"{item['id']}: malformed base_policy keys")
    resource_ids = {row["id"] for row in policy["resources"]}
    if len(resource_ids) != len(policy["resources"]) or "O00" not in resource_ids:
        raise SystemExit(f"{item['id']}: non-unique or missing resource ids")
    for resource in policy["resources"]:
        if resource["parent"] is not None and resource["parent"] not in resource_ids:
            raise SystemExit(f"{item['id']}: resource parent is absent")
    for kind, collection in (("membership", policy["memberships"]), ("link", policy["links"]), ("rule", policy["rules"])):
        identifiers = [row["id"] for row in collection]
        if len(identifiers) != len(set(identifiers)):
            raise SystemExit(f"{item['id']}: duplicate {kind} id")
    rule_ids = {row["id"] for row in policy["rules"]}
    membership_ids = {row["id"] for row in policy["memberships"]}
    link_ids = {row["id"] for row in policy["links"]}
    for patch in item["patches"]:
        if patch["op"] == "rule_field" and patch["target"] not in rule_ids:
            raise SystemExit(f"{item['id']}: patch targets absent rule")
        if patch["op"] == "membership_field" and patch["target"] not in membership_ids:
            raise SystemExit(f"{item['id']}: patch targets absent membership")
        if patch["op"] == "link_field" and patch["target"] not in link_ids:
            raise SystemExit(f"{item['id']}: patch targets absent link")
        if patch["op"] == "tag" and patch["target"] not in resource_ids:
            raise SystemExit(f"{item['id']}: patch targets absent resource")
    query_ids = [query["id"] for query in item["queries"]]
    if query_ids != [f"q{index:02d}" for index in range(10)]:
        raise SystemExit(f"{item['id']}: query ids must be q00 through q09 in order")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    args = parser.parse_args()
    items = load_jsonl(args.items)
    gold = load_jsonl(args.gold)
    if not items:
        raise SystemExit("no items")
    item_ids = [item.get("id") for item in items]
    if len(item_ids) != len(set(item_ids)):
        raise SystemExit("duplicate item ids")
    for item in items:
        check_item(item)
    for row in gold:
        require_keys(row, {"id", "answer"}, "gold row")
        if not isinstance(row["id"], str) or not isinstance(row["answer"], str):
            raise SystemExit("gold fields must be strings")
    if [row["id"] for row in gold] != item_ids:
        raise SystemExit("gold ids must occur once and in exactly item order")
    for item, row in zip(items, gold):
        expected = recompute_answer(item)
        if row["answer"] != expected:
            raise SystemExit(f"{item['id']}: gold answer disagrees with public semantics")
    print(f"OK: {len(items)} items, {len(gold)} gold rows, semantic recomputation matched")


if __name__ == "__main__":
    main()
