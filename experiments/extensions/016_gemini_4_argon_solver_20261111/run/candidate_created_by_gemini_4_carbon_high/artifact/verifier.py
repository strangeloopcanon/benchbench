#!/usr/bin/env python3
"""Independent Bellman-Ford instance verifier and solver-bundle auditor for HolonomyWeave."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

INT_RE = re.compile(r"^-?[0-9]+$")


def parse_canonical_int(val: Any) -> tuple[bool, int | None]:
    if isinstance(val, bool):
        return False, None
    if isinstance(val, int):
        return True, val
    if isinstance(val, str):
        s = val.strip()
        if INT_RE.match(s):
            return True, int(s)
    return False, None


def load_gold_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"gold file not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            obj = json.loads(stripped)
            if not isinstance(obj, dict) or "id" not in obj or "answer" not in obj:
                raise ValueError(f"gold line {line_no}: expected JSON object with 'id' and 'answer'")
            if not isinstance(obj["id"], str) or not obj["id"]:
                raise ValueError(f"gold line {line_no}: 'id' must be a non-empty string")
            rows.append(obj)
    return rows


def score_predictions_inline(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    gold_rows = load_gold_rows(gold_path)
    gold_map: dict[str, int] = {}
    for row in gold_rows:
        ok, parsed = parse_canonical_int(row["answer"])
        if not ok or parsed is None:
            raise ValueError(f"Non-integer gold answer for {row['id']}")
        gold_map[row["id"]] = parsed
    if not pred_path.is_file():
        raise FileNotFoundError(f"predictions file not found: {pred_path}")
    pred_map: dict[str, Any] = {}
    with pred_path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and isinstance(obj.get("id"), str) and "answer" in obj:
                pred_map[obj["id"]] = obj["answer"]
    total = int(len(gold_map))
    correct = 0
    for item_id, gold_val in gold_map.items():
        if item_id in pred_map:
            ok, pv = parse_canonical_int(pred_map[item_id])
            if ok and pv == gold_val:
                correct += 1
    correct = int(correct)
    return {
        "schema_version": 2,
        "benchmark": "holonomy_weave",
        "total": total,
        "correct": correct,
        "accuracy": float(correct / total) if total > 0 else 0.0,
    }

FORBIDDEN_ITEM_KEYS = {
    "answer",
    "gold",
    "solution",
    "label",
    "target",
    "expected",
    "ground_truth",
    "secret",
    "witness",
}

ALLOWED_BUNDLE_FILES = {
    "README.md",
    "SOLVER_MANIFEST.json",
    "items_private_sample.jsonl",
    "solver_packet.md",
}


def bellman_ford_verify_item(item: dict[str, Any]) -> int:
    """Independently solve an item from public graph fields via Bellman-Ford and certify walks."""
    graph = item["graph"]
    num_vertices = int(graph["num_vertices"])
    modulus = int(graph["modulus"])
    source = int(graph["source"])
    sink = int(graph["sink"])
    queries = graph["queries"]
    edges = graph["edges"]

    if num_vertices < 2 or modulus < 3:
        raise ValueError(f"Invalid graph dimensions: N={num_vertices}, M={modulus}")
    if not (0 <= source < num_vertices and 0 <= sink < num_vertices and source != sink):
        raise ValueError(f"Invalid endpoints: source={source}, sink={sink}, N={num_vertices}")
    if not isinstance(queries, list) or len(queries) != 3:
        raise ValueError("Expected exact 3 holonomy queries")

    edge_lookup: dict[tuple[int, int], tuple[int, int, int]] = {}
    adj: list[list[tuple[int, int, int, int]]] = [[] for _ in range(num_vertices)]
    for raw_e in edges:
        if not isinstance(raw_e, list) or len(raw_e) != 5:
            raise ValueError(f"Malformed edge tuple: {raw_e!r}")
        u, v, se, re, we = (int(x) for x in raw_e)
        if not (0 <= u < num_vertices and 0 <= v < num_vertices and u != v):
            raise ValueError(f"Invalid edge endpoints: ({u}, {v})")
        if se not in (-1, 1):
            raise ValueError(f"Invalid parity twist {se}")
        if not (0 <= re < modulus):
            raise ValueError(f"Invalid shift {re} for modulus {modulus}")
        if we <= 0:
            raise ValueError(f"Non-positive edge weight {we}")
        if (u, v) in edge_lookup:
            raise ValueError(f"Duplicate directed edge ({u}, {v})")
        edge_lookup[(u, v)] = (se, re, we)
        adj[u].append((v, se, re, we))

    inf = 10**18
    start_state = (source, 1, 0)
    dist: dict[tuple[int, int, int], int] = {start_state: 0}
    parent: dict[tuple[int, int, int], tuple[tuple[int, int, int], tuple[int, int, int, int, int]]] = {}

    max_rounds = 2 * num_vertices * modulus
    for _ in range(max_rounds):
        next_dist = dict(dist)
        changed = False
        for (u, su, ru), d_u in dist.items():
            for v, se, re, we in adj[u]:
                sv = su * se
                rv = (ru + su * re) % modulus
                nd = d_u + we
                nxt = (v, sv, rv)
                if nd < next_dist.get(nxt, inf):
                    next_dist[nxt] = nd
                    parent[nxt] = ((u, su, ru), (u, v, se, re, we))
                    changed = True
        dist = next_dist
        if not changed:
            break

    # Verify Bellman optimality inequalities across all lifted edges
    for (u, su, ru), d_u in dist.items():
        for v, se, re, we in adj[u]:
            nxt = (v, su * se, (ru + su * re) % modulus)
            if dist.get(nxt, inf) > d_u + we:
                raise RuntimeError(f"Optimality inequality violated on transition to {nxt}")

    query_distances: list[int] = []
    seen_queries: set[tuple[int, int]] = set()
    for q in queries:
        if not isinstance(q, list) or len(q) != 2:
            raise ValueError(f"Malformed query {q!r}")
        sq, rq = int(q[0]), int(q[1])
        if sq not in (-1, 1) or not (0 <= rq < modulus):
            raise ValueError(f"Invalid query state ({sq}, {rq})")
        if (sq, rq) in seen_queries:
            raise ValueError(f"Duplicate query state ({sq}, {rq})")
        seen_queries.add((sq, rq))

        goal = (sink, sq, rq)
        if goal not in dist:
            raise RuntimeError(f"Queried state {goal} is unreachable")
        d_opt = dist[goal]
        if not (0 < d_opt < 10000):
            raise RuntimeError(f"Distance {d_opt} outside packing bounds")

        # Reconstruct and forward-simulate primal witness walk
        walk_edges: list[tuple[int, int, int, int, int]] = []
        cur = goal
        steps = 0
        while cur != start_state:
            if cur not in parent or steps > max_rounds:
                raise RuntimeError(f"Failed to reconstruct witness walk for {goal}")
            prev_state, edge_used = parent[cur]
            walk_edges.append(edge_used)
            cur = prev_state
            steps += 1
        walk_edges.reverse()

        sim_u = source
        sim_s, sim_r = 1, 0
        sim_cost = 0
        for u, v, se, re, we in walk_edges:
            if u != sim_u or edge_lookup.get((u, v)) != (se, re, we):
                raise RuntimeError("Invalid edge in reconstructed walk")
            prev_s = sim_s
            sim_s = prev_s * se
            sim_r = (sim_r + prev_s * re) % modulus
            sim_u = v
            sim_cost += we
        if (sim_u, sim_s, sim_r) != goal or sim_cost != d_opt:
            raise RuntimeError("Forward walk simulation mismatch")

        query_distances.append(d_opt)

    return query_distances[0] * 100_000_000 + query_distances[1] * 10_000 + query_distances[2]


def check_no_forbidden_keys(obj: Any, path_prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for k, val in obj.items():
            key_lower = str(k).lower()
            cur_path = f"{path_prefix}.{k}" if path_prefix else str(k)
            if key_lower in FORBIDDEN_ITEM_KEYS:
                hits.append(cur_path)
            hits.extend(check_no_forbidden_keys(val, cur_path))
    elif isinstance(obj, list):
        for idx, elem in enumerate(obj):
            hits.extend(check_no_forbidden_keys(elem, f"{path_prefix}[{idx}]"))
    return hits


def verify_package(items_path: Path, gold_path: Path, bundle_dir: Path) -> dict[str, Any]:
    gold_rows = load_gold_rows(gold_path)
    gold_map: dict[str, int] = {}
    for row in gold_rows:
        item_id = row["id"]
        if set(row.keys()) != {"id", "answer"}:
            raise ValueError(f"Gold row {item_id} must have exact keys {{'id', 'answer'}}")
        ok, ans = parse_canonical_int(row["answer"])
        if not ok or ans is None:
            raise ValueError(f"Non-integer gold answer for {item_id}")
        if item_id in gold_map:
            raise ValueError(f"Duplicate gold id {item_id}")
        gold_map[item_id] = ans

    if not items_path.is_file():
        raise FileNotFoundError(f"Items file not found: {items_path}")

    items: list[dict[str, Any]] = []
    forbidden_key_hits: list[str] = []
    with items_path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            obj = json.loads(stripped)
            if not isinstance(obj, dict):
                raise ValueError(f"Items line {line_no}: expected JSON object")
            for req in ("id", "tier", "prompt", "graph"):
                if req not in obj:
                    raise ValueError(f"Items line {line_no}: missing key {req!r}")
            forbidden_key_hits.extend(check_no_forbidden_keys(obj, f"line_{line_no}"))
            items.append(obj)

    if len(items) != len(gold_map):
        raise ValueError(f"Item count ({len(items)}) != gold count ({len(gold_map)})")

    verified = 0
    mismatches: list[dict[str, Any]] = []
    for item, gold_row in zip(items, gold_rows):
        item_id = item["id"]
        if item_id != gold_row["id"]:
            raise ValueError(f"ID order mismatch: {item_id} vs {gold_row['id']}")
        derived = bellman_ford_verify_item(item)
        expected = gold_map[item_id]
        if derived == expected:
            verified += 1
        else:
            mismatches.append({"id": item_id, "derived": derived, "gold": expected})

    # Audit solver_bundle isolation and leak scan
    leak_matches: list[str] = list(forbidden_key_hits)
    bundle_files: list[str] = []
    if bundle_dir.is_dir():
        gold_strings = {str(v) for v in gold_map.values()}
        for fp in sorted(bundle_dir.rglob("*")):
            if fp.is_file():
                rel = fp.relative_to(bundle_dir).as_posix()
                bundle_files.append(rel)
                if rel not in ALLOWED_BUNDLE_FILES:
                    leak_matches.append(f"unexpected_bundle_file:{rel}")
                text = fp.read_text(encoding="utf-8")
                for gs in gold_strings:
                    if gs in text:
                        leak_matches.append(f"gold_value_leak:{rel}:{gs}")
    else:
        leak_matches.append("missing_solver_bundle_dir")

    distinct_answers = len(set(gold_map.values()))
    total = int(len(gold_map))
    correct = int(verified)
    valid = (
        total > 0
        and correct == total
        and not mismatches
        and not leak_matches
        and distinct_answers == total
    )

    return {
        "schema_version": 2,
        "benchmark": "holonomy_weave",
        "status": "ok" if valid else "failed",
        "valid": valid,
        "total": total,
        "correct": correct,
        "accuracy": float(correct / total) if total > 0 else 0.0,
        "distinct_gold_answers": distinct_answers,
        "solver_bundle_files": bundle_files,
        "leak_scan_matches": leak_matches,
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify HolonomyWeave package and instances.")
    parser.add_argument(
        "--root",
        "--dir",
        "--out-dir",
        dest="root",
        type=Path,
        default=Path("."),
        help="Benchmark root directory (default: current directory).",
    )
    parser.add_argument("--items", type=Path, default=None, help="Path to items JSONL.")
    parser.add_argument("--gold", type=Path, default=None, help="Path to gold JSONL.")
    parser.add_argument(
        "--solver-bundle",
        "--bundle",
        dest="bundle",
        type=Path,
        default=None,
        help="Path to solver_bundle directory.",
    )
    parser.add_argument(
        "--predictions",
        "--pred",
        "--preds",
        dest="predictions",
        type=Path,
        default=None,
        help="Optional predictions JSONL to score.",
    )
    parser.add_argument(
        "--out",
        "--output",
        "-o",
        dest="out",
        type=Path,
        default=None,
        help="Optional output JSON report path.",
    )
    args = parser.parse_args()

    gold_path = args.gold if args.gold is not None else (args.root / "gold_private_sample.jsonl")

    if args.predictions is not None:
        report = score_predictions_inline(gold_path, args.predictions)
        payload = json.dumps(report, indent=2)
        if args.out is not None:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(payload + "\n")
        print(payload)
        return 0

    bundle_dir = args.bundle if args.bundle is not None else (args.root / "solver_bundle")
    items_path = (
        args.items if args.items is not None else (bundle_dir / "items_private_sample.jsonl")
    )

    report = verify_package(items_path=items_path, gold_path=gold_path, bundle_dir=bundle_dir)
    payload = json.dumps(report, indent=2)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload + "\n")
    print(payload)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
