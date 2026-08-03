#!/usr/bin/env python3
"""Generate deterministic Patchwork Access Logic (PAL) evaluation items.

The generated solver packet contains only its manifest, public semantics, and
policy instances. Answers are intentionally emitted to a separate gold file at
the requested output directory.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path
from typing import Any


ACTIONS = ["read", "write", "share", "delete"]
DEVICES = ["desk", "field", "secure"]
TAGS = ["amber", "blue", "cold", "delta", "ember", "frost", "green", "high", "iris"]
LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"

# Public templates are emitted by generate(), so --out-dir can be empty.
SOLVER_MANIFEST: dict[str, Any] = {
    "benchmark": "Patchwork Access Logic (PAL)",
    "version": "1.0",
    "entrypoint": "items_private_sample.jsonl",
    "instructions": "README.md",
    "answer_format": "one JSONL object per item with exactly id and answer",
    "assets": ["items_private_sample.jsonl", "README.md"],
    "contains_gold": False,
    "contains_generator": False,
}
SOLVER_README = "# Patchwork Access Logic (PAL)\n\nEach line of `items_private_sample.jsonl` is one independent policy-delta\nproblem. For every item, return one JSON object with exactly `id` and `answer`.\nNo explanation is scored. The answer must concatenate its ten query outcomes in\nthe displayed query order, with no spaces:\n\n```\nq00=D@DEFAULT>D@DEFAULT;q01=A@R07>D@R07;...;q09=A@R12>A@R12\n```\n\nFor each query, the left side is the decision/source for `base_policy`; the\nright side is the decision/source after applying every `patches` entry in array\norder. `A` means allow and `D` means deny. `DEFAULT` is the source if no rule\nmatches. A source is always the winning rule's `id`, even if the decision stays\nthe same after a patch.\n\n## Public semantics\n\nAll integer time intervals are closed: `start <= query.time <= end`. A record\nis usable only when `active` is true, its interval contains the query time, and\nits `devices` includes either the query device or `\"*\"`.\n\n### Effective membership\n\nA principal directly belongs to every usable `memberships` record with that\nprincipal. A usable `links` record means membership in `child` also gives\nmembership in `parent`. Repeat this implication transitively until no new\ngroups are reached. (The supplied link graph is acyclic.) A rule with\n`subject_type: \"P\"` matches only its named principal; one with `\"G\"` matches\nwhen the query principal is effectively a member of its named group under that\nquery's time and device.\n\n### Rule matching\n\nA rule matches a query exactly when all of these hold:\n\n1. The rule itself is usable at the query time/device.\n2. Its `action` equals the query action, or is `\"*\"`.\n3. Its subject matches by the membership rule above.\n4. `scope_mode: \"SELF\"` requires the query resource to equal `scope`.\n   `scope_mode: \"TREE\"` permits the scope resource itself and every descendant\n   of it in the `resources` parent tree.\n5. Every `all_tags` tag occurs on the query resource; if `any_tags` is nonempty,\n   at least one of its tags occurs; none of `forbid_tags` occurs.\n\nTags live only on the queried resource—ancestor tags are not inherited. An\nempty `all_tags`, `any_tags`, or `forbid_tags` imposes no condition of that\nkind.\n\n### Winner and decision\n\nAmong all matching rules, select the maximum tuple:\n\n```\n(priority, depth(scope), position_in_rules_array)\n```\n\nwhere root `O00` has depth 0 and children have depth one more than their\nparent. Thus larger priority wins; ties go to the deeper scope; remaining ties\ngo to the rule appearing later in `rules`. The winner produces `A` for effect\n`ALLOW` and `D` for effect `DENY`. If nothing matches, the result is\n`D@DEFAULT`.\n\n### Patches\n\nStart from a deep copy of `base_policy`, then apply `patches` in listed order.\n`rule_field`, `membership_field`, and `link_field` replace the named field on\nthe object with that `target` id. A `tag` patch adds its tag if `present` is\ntrue and absent, or removes all occurrences if `present` is false. No other\nfield changes. Then evaluate the same queries against that patched policy.\n\nThe policy itself is the complete evidence: no external facts or customary\naccess-control conventions apply.\n"



def _dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":"), sort_keys=True))
            handle.write("\n")


def _write_solver_packet(bundle: Path, items: list[dict[str, Any]]) -> None:
    """Write every public solver-bundle asset deterministically and leak-free."""
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "SOLVER_MANIFEST.json").write_text(
        json.dumps(SOLVER_MANIFEST, indent=2) + "\n", encoding="utf-8"
    )
    (bundle / "README.md").write_text(SOLVER_README, encoding="utf-8")
    _dump_jsonl(bundle / "items_private_sample.jsonl", items)


def _find(records: list[dict[str, Any]], identifier: str) -> dict[str, Any]:
    for record in records:
        if record["id"] == identifier:
            return record
    raise ValueError(f"unknown identifier {identifier}")


def _in_window(record: dict[str, Any], moment: int, device: str) -> bool:
    return (
        record["active"]
        and record["start"] <= moment <= record["end"]
        and ("*" in record["devices"] or device in record["devices"])
    )


def _is_member(policy: dict[str, Any], principal: str, group: str, moment: int, device: str) -> bool:
    """Determine effective group membership through active child->parent links."""
    direct_groups = {
        row["group"]
        for row in policy["memberships"]
        if row["principal"] == principal and _in_window(row, moment, device)
    }
    frontier = list(direct_groups)
    reached = set(direct_groups)
    while frontier:
        child = frontier.pop()
        for link in policy["links"]:
            if link["child"] == child and _in_window(link, moment, device):
                parent = link["parent"]
                if parent not in reached:
                    reached.add(parent)
                    frontier.append(parent)
    return group in reached


def _resource_map(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in policy["resources"]}


def _is_under(resources: dict[str, dict[str, Any]], target: str, scope: str) -> bool:
    current = target
    while current is not None:
        if current == scope:
            return True
        current = resources[current]["parent"]
    return False


def _depth(resources: dict[str, dict[str, Any]], resource: str) -> int:
    value = 0
    current = resource
    while resources[current]["parent"] is not None:
        value += 1
        current = resources[current]["parent"]
    return value


def _matches(policy: dict[str, Any], rule: dict[str, Any], query: dict[str, Any]) -> bool:
    if not _in_window(rule, query["time"], query["device"]):
        return False
    if rule["action"] not in ("*", query["action"]):
        return False
    if rule["subject_type"] == "P":
        if rule["subject"] != query["principal"]:
            return False
    elif not _is_member(policy, query["principal"], rule["subject"], query["time"], query["device"]):
        return False
    resources = _resource_map(policy)
    if rule["scope_mode"] == "SELF":
        if rule["scope"] != query["resource"]:
            return False
    elif not _is_under(resources, query["resource"], rule["scope"]):
        return False
    tags = set(resources[query["resource"]]["tags"])
    if not set(rule["all_tags"]).issubset(tags):
        return False
    if rule["any_tags"] and not tags.intersection(rule["any_tags"]):
        return False
    if tags.intersection(rule["forbid_tags"]):
        return False
    return True


def decision(policy: dict[str, Any], query: dict[str, Any]) -> tuple[str, str]:
    """Return (A|D, source-rule-id-or-DEFAULT) under the public PAL ordering."""
    resources = _resource_map(policy)
    candidates: list[tuple[tuple[int, int, int], dict[str, Any]]] = []
    for order, rule in enumerate(policy["rules"]):
        if _matches(policy, rule, query):
            candidates.append(((rule["priority"], _depth(resources, rule["scope"]), order), rule))
    if not candidates:
        return "D", "DEFAULT"
    winner = max(candidates, key=lambda pair: pair[0])[1]
    return ("A" if winner["effect"] == "ALLOW" else "D"), winner["id"]


def apply_patches(base: dict[str, Any], patches: list[dict[str, Any]]) -> dict[str, Any]:
    policy = copy.deepcopy(base)
    for patch in patches:
        kind = patch["op"]
        if kind == "rule_field":
            _find(policy["rules"], patch["target"])[patch["field"]] = patch["value"]
        elif kind == "membership_field":
            _find(policy["memberships"], patch["target"])[patch["field"]] = patch["value"]
        elif kind == "link_field":
            _find(policy["links"], patch["target"])[patch["field"]] = patch["value"]
        elif kind == "tag":
            resource = _find(policy["resources"], patch["target"])
            tag = patch["tag"]
            if patch["present"] and tag not in resource["tags"]:
                resource["tags"].append(tag)
                resource["tags"].sort()
            if not patch["present"]:
                resource["tags"] = [existing for existing in resource["tags"] if existing != tag]
        else:
            raise ValueError(f"bad patch op {kind}")
    return policy


def answer_for(item: dict[str, Any]) -> str:
    before = item["base_policy"]
    after = apply_patches(before, item["patches"])
    values = []
    for query in item["queries"]:
        old_decision, old_source = decision(before, query)
        new_decision, new_source = decision(after, query)
        values.append(f"{query['id']}={old_decision}@{old_source}>{new_decision}@{new_source}")
    return ";".join(values)


def _id(prefix: str, number: int) -> str:
    return f"{prefix}{number:02d}"


def _devices(rng: random.Random, broad_probability: float = 0.62) -> list[str]:
    if rng.random() < broad_probability:
        return ["*"]
    count = 1 if rng.random() < 0.75 else 2
    return sorted(rng.sample(DEVICES, count))


def _window(rng: random.Random, broad_probability: float = 0.55) -> tuple[int, int]:
    if rng.random() < broad_probability:
        return 1, 12
    start = rng.randint(1, 10)
    return start, rng.randint(start, 12)


def _make_resources(rng: random.Random) -> list[dict[str, Any]]:
    resources = [{"id": "O00", "parent": None, "tags": sorted(rng.sample(TAGS, 2))}]
    for index in range(1, 25):
        # Restrict parents to earlier nodes, making a visible acyclic tree.
        parent = rng.choice(resources[max(0, index - 12) :]) ["id"]
        tags = sorted(rng.sample(TAGS, rng.choice([1, 2, 2, 3])))
        resources.append({"id": _id("O", index), "parent": parent, "tags": tags})
    return resources


def _make_policy(rng: random.Random) -> dict[str, Any]:
    principals = [_id("P", index) for index in range(16)]
    groups = [_id("G", index) for index in range(12)]
    resources = _make_resources(rng)
    memberships: list[dict[str, Any]] = []
    for index in range(52):
        start, end = _window(rng, 0.7)
        memberships.append(
            {
                "id": _id("M", index),
                "principal": rng.choice(principals),
                "group": rng.choice(groups),
                "active": True,
                "start": start,
                "end": end,
                "devices": _devices(rng, 0.7),
            }
        )
    links: list[dict[str, Any]] = []
    possible_links = [(groups[child], groups[parent]) for child in range(1, len(groups)) for parent in range(child)]
    rng.shuffle(possible_links)
    for index, (child, parent) in enumerate(possible_links[:18]):
        start, end = _window(rng, 0.68)
        links.append(
            {
                "id": _id("L", index),
                "child": child,
                "parent": parent,
                "active": True,
                "start": start,
                "end": end,
                "devices": _devices(rng, 0.72),
            }
        )
    rules: list[dict[str, Any]] = []
    for index in range(66):
        start, end = _window(rng, 0.65)
        tag_mode = rng.random()
        all_tags = [] if tag_mode < 0.46 else rng.sample(TAGS, 1)
        any_tags = [] if tag_mode < 0.85 else rng.sample(TAGS, rng.choice([1, 2]))
        forbid_tags = [] if rng.random() < 0.82 else rng.sample(TAGS, 1)
        if rng.random() < 0.42:
            subject_type, subject = "P", rng.choice(principals)
        else:
            subject_type, subject = "G", rng.choice(groups)
        rules.append(
            {
                "id": _id("R", index),
                "active": True,
                "scope": rng.choice(resources)["id"],
                "scope_mode": "TREE" if rng.random() < 0.71 else "SELF",
                "subject_type": subject_type,
                "subject": subject,
                "action": rng.choice(ACTIONS + ["*", "*"]),
                "all_tags": sorted(all_tags),
                "any_tags": sorted(any_tags),
                "forbid_tags": sorted(forbid_tags),
                "start": start,
                "end": end,
                "devices": _devices(rng, 0.72),
                "effect": "ALLOW" if rng.random() < 0.57 else "DENY",
                "priority": rng.randint(0, 22),
            }
        )
    return {
        "principals": principals,
        "groups": groups,
        "resources": resources,
        "memberships": memberships,
        "links": links,
        "rules": rules,
    }


def _make_patches(policy: dict[str, Any], rng: random.Random) -> list[dict[str, Any]]:
    """Produce changes of every public kind, including second-order changes."""
    patches: list[dict[str, Any]] = []
    rule_choices = rng.sample(policy["rules"], 8)
    for index, rule in enumerate(rule_choices):
        if index % 3 == 0:
            patches.append({"op": "rule_field", "target": rule["id"], "field": "effect", "value": "DENY" if rule["effect"] == "ALLOW" else "ALLOW"})
        elif index % 3 == 1:
            patches.append({"op": "rule_field", "target": rule["id"], "field": "active", "value": False})
        else:
            patches.append({"op": "rule_field", "target": rule["id"], "field": "priority", "value": min(30, rule["priority"] + rng.randint(6, 12))})
    for membership in rng.sample(policy["memberships"], 3):
        patches.append({"op": "membership_field", "target": membership["id"], "field": "active", "value": False})
    for link in rng.sample(policy["links"], 2):
        patches.append({"op": "link_field", "target": link["id"], "field": "active", "value": False})
    for resource in rng.sample(policy["resources"][1:], 2):
        tag = rng.choice(TAGS)
        patches.append({"op": "tag", "target": resource["id"], "tag": tag, "present": tag not in resource["tags"]})
    rng.shuffle(patches)
    return patches


def _query_pool(policy: dict[str, Any], rng: random.Random, size: int = 2600) -> list[dict[str, Any]]:
    return [
        {
            "id": "_",
            "principal": rng.choice(policy["principals"]),
            "action": rng.choice(ACTIONS),
            "resource": rng.choice(policy["resources"])["id"],
            "time": rng.randint(1, 12),
            "device": rng.choice(DEVICES),
        }
        for _ in range(size)
    ]


def _choose_queries(policy: dict[str, Any], patches: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]] | None:
    after = apply_patches(policy, patches)
    buckets: dict[str, list[dict[str, Any]]] = {key: [] for key in ("flip", "source", "allow", "deny")}
    seen: set[tuple[str, str, str, int, str]] = set()
    for query in _query_pool(policy, rng):
        signature = (query["principal"], query["action"], query["resource"], query["time"], query["device"])
        if signature in seen:
            continue
        seen.add(signature)
        old = decision(policy, query)
        new = decision(after, query)
        if old[0] != new[0]:
            buckets["flip"].append(query)
        elif old[1] != new[1]:
            buckets["source"].append(query)
        elif old[0] == "A":
            buckets["allow"].append(query)
        else:
            buckets["deny"].append(query)
    needed = {"flip": 4, "source": 2, "allow": 2, "deny": 2}
    if any(len(buckets[key]) < count for key, count in needed.items()):
        return None
    selected: list[dict[str, Any]] = []
    for key in ("flip", "source", "allow", "deny"):
        selected.extend(rng.sample(buckets[key], needed[key]))
    rng.shuffle(selected)
    for index, query in enumerate(selected):
        query["id"] = f"q{index:02d}"
    return selected


def make_item(seed: int, item_index: int) -> dict[str, Any]:
    """Use retry seeds so each public item has a deliberately mixed response set."""
    for attempt in range(100):
        local_seed = seed * 1_000_003 + item_index * 10_007 + attempt * 97
        rng = random.Random(local_seed)
        policy = _make_policy(rng)
        patches = _make_patches(policy, rng)
        queries = _choose_queries(policy, patches, rng)
        if queries is not None:
            return {
                "id": f"pal-{item_index + 1:03d}",
                "task": "Evaluate every request before and after the ordered patch list, then return the canonical provenance string.",
                "base_policy": policy,
                "patches": patches,
                "queries": queries,
            }
    raise RuntimeError(f"could not construct a balanced item {item_index}")


def generate(sample_count: int, seed: int, out_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items = [make_item(seed, index) for index in range(sample_count)]
    gold = [{"id": item["id"], "answer": answer_for(item)} for item in items]
    bundle = out_dir / "solver_bundle"
    _write_solver_packet(bundle, items)
    _dump_jsonl(out_dir / "gold_private_sample.jsonl", gold)
    return items, gold


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-count", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.sample_count <= 0:
        raise SystemExit("--sample-count must be positive")
    generate(args.sample_count, args.seed, args.out_dir)


if __name__ == "__main__":
    main()
