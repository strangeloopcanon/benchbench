#!/usr/bin/env python3
"""Generate the private CFPS sample and its solver-only packet.

This program intentionally has no third-party dependencies.  The generated
items are public instances; their optimum revocation sets are written only to
the root-level gold file.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
TASK_NAME = "Counterfactual Firewall Policy Synthesis (CFPS)"


def recipe_mask(recipe: list[str], index: dict[str, int]) -> int:
    result = 0
    for name in recipe:
        result |= 1 << index[name]
    return result


def operation_masks(operation: dict[str, Any], index: dict[str, int]) -> list[list[int]]:
    return [
        [recipe_mask(recipe, index) for recipe in channel["recipes"]]
        for channel in operation["channels"]
    ]


def service_operational(channels: list[list[int]], revoked: int) -> bool:
    # Every channel needs at least one wholly active recipe.
    return all(any((recipe & revoked) == 0 for recipe in channel) for channel in channels)


def attack_blocked(channels: list[list[int]], revoked: int) -> bool:
    # An attack fails as soon as one of its required channels has no active recipe.
    return any(all((recipe & revoked) != 0 for recipe in channel) for channel in channels)


def answer_for_item(item: dict[str, Any]) -> str:
    """Return the canonical optimum.  Used for generation and independent checks."""
    names = [entry["name"] for entry in item["permissions"]]
    costs = [entry["revoke_cost"] for entry in item["permissions"]]
    index = {name: i for i, name in enumerate(names)}
    services = [operation_masks(x, index) for x in item["services"]]
    attacks = [operation_masks(x, index) for x in item["attacks"]]
    n = len(names)

    def feasible(mask: int) -> bool:
        return all(service_operational(x, mask) for x in services) and all(
            attack_blocked(x, mask) for x in attacks
        )

    # The construction gives us a feasible incumbent, but this general search
    # is also valid for hand-authored instances.  Positive costs permit safe
    # branch-and-bound on the primary objective.
    incumbent_mask = (1 << n) - 1
    incumbent_cost = sum(costs)
    incumbent_count = n
    incumbent_names = tuple(names)

    def consider(mask: int, cost: int, count: int) -> None:
        nonlocal incumbent_mask, incumbent_cost, incumbent_count, incumbent_names
        if not feasible(mask):
            return
        selected = tuple(names[i] for i in range(n) if mask & (1 << i))
        key = (cost, count, selected)
        old_key = (incumbent_cost, incumbent_count, incumbent_names)
        if key < old_key:
            incumbent_mask = mask
            incumbent_cost = cost
            incumbent_count = count
            incumbent_names = selected

    # Seed the search with a known solution embedded in the generation-only
    # object.  It is removed before the public item is emitted.
    planted_names = item.get("_planted_solution", [])
    if planted_names:
        planted_mask = sum(1 << index[x] for x in planted_names)
        planted_cost = sum(costs[index[x]] for x in planted_names)
        if feasible(planted_mask):
            incumbent_mask = planted_mask
            incumbent_cost = planted_cost
            incumbent_count = len(planted_names)
            incumbent_names = tuple(name for name in names if name in planted_names)

    def visit(position: int, mask: int, cost: int, count: int) -> None:
        if cost > incumbent_cost:
            return
        if cost == incumbent_cost and count > incumbent_count:
            return
        if position == n:
            consider(mask, cost, count)
            return
        visit(position + 1, mask, cost, count)
        next_cost = cost + costs[position]
        if next_cost <= incumbent_cost:
            visit(position + 1, mask | (1 << position), next_cost, count + 1)

    visit(0, 0, 0, 0)
    if incumbent_mask == (1 << n) - 1 and not feasible(incumbent_mask):
        raise ValueError("instance has no feasible revocation set")
    return ",".join(incumbent_names) if incumbent_names else "NONE"


def canonical_recipe(values: list[str]) -> list[str]:
    return sorted(set(values))


def make_distinct_recipes(
    rng: random.Random, candidates: list[str], count: int, minimum: int, maximum: int
) -> list[list[str]]:
    recipes: set[tuple[str, ...]] = set()
    while len(recipes) < count:
        width = rng.randint(minimum, maximum)
        recipes.add(tuple(sorted(rng.sample(candidates, width))))
    return [list(x) for x in sorted(recipes)]


def make_item(rng: random.Random, serial: int) -> dict[str, Any]:
    names = [f"p{i:02d}" for i in range(1, 19)]
    protected = names[:5]
    eligible = names[5:]
    # A generation-only feasible policy has six members, but each attack uses
    # a different overlapping subset of them.  It is therefore an upper bound,
    # not an answer pattern exposed by a single common gate.
    planted = sorted(rng.sample(eligible, 6))
    non_planted = [x for x in eligible if x not in planted]
    costs: dict[str, int] = {}
    for name in protected:
        costs[name] = rng.randint(6, 10)
    for name in planted:
        costs[name] = rng.randint(2, 7)
    for name in non_planted:
        costs[name] = rng.randint(2, 8)

    services: list[dict[str, Any]] = []
    # These singleton channels make several permissions truly operationally
    # indispensable.  The other channels impose less obvious coupled limits.
    for number, must_keep in enumerate(protected[:3], start=1):
        other_pool = [x for x in names if x not in planted]
        services.append(
            {
                "name": f"service_{number}",
                "channels": [
                    {"name": "identity", "recipes": [[must_keep]]},
                    {
                        "name": "continuity",
                        "recipes": make_distinct_recipes(rng, other_pool, 4, 2, 3),
                    },
                ],
            }
        )
    for number in range(4, 7):
        other_pool = [x for x in names if x not in planted]
        services.append(
            {
                "name": f"service_{number}",
                "channels": [
                    {
                        "name": "authorization",
                        "recipes": make_distinct_recipes(rng, other_pool, 4, 1, 3),
                    },
                    {
                        "name": "delivery",
                        "recipes": make_distinct_recipes(rng, other_pool, 4, 2, 3),
                    },
                ],
            }
        )

    attacks: list[dict[str, Any]] = []
    for number in range(1, 9):
        choke_recipes: set[tuple[str, ...]] = set()
        # Each attack has a different focus set.  Every recipe in this channel
        # touches that focus set, so the generation-only policy is feasible,
        # but a solver can trade off overlapping focuses and incidental
        # supports across attacks.
        focus = sorted(rng.sample(planted, rng.randint(3, 5)))
        for planted_name in focus:
            for _ in range(2):
                support = rng.sample(non_planted, rng.randint(1, 2))
                choke_recipes.add(tuple(canonical_recipe([planted_name, *support])))
        while len(choke_recipes) < 9:
            planted_name = rng.choice(focus)
            support = rng.sample(non_planted, rng.randint(1, 2))
            choke_recipes.add(tuple(canonical_recipe([planted_name, *support])))
        attacks.append(
            {
                "name": f"attack_{number}",
                "channels": [
                    {"name": "credential_gate", "recipes": [list(x) for x in sorted(choke_recipes)]},
                    {
                        "name": "session_path",
                        "recipes": make_distinct_recipes(rng, eligible, 6, 2, 3),
                    },
                    {
                        "name": "egress_path",
                        "recipes": make_distinct_recipes(rng, eligible, 6, 2, 3),
                    },
                ],
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "id": f"cfps-20260516-{serial:03d}",
        "task": "cfps-v1",
        "permissions": [{"name": name, "revoke_cost": costs[name]} for name in names],
        "services": services,
        "attacks": attacks,
        "_planted_solution": planted,
    }


def public_item(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if not key.startswith("_")}


def make_samples(sample_count: int, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rng = random.Random(seed)
    items: list[dict[str, Any]] = []
    gold: list[dict[str, str]] = []
    for serial in range(1, sample_count + 1):
        # Reject instances whose optimum is too shallow to exercise the full
        # policy semantics.  The acceptance test is deterministic under seed.
        for attempt in range(500):
            item = make_item(rng, serial)
            answer = answer_for_item(item)
            selected = [] if answer == "NONE" else answer.split(",")
            if len(selected) >= 4 and sum(
                p["revoke_cost"] for p in item["permissions"] if p["name"] in selected
            ) >= 10:
                items.append(public_item(item))
                gold.append({"id": item["id"], "answer": answer})
                break
        else:
            raise RuntimeError(f"could not construct a suitably difficult item {serial}")
    return items, gold


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


SOLVER_README = """# CFPS solver packet

