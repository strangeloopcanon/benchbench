# HolonomyWeave Problem Specification

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
