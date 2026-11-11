#!/usr/bin/env python3
"""Deterministic parametric instance generator for HolonomyWeave."""

from __future__ import annotations

import argparse
import heapq
import json
import sys
from pathlib import Path
from typing import Any

SOLVER_PACKET_MD = """# HolonomyWeave Problem Specification

## 1. Dihedral Gauge Weave

Each item in `items_private_sample.jsonl` specifies a finite directed graph on `N` vertices `0, 1, ..., N-1` equipped with an integer modulus `M >= 3`, a `source` vertex, a `sink` vertex, three query fiber states `queries = [[s0, r0], [s1, r1], [s2, r2]]`, and a list of directed edges `[u, v, se, re, we]`.

### Fiber State Space and Parallel Transport

A fiber state is a pair `(s, r)` where:
- `s in {-1, 1}` is the orientation parity, and
- `r in {0, 1, ..., M-1}` is the modular shift.

Every walk starting at `source` begins in the identity fiber state `(1, 0)` with total cost `0`.
When a walk in current fiber state `(s, r)` traverses a directed edge `[u, v, se, re, we]` (`u -> v`), the new fiber state at `v` is:

```
s_next = s * se
r_next = (r + s * re) mod M
```

where `x mod M` denotes the canonical non-negative remainder in `{0, 1, ..., M-1}` (i.e. `x % M` in Python), and the walk cost increases by the positive integer `we >= 1`.

Walks are **not** restricted to simple paths in the base graph: directed cycles may be traversed any number of times to reach a desired fiber state at `sink`.

## 2. Objective and Integer Packing

For each queried fiber state `[sq, rq]` in `queries`, let `d(sq, rq)` denote the minimum total edge cost over all finite directed walks from `source` to `sink` whose final fiber state upon arriving at `sink` equals `(sq, rq)`. All queried states are guaranteed reachable with `0 < d(sq, rq) < 10000`.

Given `queries = [[s0, r0], [s1, r1], [s2, r2]]`, return the exact integer:

```
d(s0, r0) * 100000000 + d(s1, r1) * 10000 + d(s2, r2)
```

## 3. Worked Toy Example

Suppose `N = 3`, `M = 4`, `source = 0`, `sink = 2`, `queries = [[1, 0], [-1, 1], [1, 3]]`, and edges:
- `[0, 1, -1, 1, 5]`
- `[1, 1, 1, 1, 8]`
- `[1, 2, -1, 0, 7]`
- `[1, 2, 1, 0, 22]`

Tracing walks from `0` (initial state `(1, 0)`):
1. Edge `0 -> 1` (`se=-1, re=1, w=5`) reaches vertex `1` in state `(1*(-1), (0 + 1*1) mod 4) = (-1, 1)` with cost `5`.
2. Taking `1 -> 2` (`se=-1, re=0, w=7`) from state `(-1, 1)` reaches `2` in state `(1, 1)` with cost `12`.
3. Taking `1 -> 2` (`se=1, re=0, w=22`) from state `(-1, 1)` reaches `2` in state `(-1, 1)` with cost `27`, so `d(-1, 1) = 27`.
4. Traversing loop `1 -> 1` (`se=1, re=1, w=8`) once while in state `(-1, 1)` updates `(s, r)` to `(-1, (1 + (-1)*1) mod 4) = (-1, 0)` at cost `5 + 8 = 13`; then `1 -> 2` (`se=-1, re=0, w=7`) reaches `(1, 0)` at cost `20`, so `d(1, 0) = 20`.
5. Traversing loop `1 -> 1` twice from `(-1, 1)` reaches `(-1, 3)` at cost `5 + 16 = 21`; then `1 -> 2` (`se=-1, re=0, w=7`) reaches `(1, 3)` at cost `28`, so `d(1, 3) = 28`.

Packed integer output: `20 * 100000000 + 27 * 10000 + 28 = 2000270028`.
"""