## Counterfactual Firewall Policy Synthesis v1

Each line of `items_private_sample.jsonl` is one independent policy-synthesis
instance.  Submit exactly one JSON line per item with its `id` and `answer`.

For an instance, choose a set `R` of permission names to revoke.  A permission
not in `R` is active.

- A recipe is a list of permissions.  It is **active** iff every listed
  permission is active (equivalently, none of its names is in `R`).
- A channel is **open** iff at least one of its recipes is active.
- A service is **operational** iff every one of its channels is open.
- An attack **succeeds** iff every one of its channels is open.  It is
  **blocked** iff at least one of its channels is not open.

A valid policy leaves every listed service operational and blocks every listed
attack.  Its primary objective is to minimize the sum of `revoke_cost` for all
permissions in `R`.  Break equal-cost ties by fewer revoked permissions, then
by the lexicographically smallest increasing tuple of permission names.  Names
are compared as ordinary strings (`p02` precedes `p10`).

The answer is that final increasing tuple as comma-separated names with no
spaces, e.g. `p03,p11,p14`.  If the tuple is empty, write `NONE`.

All information needed to solve an instance is in this packet.  A practical
method is to encode the rules as Boolean constraints or enumerate the 2^18
candidate revocation masks with cost-based pruning.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a CFPS private sample")
    parser.add_argument("--sample-count", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.sample_count <= 0:
        raise SystemExit("--sample-count must be positive")
    out_dir = args.out_dir
    bundle = out_dir / "solver_bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    items, gold = make_samples(args.sample_count, args.seed)
    write_jsonl(bundle / "items_private_sample.jsonl", items)
    write_jsonl(out_dir / "gold_private_sample.jsonl", gold)
    (bundle / "README.md").write_text(SOLVER_README, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "benchmark": "cfps-v1",
        "item_file": "items_private_sample.jsonl",
        "solver_instructions": "README.md",
        "item_count": args.sample_count,
        "answer_format": "comma-separated increasing permission names, or NONE",
        "public_assets": [],
    }
    (bundle / "SOLVER_MANIFEST.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
