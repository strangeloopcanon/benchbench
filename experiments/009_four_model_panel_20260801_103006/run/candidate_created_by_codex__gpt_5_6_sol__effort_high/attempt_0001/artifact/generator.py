#!/usr/bin/env python3
"""Generate deterministic Counterfeit Clock benchmark samples."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from reference_core import enumerate_answers, validate_public_item


NODES = ["Aster", "Birch", "Cobalt", "Dune", "Ember"]
MANIFEST_NODES = ["Kilo", "Lumen", "Mica", "Nova", "Onyx"]
RATES = [3, 5, 7, 11, 13]
MODULI = [97, 101, 103, 107, 109]
ROUTE_COUNTS = [3, 3, 3, 2, 2, 2, 2, 2]


def jsonl_write(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def make_routes(rng):
    order = NODES[:]
    rng.shuffle(order)
    candidate_routes = [
        (order[0], order[1]), (order[1], order[2]),
        (order[2], order[3]), (order[3], order[4]),
        (order[4], order[0]), (order[0], order[2]),
        (order[1], order[3]), (order[2], order[4]),
    ]
    routes = []
    for route, count in zip(candidate_routes, ROUTE_COUNTS):
        if rng.random() < 0.5:
            route = (route[1], route[0])
        routes.extend([route] * count)
    rng.shuffle(routes)
    return routes


def construct_candidate(item_id, rng):
    modulus = rng.choice(MODULI)
    rate_values = RATES[:]
    rng.shuffle(rate_values)
    clocks = {
        node: (rate_values[i], rng.randrange(modulus))
        for i, node in enumerate(NODES)
    }
    shuffled_manifest_nodes = MANIFEST_NODES[:]
    rng.shuffle(shuffled_manifest_nodes)
    node_map = dict(zip(NODES, shuffled_manifest_nodes))

    routes = make_routes(rng)
    send_times = sorted(rng.sample(range(20, 881), len(routes)))
    rng.shuffle(send_times)
    manifests = []
    for i, ((source, destination), send_time) in enumerate(zip(routes, send_times), 1):
        manifests.append({
            "manifest_id": f"M{i:02d}",
            "source": node_map[source],
            "destination": node_map[destination],
            "send_time": send_time,
            "receive_time": send_time + rng.randint(4, 37),
        })

    # Public packet aliases deliberately disagree with manifest IDs.  The
    # alias-to-manifest bijection is permuted independently within each route.
    by_route = defaultdict(list)
    for manifest in manifests:
        by_route[(manifest["source"], manifest["destination"])].append(manifest)
    packet_number = 1
    logs = []
    event_global_times = {}
    inverse_node_map = {value: key for key, value in node_map.items()}
    for route in sorted(by_route):
        group = by_route[route]
        aliases = [f"P{packet_number + i:02d}" for i in range(len(group))]
        packet_number += len(group)
        rng.shuffle(aliases)
        for alias, manifest in zip(aliases, group):
            source = inverse_node_map[manifest["source"]]
            destination = inverse_node_map[manifest["destination"]]
            for kind, node, peer, global_time in (
                ("send", source, destination, manifest["send_time"]),
                ("receive", destination, source, manifest["receive_time"]),
            ):
                rate, offset = clocks[node]
                tick = (rate * global_time + offset) % modulus
                record = {
                    "record_id": "pending",
                    "node": node,
                    "packet": alias,
                    "kind": kind,
                    "peer": peer,
                    "tick": tick,
                }
                logs.append(record)
                event_global_times[id(record)] = global_time

    # Record IDs encode only node-local chronological position, which is also
    # the display order promised by the task.
    ordered_logs = []
    for node in NODES:
        node_logs = [r for r in logs if r["node"] == node]
        node_logs.sort(key=lambda r: (event_global_times[id(r)], r["kind"], r["packet"]))
        for index, record in enumerate(node_logs, 1):
            record["record_id"] = f"{node[0]}-{index:02d}"
            ordered_logs.append(record)

    corrupt = rng.choice(ordered_logs)
    corrected_tick = corrupt["tick"]
    corrupt["tick"] = (corrected_tick + rng.randrange(1, modulus)) % modulus

    rng.shuffle(manifests)
    item = {
        "id": item_id,
        "modulus": modulus,
        "allowed_rates": sorted(RATES),
        "nodes": NODES,
        "manifest_nodes": MANIFEST_NODES,
        "manifests": manifests,
        "logs": ordered_logs,
    }
    answer = {"record_id": corrupt["record_id"], "corrected_tick": corrected_tick}
    return item, answer


def generate_one(index, master_rng):
    item_id = f"CC-{index:03d}"
    for attempt in range(1, 501):
        child_seed = master_rng.getrandbits(128)
        item, answer = construct_candidate(item_id, random.Random(child_seed))
        validate_public_item(item)
        admitted = enumerate_answers(item, stop_after=2)
        expected = {(answer["record_id"], answer["corrected_tick"])}
        if admitted == expected:
            return item, answer, attempt
    raise RuntimeError(f"could not generate uniquely solvable {item_id}")


def write_solver_docs(bundle):
    packet = """# Counterfeit Clock — Solver Packet