def build_solver_readme(sample_count: int) -> str:
    return (
        "# HolonomyWeave Solver Bundle\n\n"
        "This directory contains the self-contained solver inputs for **HolonomyWeave** (`holonomy_weave`).\n\n"
        "## Contents\n\n"
        "- `SOLVER_MANIFEST.json` - Bundle manifest and submission schema contract.\n"
        f"- `items_private_sample.jsonl` - {sample_count} problem instances in JSON Lines format.\n"
        "- `solver_packet.md` - Complete mathematical specification and worked toy example.\n\n"
        "## Submission Format\n\n"
        "Produce a UTF-8 JSON Lines file (e.g. `predictions.jsonl`) with one JSON object per item:\n\n"
        "```json\n"
        '{"id": "hw_001", "answer": 1200270035}\n'
        "```\n\n"
        "Rules:\n"
        '1. Every `"id"` from `items_private_sample.jsonl` must appear once.\n'
        '2. Each `"answer"` must be an exact base-10 integer (JSON integer, not float or boolean).\n'
        "3. See `solver_packet.md` for the exact dihedral parallel-transport recurrence and packing formula.\n"
    )


def build_solver_manifest(sample_count: int) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "benchmark": "holonomy_weave",
        "title": "HolonomyWeave",
        "item_count": sample_count,
        "items_file": "items_private_sample.jsonl",
        "readme_file": "README.md",
        "solver_packet_file": "solver_packet.md",
        "files": [
            "README.md",
            "SOLVER_MANIFEST.json",
            "items_private_sample.jsonl",
            "solver_packet.md",
        ],
        "answer_schema": {
            "format": "jsonl",
            "row_keys": ["id", "answer"],
            "id_type": "string",
            "answer_type": "integer",
        },
        "contains_gold_answers": False,
        "network_access_required": False,
    }


def d_mul(a: tuple[int, int], b: tuple[int, int], mod: int) -> tuple[int, int]:
    """Group multiplication in D_M = Z_2 |x Z_M."""
    return (a[0] * b[0], (a[1] + a[0] * b[1]) % mod)


def d_inv(a: tuple[int, int], mod: int) -> tuple[int, int]:
    """Group inverse in D_M = Z_2 |x Z_M."""
    return (a[0], (-a[0] * a[1]) % mod)


def solve_holonomy_dijkstra(
    num_vertices: int,
    modulus: int,
    source: int,
    sink: int,
    edges: list[list[int]],
    queries: list[list[int]],
) -> int:
    """Compute exact packed holonomy spectrum via Dijkstra on the lifted bundle V x D_M."""
    adj: list[list[tuple[int, int, int, int]]] = [[] for _ in range(num_vertices)]
    for u, v, se, re, we in edges:
        if we <= 0:
            raise ValueError(f"Edge weight must be positive, got {we}")
        adj[u].append((v, se, re, we))

    inf = 10**18
    dist: dict[tuple[int, int, int], int] = {(source, 1, 0): 0}
    pq: list[tuple[int, int, int, int]] = [(0, source, 1, 0)]

    while pq:
        d_cur, u, su, ru = heapq.heappop(pq)
        if d_cur > dist.get((u, su, ru), inf):
            continue
        for v, se, re, we in adj[u]:
            sv = su * se
            rv = (ru + su * re) % modulus
            nd = d_cur + we
            state = (v, sv, rv)
            if nd < dist.get(state, inf):
                dist[state] = nd
                heapq.heappush(pq, (nd, v, sv, rv))

    vals: list[int] = []
    for sq, rq in queries:
        key = (sink, sq, rq)
        if key not in dist:
            raise RuntimeError(f"Queried holonomy state {key} is unreachable")
        d_val = dist[key]
        if not (0 < d_val < 10000):
            raise RuntimeError(f"Distance {d_val} outside valid packing range (0, 10000)")
        vals.append(d_val)

    return vals[0] * 100_000_000 + vals[1] * 10_000 + vals[2]


