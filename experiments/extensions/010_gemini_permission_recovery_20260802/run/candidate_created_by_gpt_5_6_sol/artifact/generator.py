#!/usr/bin/env python3
"""Deterministically generate AuditWeave benchmark samples."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from auditweave_core import REGS, apply_op, audit_value, freeze, render_answer, solve_public_item


def random_op(rng):
    kind = rng.choices(
        ["add", "affine", "swap", "mix", "cas", "route", "toggle", "flip_if"],
        weights=[15, 13, 9, 10, 12, 12, 8, 11],
    )[0]
    x, y = rng.sample(REGS, 2)
    if kind == "add":
        return {"op": kind, "x": x, "n": rng.randrange(-24, 25) or 7}
    if kind == "affine":
        return {"op": kind, "x": x, "m": rng.choice([2, 3, 5, 7]), "n": rng.randrange(-15, 16)}
    if kind == "swap":
        return {"op": kind, "x": x, "y": y}
    if kind == "mix":
        return {"op": kind, "x": x, "y": y, "n": rng.randrange(-12, 13)}
    if kind == "cas":
        q = rng.choice([3, 4, 5, 7])
        return {"op": kind, "x": x, "q": q, "r": rng.randrange(q), "yes": rng.randrange(97), "no": rng.randrange(-13, 14) or 4}
    if kind == "route":
        return {"op": kind, "bit": rng.randrange(4), "x": x, "y": y, "n": rng.randrange(-18, 19) or 6}
    if kind == "toggle":
        return {"op": kind, "bit": rng.randrange(4)}
    q = rng.choice([2, 3, 4, 5])
    return {"op": kind, "bit": rng.randrange(4), "x": x, "q": q, "r": rng.randrange(q)}


def distinct_ops(rng, true_op):
    seen = {json.dumps(true_op, sort_keys=True)}
    ops = [true_op]
    while len(ops) < 4:
        op = random_op(rng)
        key = json.dumps(op, sort_keys=True)
        if key not in seen:
            seen.add(key)
            ops.append(op)
    rng.shuffle(ops)
    return ops


def make_audits(rng, state, phase_index):
    specs = []
    if phase_index == 0:
        specs.append({"kind": "linear", "weights": [rng.randrange(1, 13) for _ in range(5)], "bit_weights": [rng.randrange(1, 13) for _ in range(4)], "mod": 13})
        specs.append({"kind": "probe", "x": rng.choice(REGS), "mod": 5})
    elif phase_index == 1:
        specs.append({"kind": "quadratic", "weights": [rng.randrange(1, 17) for _ in range(5)], "bit_weights": [rng.randrange(1, 17) for _ in range(4)], "mod": 17})
        specs.append({"kind": "linear", "weights": [rng.randrange(1, 19) for _ in range(5)], "bit_weights": [rng.randrange(1, 19) for _ in range(4)], "mod": 19})
    else:
        specs.append({"kind": "linear", "weights": [rng.randrange(1, 23) for _ in range(5)], "bit_weights": [rng.randrange(1, 23) for _ in range(4)], "mod": 23})
        specs.append({"kind": "quadratic", "weights": [rng.randrange(1, 29) for _ in range(5)], "bit_weights": [rng.randrange(1, 29) for _ in range(4)], "mod": 29})
        specs.append({"kind": "bit_code", "mod": 7})
    for spec in specs:
        spec["value"] = audit_value(state, spec)
    return specs


def make_candidate(rng, item_index, attempt):
    initial_obj = {"v": {r: rng.randrange(97) for r in REGS}, "bits": [rng.randrange(2) for _ in range(4)]}
    state = freeze(initial_obj)
    hole_phase = rng.randrange(3)
    hole_pos = rng.randrange(6)
    phases = []
    true_label = None
    for pidx in range(3):
        ids = [f"p{pidx + 1}e{i + 1}" for i in range(6)]
        actual_order = ids[:]
        rng.shuffle(actual_order)
        raw_ops = [random_op(rng) for _ in ids]
        events = []
        actual_by_id = {}
        for i, eid in enumerate(ids):
            true_op = raw_ops[i]
            actual_by_id[eid] = true_op
            if pidx == hole_phase and i == hole_pos:
                options = distinct_ops(rng, true_op)
                labels = ["A", "B", "C", "D"]
                candidates = [{"label": lab, "op": op} for lab, op in zip(labels, options)]
                true_label = labels[options.index(true_op)]
                events.append({"eid": eid, "candidates": candidates})
            else:
                events.append({"eid": eid, "op": true_op})
        edges = []
        for i in range(6):
            for j in range(i + 1, 6):
                if rng.random() < 0.42:
                    edges.append([actual_order[i], actual_order[j]])
        # Always include two true-order edges while keeping plenty of concurrency.
        for i in rng.sample(range(5), 2):
            edge = [actual_order[i], actual_order[i + 1]]
            if edge not in edges:
                edges.append(edge)
        for eid in actual_order:
            state = apply_op(state, actual_by_id[eid])
        phases.append({"phase": pidx + 1, "events": events, "before": sorted(edges), "audits": make_audits(rng, state, pidx)})
    query_ops = [random_op(rng) for _ in range(rng.randrange(4, 7))]
    item = {
        "id": f"aw-{item_index + 1:03d}",
        "initial": initial_obj,
        "phases": phases,
        "query_ops": query_ops,
        "answer_format": "LABEL|a,b,c,d,e|b0b1b2b3",
    }
    answers = solve_public_item(item)
    if len(answers) != 1:
        return None
    answer = next(iter(answers))
    if not answer.startswith(true_label + "|"):
        raise AssertionError("public reconstruction disagrees with planted trace")
    return item, answer, sum(answers.values())


def generate(count, seed):
    rng = random.Random(seed)
    items, gold, witness_counts = [], [], []
    attempts = 0
    while len(items) < count:
        attempts += 1
        if attempts > count * 500:
            raise RuntimeError("unable to generate enough uniquely identifiable items")
        made = make_candidate(rng, len(items), attempts)
        if made is None:
            continue
        item, answer, witnesses = made
        items.append(item)
        gold.append({"id": item["id"], "answer": answer})
        witness_counts.append(witnesses)
    return items, gold, witness_counts, attempts


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-count", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    if args.sample_count < 1:
        raise SystemExit("sample-count must be positive")
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bundle = out / "solver_bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    items, gold, witness_counts, attempts = generate(args.sample_count, args.seed)
    write_jsonl(out / "gold_private_sample.jsonl", gold)
    write_jsonl(bundle / "items_private_sample.jsonl", items)
    manifest = {
        "schema_version": 1,
        "benchmark": "AuditWeave",
        "item_file": "items_private_sample.jsonl",
        "item_count": len(items),
        "solver_instructions": "solver_packet.md",
        "answer_record_schema": {"id": "string", "answer": "string"},
    }
    (bundle / "SOLVER_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    packet_source = Path(__file__).with_name("solver_packet_template.md")
    if not packet_source.exists():
        raise SystemExit("solver_packet_template.md is required to generate the bundle")
    (bundle / "solver_packet.md").write_text(packet_source.read_text(encoding="utf-8"), encoding="utf-8")
    audit = {"accepted_items": len(items), "attempts": attempts, "witness_count_min": min(witness_counts), "witness_count_max": max(witness_counts)}
    (out / "generation_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"generated": len(items), "attempts": attempts, "out_dir": str(out)}))


if __name__ == "__main__":
    main()