For every item, recover the one altered node-log timestamp.

## Public system rules

Each item is independent. It contains five local `nodes`, five
`manifest_nodes`, a prime `modulus`, five distinct `allowed_rates`, a trusted
global `manifests` ledger, and untrusted node `logs`.

For node `n`, there is an unknown rate `r_n` and offset `b_n`. The five nodes
use the five allowed rates bijectively: no two nodes use the same rate. Offsets
are arbitrary integers modulo `modulus`. At true integer time `t`, the node's
displayed counter is exactly

    tick_n(t) = (r_n * t + b_n) mod modulus.

The manifest station names and local node names are two different naming
systems. There is an unknown bijection between the five `nodes` and the five
`manifest_nodes`; a local record's `peer` is also a local node name. Every
manifest is one real packet and gives its trusted manifest-name source,
destination, global send time, and global receive time.

Every packet alias in the logs is also one real packet. Packet aliases and
manifest IDs are different naming systems. After applying the unknown station
bijection, within each ordered `(source, destination)` route there is an
unknown bijection between packet aliases and manifests. An alias's `send` and
`receive` records belong to the same packet.

The records for each node appear in chronological order within that node's
contiguous block in `logs`. Record order is correct even across counter wraps.
The manifest, endpoints, packet aliases, kinds, peers, record IDs, and order
are all correct. Across the entire item, exactly one `tick` value was replaced
by a different residue. All other ticks obey the clock equation.

## Required answer

Return one JSONL row per item, with exactly these outer keys:

    {"id":"CC-001","answer":{"record_id":"A-01","corrected_tick":42}}

`record_id` is the altered record. `corrected_tick` is its counter value before
alteration, an integer in `[0, modulus)`. Include every item exactly once.

## Auditable solving route

A complete finite search is practical. Enumerate the 5! station-name
bijections, rejecting those whose directed route multiplicities disagree. For
each surviving node/rate pairing, propose offsets from equations pairing a log
record with a compatible manifest event. Reject clock hypotheses that cannot
match all but at most one local tick multiset. Keep only five-node hypotheses
with distinct rates. For each route, enumerate the small within-route
alias/manifest permutations and retain explanations with exactly one unequal
tick overall. The supplied instances were accepted only when all valid
explanations give one identical `(record_id, corrected_tick)` answer.
"""
    (bundle / "solver_packet.md").write_text(packet, encoding="utf-8")
    manifest = {
        "benchmark": "counterfeit_clock",
        "version": "1.0",
        "entrypoint": "items_private_sample.jsonl",
        "instructions": "solver_packet.md",
        "prediction_format": "JSONL rows with exactly id and answer",
        "item_count": None,
        "assets": ["items_private_sample.jsonl", "solver_packet.md"],
    }
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-count", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    if args.sample_count < 1:
        parser.error("--sample-count must be positive")

    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bundle = out / "solver_bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    master_rng = random.Random(args.seed)
    items, gold, attempts = [], [], []
    for index in range(1, args.sample_count + 1):
        item, answer, attempt = generate_one(index, master_rng)
        items.append(item)
        gold.append({"id": item["id"], "answer": answer})
        attempts.append(attempt)

    jsonl_write(bundle / "items_private_sample.jsonl", items)
    jsonl_write(out / "gold_private_sample.jsonl", gold)
    solver_manifest = write_solver_docs(bundle)
    solver_manifest["item_count"] = len(items)
    (bundle / "SOLVER_MANIFEST.json").write_text(
        json.dumps(solver_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "generated": len(items),
        "max_acceptance_attempts": max(attempts),
        "mean_acceptance_attempts": sum(attempts) / len(attempts),
        "out_dir": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