def generate_item(seed: int, idx: int, sample_count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Construct a gauge-scrambled HolonomyWeave instance and solve it from public graph data."""
    seed_norm = abs(int(seed))
    s_a = seed_norm % 101
    s_b = seed_norm % 99
    sc_mod = (seed_norm % 1000) % 50

    t1_cut = max(1, sample_count // 5)
    t2_cut = max(2, (3 * sample_count) // 5)

    item_id = f"hw_{idx + 1:03d}"
    mult = 1 + ((idx + s_b) % 3)

    if idx < t1_cut:
        tier = "tier1_tractable"
        num_vertices = 6
        modulus = (5, 7)[(idx + s_a) % 2]
        b1 = 100 + s_a + 7 * idx
        b2 = 110 + s_b + 5 * idx
        b3 = 90 + sc_mod + 3 * idx
        clean_edges = [
            (0, 1, 1, 0, b1),
            (1, 3, 1, 0, b2),
            (0, 2, 1, 1, b1 + 45 * mult),
            (2, 3, 1, 0, b2),
            (1, 2, 1, 2, 80 * mult),
            (3, 4, 1, 1, 35 * mult),
            (4, 3, 1, 0, 35 * mult),
            (3, 5, 1, 0, b3),
            (4, 5, 1, 2, b3 + 95 * mult),
        ]
        queries = [[1, 1 + (idx % 2)], [1, 3], [1, modulus - 1]]
        step = 5
    elif idx < t2_cut:
        tier = "tier2_intermediate"
        num_vertices = 8
        modulus = (9, 11)[(idx + s_a) % 2]
        b1 = 80 + s_a + 4 * idx
        b2 = 70 + s_b + 3 * idx
        b3 = 90 + sc_mod + 2 * idx
        b4 = 60 + idx
        clean_edges = [
            (0, 1, 1, 0, b1),
            (1, 3, 1, 0, b2),
            (0, 2, 1, 1, b1 + 35 * mult),
            (2, 3, 1, 0, b2),
            (1, 2, 1, 2, 60 * mult),
            (3, 4, 1, 1, 40 * mult),
            (4, 3, 1, 0, 40 * mult),
            (3, 5, 1, 0, b3),
            (4, 5, 1, 2, b3 + 45 * mult),
            (5, 6, 1, modulus - 2, 35 * mult),
            (6, 5, 1, 0, 35 * mult),
            (5, 7, 1, 0, b4),
        ]
        queries = [[1, 5], [1, 6], [1, modulus - 1 - ((idx // 2) % 2)]]
        step = 3 if (idx % 2 == 0) else 5
    else:
        tier = "tier3_holonomy"
        num_vertices = 9
        modulus = (7, 9)[(idx + s_a) % 2]
        b1 = 80 + s_a + 4 * idx
        b2 = 70 + s_b + 3 * idx
        b3 = 90 + sc_mod + 2 * idx
        b4 = 60 + idx
        clean_edges = [
            (0, 1, 1, 0, b1),
            (1, 2, 1, 1, 45 * mult),
            (2, 1, 1, 0, 45 * mult),
            (1, 3, 1, 0, b2),
            (3, 5, 1, 0, b3),
            (1, 4, -1, 0, b2 + 30 * mult),
            (4, 5, 1, 0, b3),
            (3, 4, -1, 1, 50 * mult),
            (2, 3, 1, 1, b2 + 15 * mult),
            (5, 6, 1, 2, 35 * mult),
            (6, 5, 1, 0, 35 * mult),
            (5, 8, 1, 0, b4),
            (5, 7, -1, 0, b4 + 10 * mult),
            (7, 8, 1, 0, 30 * mult),
        ]
        queries = [[1, 5], [1, modulus - 1], [-1, 2 + 2 * ((idx // 2) % 2)]]
        step = 2 if (idx % 2 == 0) else 5

    off = (idx + s_a) % num_vertices
    pi = [(off + step * v) % num_vertices for v in range(num_vertices)]
    phi = [10] + [((v + idx + s_b) % 4) * 5 for v in range(1, num_vertices - 1)] + [10]
    if tier == "tier3_holonomy":
        gs = [1] + [-1 if ((v + idx) % 2 == 1) else 1 for v in range(1, num_vertices - 1)] + [1]
    else:
        gs = [1] * num_vertices
    gr = [0] + [(2 * v + idx + s_a) % modulus for v in range(1, num_vertices - 1)] + [0]
    gamma = list(zip(gs, gr))

    pub_edges: list[list[int]] = []
    for u, v, sc, rc, c_clean in clean_edges:
        s_pub, r_pub = d_mul(d_mul(gamma[u], (sc, rc), modulus), d_inv(gamma[v], modulus), modulus)
        w_pub = c_clean + phi[u] - phi[v]
        pub_edges.append([pi[u], pi[v], s_pub, r_pub, w_pub])

    pub_edges.sort(key=lambda e: (e[0], e[1]))
    src_pub = pi[0]
    dst_pub = pi[num_vertices - 1]

    answer = solve_holonomy_dijkstra(
        num_vertices=num_vertices,
        modulus=modulus,
        source=src_pub,
        sink=dst_pub,
        edges=pub_edges,
        queries=queries,
    )

    edges_str = json.dumps(pub_edges, separators=(",", ":"))
    q0, q1, q2 = queries
    prompt = (
        f"HolonomyWeave {item_id} ({tier}): "
        f"Directed dihedral gauge weave on N={num_vertices} vertices 0..{num_vertices - 1}, modulus M={modulus}, source={src_pub}, sink={dst_pub}. "
        f"Fiber state (s,r) in {{-1,1}} x {{0..{modulus - 1}}} starts at (1,0) at source={src_pub}. "
        f"Each directed edge [u,v,se,re,we] transitions (s,r) -> (s*se, (r + s*re) mod {modulus}) with cost we>0; cycles may be traversed repeatedly. "
        f"Edges [u,v,se,re,we]: {edges_str}. "
        f"For minimum walk cost d(sq,rq) from {src_pub} to {dst_pub} ending in state (sq,rq), "
        f"compute d({q0[0]},{q0[1]})*100000000 + d({q1[0]},{q1[1]})*10000 + d({q2[0]},{q2[1]})."
    )

    item_row = {
        "id": item_id,
        "tier": tier,
        "prompt": prompt,
        "graph": {
            "num_vertices": num_vertices,
            "modulus": modulus,
            "source": src_pub,
            "sink": dst_pub,
            "queries": queries,
            "edges": pub_edges,
        },
    }
    gold_row = {"id": item_id, "answer": answer}
    return item_row, gold_row


def write_utf8(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def generate_dataset(sample_count: int, seed: int, out_dir: Path) -> None:
    if sample_count <= 0:
        raise ValueError(f"sample_count must be positive, got {sample_count}")

    item_lines: list[str] = []
    gold_lines: list[str] = []
    for idx in range(sample_count):
        item_row, gold_row = generate_item(seed=seed, idx=idx, sample_count=sample_count)
        item_lines.append(json.dumps(item_row, separators=(",", ":")))
        gold_lines.append(json.dumps(gold_row, separators=(",", ":")))

    bundle_dir = out_dir / "solver_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    write_utf8(out_dir / "gold_private_sample.jsonl", "\n".join(gold_lines) + "\n")
    write_utf8(bundle_dir / "items_private_sample.jsonl", "\n".join(item_lines) + "\n")
    write_utf8(
        bundle_dir / "SOLVER_MANIFEST.json",
        json.dumps(build_solver_manifest(sample_count), indent=2) + "\n",
    )
    write_utf8(bundle_dir / "README.md", build_solver_readme(sample_count))
    write_utf8(bundle_dir / "solver_packet.md", SOLVER_PACKET_MD)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate HolonomyWeave benchmark artifacts.")
    parser.add_argument(
        "--sample-count",
        "--count",
        "-n",
        dest="sample_count",
        type=int,
        default=30,
        help="Number of benchmark instances to generate (default: 30).",
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=20260516,
        help="Deterministic integer generation seed (default: 20260516).",
    )
    parser.add_argument(
        "--out-dir",
        "--output-dir",
        "-o",
        dest="out_dir",
        type=Path,
        default=Path("."),
        help="Output root directory (default: current directory).",
    )
    args = parser.parse_args()

    generate_dataset(sample_count=args.sample_count, seed=args.seed, out_dir=args.out_dir)
    summary = {
        "schema_version": 2,
        "benchmark": "holonomy_weave",
        "status": "ok",
        "seed": args.seed,
        "sample_count": args.sample_count,
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
