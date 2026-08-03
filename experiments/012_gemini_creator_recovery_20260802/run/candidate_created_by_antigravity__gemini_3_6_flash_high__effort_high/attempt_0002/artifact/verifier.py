#!/usr/bin/env python3
"""
Verifier for RADN (Reconfigurable Asynchronous Dataflow Network) Benchmark.
Validates item format, schema compliance, solver bundle isolation, and solver solvability invariants.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any

# Import RADNSimulator from generator.py to verify internal ground truth consistency
from generator import RADNSimulator


def verify_hex_sha256(val: str) -> bool:
    return bool(re.match(r"^[0-9a-f]{64}$", str(val)))


def main():
    parser = argparse.ArgumentParser(description="RADN Benchmark Verifier")
    parser.add_argument("--items", type=str, required=True, help="Path to solver items jsonl")
    parser.add_argument("--gold", type=str, required=True, help="Path to gold ground truth jsonl")
    args = parser.parse_args()

    items_path = Path(args.items)
    gold_path = Path(args.gold)

    # 1. Existence check
    if not items_path.exists():
        print(f"[FAIL] Items file not found: {items_path}")
        sys.exit(1)
    if not gold_path.exists():
        print(f"[FAIL] Gold file not found: {gold_path}")
        sys.exit(1)

    # 2. Read lines
    with open(items_path, "r", encoding="utf-8") as f:
        items_lines = [line.strip() for line in f if line.strip()]

    with open(gold_path, "r", encoding="utf-8") as f:
        gold_lines = [line.strip() for line in f if line.strip()]

    if len(items_lines) == 0:
        print("[FAIL] Items file is empty.")
        sys.exit(1)

    if len(items_lines) != len(gold_lines):
        print(f"[FAIL] Item count mismatch: items has {len(items_lines)}, gold has {len(gold_lines)}.")
        sys.exit(1)

    # 3. Parse and validate each row
    item_ids = []
    gold_ids = []

    for idx, (i_line, g_line) in enumerate(zip(items_lines, gold_lines), start=1):
        try:
            item_data = json.loads(i_line)
        except Exception as e:
            print(f"[FAIL] Item row {idx} is invalid JSON: {e}")
            sys.exit(1)

        try:
            gold_data = json.loads(g_line)
        except Exception as e:
            print(f"[FAIL] Gold row {idx} is invalid JSON: {e}")
            sys.exit(1)

        # Gold schema check
        if set(gold_data.keys()) != {"id", "answer"}:
            print(f"[FAIL] Gold row {idx} schema invalid. Expected exactly ['id', 'answer'], got {list(gold_data.keys())}")
            sys.exit(1)

        if not verify_hex_sha256(gold_data["answer"]):
            print(f"[FAIL] Gold row {idx} answer is not a valid 64-char SHA256 hex string: {gold_data['answer']}")
            sys.exit(1)

        # Solver item schema & leak check
        if "answer" in item_data or "gold" in item_data:
            print(f"[FAIL] Data leak detected in solver item row {idx}: contains 'answer' or 'gold' key.")
            sys.exit(1)

        for required_key in ["id", "prompt", "network_spec"]:
            if required_key not in item_data:
                print(f"[FAIL] Item row {idx} missing required key '{required_key}'.")
                sys.exit(1)

        # Spec structure validation
        spec = item_data["network_spec"]
        required_spec_fields = [
            "num_nodes", "edges", "capacities", "opcodes",
            "initial_registers", "routing_rules", "injections", "max_cycles"
        ]
        for field in required_spec_fields:
            if field not in spec:
                print(f"[FAIL] Item row {idx} network_spec missing field '{field}'.")
                sys.exit(1)

        item_ids.append(item_data["id"])
        gold_ids.append(gold_data["id"])

        # Check internal consistency on sample items (re-run simulation)
        if idx in (1, len(items_lines) // 2, len(items_lines)):
            sim = RADNSimulator(spec)
            recomputed = sim.run()
            if recomputed != gold_data["answer"]:
                print(f"[FAIL] Recomputed answer mismatch for item {item_data['id']}: got {recomputed}, expected {gold_data['answer']}")
                sys.exit(1)

    # 4. ID alignment check
    if item_ids != gold_ids:
        print("[FAIL] Item IDs do not match Gold IDs in exact sequence.")
        sys.exit(1)

    # 5. Solver bundle isolation directory check
    solver_bundle_dir = items_path.parent
    forbidden_files = ["generator.py", "verifier.py", "scorer.py", "gold_private_sample.jsonl", "validation_report.md", "failure_modes.md"]
    for fname in forbidden_files:
        if (solver_bundle_dir / fname).exists():
            print(f"[FAIL] Solver bundle directory contains forbidden private file: {fname}")
            sys.exit(1)

    required_bundle_files = ["solver_packet.md", "README.md", "SOLVER_MANIFEST.json"]
    for bname in required_bundle_files:
        if not (solver_bundle_dir / bname).exists():
            print(f"[FAIL] Solver bundle directory missing required file: {bname}")
            sys.exit(1)

    print(f"[PASS] All {len(item_ids)} RADN items verified successfully!")
    print(f"[PASS] Solver bundle isolation and required files verified.")
    print(f"[PASS] Ground-truth simulator re-verification passed.")
    sys.exit(0)



if __name__ == "__main__":
    main()
