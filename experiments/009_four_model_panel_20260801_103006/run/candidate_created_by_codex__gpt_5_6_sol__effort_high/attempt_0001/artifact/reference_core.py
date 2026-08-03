"""Private reference enumerator for Counterfeit Clock.

This module is intentionally kept outside the isolated solver bundle.  It uses
only the public rules; it contains no secret key or instance-specific labels.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import permutations


def _event_time(manifest, kind):
    if kind == "send":
        return manifest["send_time"]
    return manifest["receive_time"]


def _local_candidates(item, node, node_map):
    """Return (rate, offset, local lower-bound mismatch count) candidates."""
    modulus = item["modulus"]
    logs = [r for r in item["logs"] if r["node"] == node]
    expected_by_category = defaultdict(list)
    inverse_map = {value: key for key, value in node_map.items()}
    for m in item["manifests"]:
        if m["source"] == node_map[node]:
            expected_by_category[("send", inverse_map[m["destination"]])].append(m["send_time"])
        if m["destination"] == node_map[node]:
            expected_by_category[("receive", inverse_map[m["source"]])].append(m["receive_time"])

    observed_by_category = defaultdict(list)
    for r in logs:
        observed_by_category[(r["kind"], r["peer"])].append(r["tick"])

    candidates = []
    for rate in item["allowed_rates"]:
        offsets = set()
        for category, records in observed_by_category.items():
            for tick in records:
                for global_time in expected_by_category[category]:
                    offsets.add((tick - rate * global_time) % modulus)
        for offset in offsets:
            mismatch = 0
            for category, observed in observed_by_category.items():
                expected = [
                    (rate * t + offset) % modulus
                    for t in expected_by_category[category]
                ]
                overlap = sum((Counter(observed) & Counter(expected)).values())
                mismatch += len(observed) - overlap
            if mismatch <= 1:
                candidates.append((rate, offset, mismatch))
    return candidates


def _route_options(item, clocks, node_map):
    """For each route, say whether cost 0 is possible and list cost-1 answers."""
    by_tag = defaultdict(dict)
    for record in item["logs"]:
        by_tag[record["packet"]][record["kind"]] = record

    tags_by_route = defaultdict(list)
    for tag, ends in by_tag.items():
        send = ends["send"]
        tags_by_route[(send["node"], send["peer"])].append(tag)

    manifests_by_route = defaultdict(list)
    for manifest in item["manifests"]:
        manifests_by_route[(manifest["source"], manifest["destination"])].append(manifest)

    route_results = []
    for log_route in sorted(tags_by_route):
        manifest_route = (node_map[log_route[0]], node_map[log_route[1]])
        tags = sorted(tags_by_route[log_route])
        manifests = sorted(manifests_by_route[manifest_route], key=lambda m: m["manifest_id"])
        zero_possible = False
        one_answers = set()
        for assignment in permutations(manifests):
            mismatches = []
            for tag, manifest in zip(tags, assignment):
                for kind in ("send", "receive"):
                    record = by_tag[tag][kind]
                    rate, offset = clocks[record["node"]]
                    expected = (
                        rate * _event_time(manifest, kind) + offset
                    ) % item["modulus"]
                    if record["tick"] != expected:
                        mismatches.append((record["record_id"], expected))
                        if len(mismatches) > 1:
                            break
                if len(mismatches) > 1:
                    break
            if not mismatches:
                zero_possible = True
            elif len(mismatches) == 1:
                record_id, corrected_tick = mismatches[0]
                one_answers.add((record_id, corrected_tick))
        route_results.append((zero_possible, one_answers))
    return route_results


def enumerate_answers(item, stop_after=2):
    """Enumerate distinct answers admitted by all public constraints.

    `stop_after` bounds work for validation: once that many different answers
    exist, uniqueness has already failed.  Use None to enumerate them all.
    """
    nodes = item["nodes"]
    answers = set()

    # Distinct rates are a public global constraint.  The sum of local
    # assignment lower bounds cannot exceed the single allowed bad record.
    def visit(index, clocks, used_rates, lower_bound):
        if stop_after is not None and len(answers) >= stop_after:
            return
        if index == len(nodes):
            route_results = _route_options(item, clocks, node_map)
            # Exactly one route uses a cost-1 assignment; every other route
            # must admit a cost-0 assignment.
            for chosen, (_, route_answers) in enumerate(route_results):
                if not route_answers:
                    continue
                if all(
                    other == chosen or route_results[other][0]
                    for other in range(len(route_results))
                ):
                    answers.update(route_answers)
                    if stop_after is not None and len(answers) >= stop_after:
                        return
            return

        node = nodes[index]
        for rate, offset, mismatch in candidates[node]:
            if rate in used_rates or lower_bound + mismatch > 1:
                continue
            clocks[node] = (rate, offset)
            visit(index + 1, clocks, used_rates | {rate}, lower_bound + mismatch)
            del clocks[node]

    log_routes = Counter(
        (r["node"], r["peer"]) for r in item["logs"] if r["kind"] == "send"
    )
    manifest_routes = Counter(
        (m["source"], m["destination"]) for m in item["manifests"]
    )
    for mapped_order in permutations(item["manifest_nodes"]):
        if stop_after is not None and len(answers) >= stop_after:
            break
        node_map = dict(zip(nodes, mapped_order))
        mapped_routes = Counter({
            (node_map[source], node_map[destination]): count
            for (source, destination), count in log_routes.items()
        })
        if mapped_routes != manifest_routes:
            continue
        candidates = {node: _local_candidates(item, node, node_map) for node in nodes}
        if any(not candidates[node] for node in nodes):
            continue
        visit(0, {}, set(), 0)
    return {
        (record_id, corrected_tick)
        for record_id, corrected_tick in answers
    }


def validate_public_item(item):
    required = {"id", "modulus", "allowed_rates", "nodes", "manifest_nodes", "manifests", "logs"}
    if set(item) != required:
        raise ValueError(f"{item.get('id', '<unknown>')}: wrong item keys")
    if len(item["nodes"]) != len(item["allowed_rates"]):
        raise ValueError(f"{item['id']}: rate/node count differs")
    if len(set(item["nodes"])) != len(item["nodes"]):
        raise ValueError(f"{item['id']}: duplicate nodes")
    if len(item["manifest_nodes"]) != len(item["nodes"]) or len(set(item["manifest_nodes"])) != len(item["manifest_nodes"]):
        raise ValueError(f"{item['id']}: malformed manifest node names")
    if len(set(item["allowed_rates"])) != len(item["allowed_rates"]):
        raise ValueError(f"{item['id']}: duplicate rates")
    if item["modulus"] <= max(item["allowed_rates"]):
        raise ValueError(f"{item['id']}: invalid modulus")

    manifest_ids = [m["manifest_id"] for m in item["manifests"]]
    if len(manifest_ids) != len(set(manifest_ids)):
        raise ValueError(f"{item['id']}: duplicate manifest id")
    for m in item["manifests"]:
        if set(m) != {"manifest_id", "source", "destination", "send_time", "receive_time"}:
            raise ValueError(f"{item['id']}: wrong manifest keys")
        if m["source"] not in item["manifest_nodes"] or m["destination"] not in item["manifest_nodes"]:
            raise ValueError(f"{item['id']}: unknown manifest node")
        if m["source"] == m["destination"] or m["send_time"] >= m["receive_time"]:
            raise ValueError(f"{item['id']}: invalid manifest timing")

    record_ids = [r["record_id"] for r in item["logs"]]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError(f"{item['id']}: duplicate record id")
    by_packet = defaultdict(list)
    for r in item["logs"]:
        if set(r) != {"record_id", "node", "packet", "kind", "peer", "tick"}:
            raise ValueError(f"{item['id']}: wrong log keys")
        if r["node"] not in item["nodes"] or r["peer"] not in item["nodes"]:
            raise ValueError(f"{item['id']}: unknown log node")
        if r["kind"] not in {"send", "receive"} or not 0 <= r["tick"] < item["modulus"]:
            raise ValueError(f"{item['id']}: invalid log record")
        by_packet[r["packet"]].append(r)
    if len(by_packet) != len(item["manifests"]):
        raise ValueError(f"{item['id']}: packet/manifest count differs")
    for packet, records in by_packet.items():
        if len(records) != 2 or {r["kind"] for r in records} != {"send", "receive"}:
            raise ValueError(f"{item['id']}: malformed packet {packet}")
        send = next(r for r in records if r["kind"] == "send")
        receive = next(r for r in records if r["kind"] == "receive")
        if send["node"] != receive["peer"] or send["peer"] != receive["node"]:
            raise ValueError(f"{item['id']}: packet endpoints disagree")
