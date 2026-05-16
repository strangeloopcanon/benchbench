#!/usr/bin/env python3
"""Generate Protocol Archaeology benchmark items.

The solver sees input/output traces from an unknown byte protocol and must
infer the response for one held-out query. Gold answers and audit traces are
kept outside the solver bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


OPS = ("mix", "gate", "permute", "sbox", "fold")
SBOX = [0x6, 0x4, 0xC, 0x5, 0x0, 0x7, 0x2, 0xE, 0x1, 0xF, 0x3, 0xD, 0x8, 0xA, 0x9, 0xB]


def rotl8(x: int, k: int) -> int:
    k %= 8
    return ((x << k) | (x >> (8 - k))) & 0xFF


def bhex(bs: list[int]) -> str:
    return "".join(f"{b:02x}" for b in bs)


def parse_hex(s: str) -> list[int]:
    return [int(s[i : i + 2], 16) for i in range(0, len(s), 2)]


def apply_program(packet: list[int], params: dict) -> list[int]:
    r = packet[:]
    salts = params["salts"]
    weights = params["weights"]
    perm = params["perm"]
    gates = params["gates"]

    # mix: local diffusion with position-specific salts.
    r = [(rotl8(r[i] ^ salts[i], (weights[i] % 7) + 1) + r[(i - 1) % 8]) & 0xFF for i in range(8)]

    # gate: two data-dependent swaps; branch is visible only through examples.
    for a, b, mask in gates:
        if bin(r[a] & mask).count("1") % 2:
            r[a], r[b] = r[b], r[a]
        else:
            r[b] = (r[b] ^ rotl8(r[a], mask.bit_count())) & 0xFF

    # permute: fixed per-item register permutation.
    r = [r[i] for i in perm]

    # sbox: nibble substitution with salt-coupled cross talk.
    r = [((SBOX[(x >> 4) & 0xF] << 4) | SBOX[x & 0xF]) ^ salts[(i + 3) % 8] for i, x in enumerate(r)]

    # fold: produce a compact 4-byte authenticator.
    out = []
    for j in range(4):
        acc = (0x31 + salts[j]) & 0xFF
        for i, x in enumerate(r):
            acc = (acc + ((x ^ weights[(i + j) % 8]) * (i + 1 + j))) & 0xFF
            acc = rotl8(acc, (i + weights[j]) % 5 + 1)
        out.append(acc)
    return out


def make_packet(rng: random.Random, item_idx: int, example_idx: int) -> list[int]:
    seed = hashlib.sha256(f"packet:{item_idx}:{example_idx}:{rng.random()}".encode()).digest()
    return list(seed[:8])


def make_params(rng: random.Random) -> dict:
    perm = list(range(8))
    rng.shuffle(perm)
    gates = []
    for _ in range(2):
        a, b = rng.sample(range(8), 2)
        mask = rng.choice([0x13, 0x25, 0x49, 0x8A, 0xC3, 0x5C, 0xA6])
        gates.append([a, b, mask])
    return {
        "salts": [rng.randrange(256) for _ in range(8)],
        "weights": [rng.randrange(1, 32) for _ in range(8)],
        "perm": perm,
        "gates": gates,
        "ops": list(OPS),
    }


def make_item(rng: random.Random, idx: int) -> tuple[dict, dict, dict]:
    params = make_params(rng)
    examples = []
    seen = set()
    for ex_idx in range(14):
        packet = make_packet(rng, idx, ex_idx)
        while bhex(packet) in seen:
            packet = [rng.randrange(256) for _ in range(8)]
        seen.add(bhex(packet))
        examples.append({"packet": bhex(packet), "response": bhex(apply_program(packet, params))})

    query = make_packet(rng, idx, 999)
    while bhex(query) in seen:
        query = [rng.randrange(256) for _ in range(8)]
    answer = bhex(apply_program(query, params))
    item_id = f"pa-{idx:04d}"
    item = {
        "id": item_id,
        "protocol_note": (
            "An 8-byte sensor packet is transformed into a 4-byte response by one "
            "unknown deterministic firmware path. The path uses byte rotations, "
            "xor/add mixing, two parity-gated register updates, one register "
            "permutation, nibble substitution, and a folded checksum. Infer only "
            "the response for the query packet from the observed traces."
        ),
        "answer_format": "exactly 8 lowercase hex characters",
        "examples": examples,
        "query_packet": bhex(query),
    }
    gold = {"id": item_id, "answer": answer}
    audit = {"id": item_id, "params": params, "query_packet": bhex(query), "answer": answer}
    return item, gold, audit


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-count", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir)
    solver = out / "solver_bundle"
    solver.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    items, gold, audit = [], [], []
    for idx in range(args.sample_count):
        item, gold_row, audit_row = make_item(rng, idx)
        items.append(item)
        gold.append(gold_row)
        audit.append(audit_row)

    write_jsonl(solver / "items_private_sample.jsonl", items)
    write_jsonl(out / "gold_private_sample.jsonl", gold)
    write_jsonl(out / "private_audit_traces.jsonl", audit)

    manifest = {
        "benchmark": "protocol_archaeology",
        "version": "0.1.0",
        "item_file": "items_private_sample.jsonl",
        "sample_count": args.sample_count,
        "prediction_schema": {"id": "string", "answer": "8 lowercase hex characters"},
        "forbidden": [
            "Do not inspect files outside this solver_bundle.",
            "Do not use generator.py, scorer.py, verifier.py, gold files, audit traces, or hidden seeds.",
        ],
    }
    (solver / "SOLVER_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
