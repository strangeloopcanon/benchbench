#!/usr/bin/env python3
"""Private package support for generating and auditing AuditWeave instances."""

from __future__ import annotations

import itertools
import json
from collections import defaultdict

REGS = ("a", "b", "c", "d", "e")
MOD = 97


def freeze(state):
    return tuple(state["v"][r] for r in REGS) + tuple(state["bits"])


def thaw(value):
    return {"v": dict(zip(REGS, value[:5])), "bits": list(value[5:9])}


def apply_op(frozen, op):
    s = thaw(frozen)
    v, bits = s["v"], s["bits"]
    kind = op["op"]
    if kind == "add":
        v[op["x"]] = (v[op["x"]] + op["n"]) % MOD
    elif kind == "affine":
        v[op["x"]] = (op["m"] * v[op["x"]] + op["n"]) % MOD
    elif kind == "swap":
        v[op["x"]], v[op["y"]] = v[op["y"]], v[op["x"]]
    elif kind == "mix":
        x, y, n = op["x"], op["y"], op["n"]
        old_x, old_y = v[x], v[y]
        v[x] = (old_x + old_y + n) % MOD
        v[y] = (old_x + 2 * old_y + n) % MOD
    elif kind == "cas":
        x = op["x"]
        if v[x] % op["q"] == op["r"]:
            v[x] = op["yes"] % MOD
        else:
            v[x] = (v[x] + op["no"]) % MOD
    elif kind == "route":
        target = op["x"] if bits[op["bit"]] else op["y"]
        v[target] = (v[target] + op["n"]) % MOD
    elif kind == "toggle":
        bits[op["bit"]] ^= 1
    elif kind == "flip_if":
        if v[op["x"]] % op["q"] == op["r"]:
            bits[op["bit"]] ^= 1
    else:
        raise ValueError(f"unknown operation {kind!r}")
    return freeze(s)


def event_op(event, candidate_label=None):
    if "op" in event:
        return event["op"]
    for c in event["candidates"]:
        if c["label"] == candidate_label:
            return c["op"]
    raise ValueError("candidate label not present")


def topological_orders(events, edges):
    ids = [e["eid"] for e in events]
    before = {eid: set() for eid in ids}
    for x, y in edges:
        if x not in before or y not in before or x == y:
            raise ValueError("bad precedence edge")
        before[y].add(x)
    out = []

    def visit(prefix, remaining):
        if not remaining:
            out.append(tuple(prefix))
            return
        ready = sorted(e for e in remaining if before[e].isdisjoint(remaining))
        if not ready:
            raise ValueError("cyclic precedence graph")
        for eid in ready:
            visit(prefix + [eid], remaining - {eid})

    visit([], set(ids))
    return out


def audit_value(frozen, audit):
    vals, bits = frozen[:5], frozen[5:]
    kind = audit["kind"]
    if kind == "linear":
        total = sum(w * x for w, x in zip(audit["weights"], vals))
        total += sum(w * b for w, b in zip(audit["bit_weights"], bits))
        return total % audit["mod"]
    if kind == "quadratic":
        total = sum(w * x * x for w, x in zip(audit["weights"], vals))
        total += sum(w * b for w, b in zip(audit["bit_weights"], bits))
        return total % audit["mod"]
    if kind == "probe":
        return vals[REGS.index(audit["x"])] % audit["mod"]
    if kind == "bit_code":
        return sum((i + 1) * b for i, b in enumerate(bits)) % audit["mod"]
    raise ValueError("bad audit kind")


def audits_match(frozen, audits):
    return all(audit_value(frozen, a) == a["value"] for a in audits)


def render_answer(label, frozen):
    vals = ",".join(str(x) for x in frozen[:5])
    bit_string = "".join(str(x) for x in frozen[5:])
    return f"{label}|{vals}|{bit_string}"


def solve_public_item(item, state_cap=200000):
    """Return answer -> witness count using only solver-visible information."""
    initial = freeze(item["initial"])
    labels = None
    phase_orders = []
    phase_maps = []
    for phase in item["phases"]:
        phase_orders.append(topological_orders(phase["events"], phase["before"]))
        phase_maps.append({e["eid"]: e for e in phase["events"]})
        for e in phase["events"]:
            if "candidates" in e:
                these = tuple(c["label"] for c in e["candidates"])
                if labels is not None:
                    raise ValueError("more than one disputed event")
                labels = these
    if labels is None or len(labels) != 4:
        raise ValueError("expected exactly four candidates")

    frontier = {(label, initial): 1 for label in labels}
    for pidx, phase in enumerate(item["phases"]):
        next_frontier = defaultdict(int)
        emap = phase_maps[pidx]
        for (label, state), count in frontier.items():
            for order in phase_orders[pidx]:
                cur = state
                for eid in order:
                    cur = apply_op(cur, event_op(emap[eid], label))
                if audits_match(cur, phase["audits"]):
                    next_frontier[(label, cur)] += count
        frontier = next_frontier
        if not frontier:
            return {}
        if len(frontier) > state_cap:
            raise RuntimeError("state cap exceeded")

    answers = defaultdict(int)
    for (label, state), count in frontier.items():
        cur = state
        for op in item["query_ops"]:
            cur = apply_op(cur, op)
        answers[render_answer(label, cur)] += count
    return dict(answers)


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))
