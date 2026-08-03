#!/usr/bin/env python3
import argparse
import json
import os
import random
from pathlib import Path

def generate_state_machine_item(rng, item_idx):
    item_id = f"item_{item_idx+1:03d}"
    num_registers = 4
    reg_names = [f"R{i}" for i in range(num_registers)]

    initial_regs = {r: rng.randint(-20, 50) for r in reg_names}

    num_steps = rng.randint(5, 10)
    instructions = []
    current_regs = dict(initial_regs)

    for s in range(num_steps):
        op_type = rng.choice(["SET", "ADD", "SUB", "MUL", "IF_THEN", "MOD"])
        if op_type == "SET":
            r_target = rng.choice(reg_names)
            r_src = rng.choice(reg_names)
            val = rng.randint(-10, 20)
            use_reg = rng.choice([True, False])
            if use_reg and r_src != r_target:
                instructions.append(f"Step {s+1}: SET {r_target} = {r_src} + {val}")
                current_regs[r_target] = current_regs[r_src] + val
            else:
                instructions.append(f"Step {s+1}: SET {r_target} = {val}")
                current_regs[r_target] = val
        elif op_type == "ADD":
            r1 = rng.choice(reg_names)
            r2 = rng.choice(reg_names)
            instructions.append(f"Step {s+1}: ADD {r2} to {r1}")
            current_regs[r1] = current_regs[r1] + current_regs[r2]
        elif op_type == "SUB":
            r1 = rng.choice(reg_names)
            r2 = rng.choice(reg_names)
            instructions.append(f"Step {s+1}: SUB {r2} from {r1}")
            current_regs[r1] = current_regs[r1] - current_regs[r2]
        elif op_type == "MUL":
            r1 = rng.choice(reg_names)
            val = rng.randint(-5, 5)
            instructions.append(f"Step {s+1}: MUL {r1} by {val}")
            current_regs[r1] = current_regs[r1] * val
        elif op_type == "MOD":
            r1 = rng.choice(reg_names)
            val = rng.randint(2, 10)
            instructions.append(f"Step {s+1}: MOD {r1} by {val}")
            current_regs[r1] = current_regs[r1] % val
        elif op_type == "IF_THEN":
            r_cond1 = rng.choice(reg_names)
            r_cond2 = rng.choice(reg_names)
            r_act = rng.choice(reg_names)
            val1 = rng.randint(1, 15)
            val2 = rng.randint(1, 15)

            cond_met = current_regs[r_cond1] > current_regs[r_cond2]
            instructions.append(f"Step {s+1}: IF {r_cond1} > {r_cond2} THEN ADD {val1} to {r_act} ELSE SUB {val2} from {r_act}")
            if cond_met:
                current_regs[r_act] += val1
            else:
                current_regs[r_act] -= val2

    init_str = ", ".join([f"{k}={v}" for k, v in initial_regs.items()])
    instr_str = "\n".join(instructions)

    prompt = (
        f"You are evaluating a register state machine execution.\n"
        f"Initial Registers: {init_str}\n\n"
        f"Execution Instructions:\n{instr_str}\n\n"
        f"Determine the final integer values of all registers ({', '.join(reg_names)}) after executing all steps in order.\n"
        f"Output your answer as a JSON object mapping register names to integer values, e.g., {{\"{reg_names[0]}\": 10, ...}}."
    )

    target_str = json.dumps(current_regs, sort_keys=True)

    gold_item = {
        "item_id": item_id,
        "prompt": prompt,
        "target": target_str,
        "gold_registers": current_regs,
        "metadata": {
            "num_steps": num_steps,
            "initial_registers": initial_regs
        }
    }

    solver_item = {
        "item_id": item_id,
        "prompt": prompt,
        "metadata": {
            "num_steps": num_steps,
            "initial_registers": initial_regs
        }
    }

    return gold_item, solver_item

def main():
    parser = argparse.ArgumentParser(description="Generator for state_machine_trace benchmark.")
    parser.add_argument("--sample-count", type=int, default=30, help="Number of items to generate")
    parser.add_argument("--seed", type=int, default=20260516, help="Random seed for deterministic generation")
    parser.add_argument("--out-dir", type=str, default=".", help="Output directory")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    out_path = Path(args.out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    solver_bundle_dir = out_path / "solver_bundle"
    solver_bundle_dir.mkdir(parents=True, exist_ok=True)

    gold_items = []
    solver_items = []

    for i in range(args.sample_count):
        g_item, s_item = generate_state_machine_item(rng, i)
        gold_items.append(g_item)
        solver_items.append(s_item)

    gold_file = out_path / "gold_private_sample.jsonl"
    with open(gold_file, "w", encoding="utf-8") as f:
        for item in gold_items:
            f.write(json.dumps(item) + "\n")

    solver_items_file = solver_bundle_dir / "items_private_sample.jsonl"
    with open(solver_items_file, "w", encoding="utf-8") as f:
        for item in solver_items:
            f.write(json.dumps(item) + "\n")

    solver_manifest = {
        "manifest_version": "1.0.0",
        "benchmark_name": "state_machine_trace",
        "items_file": "items_private_sample.jsonl",
        "sample_count": args.sample_count,
        "description": "Solver bundle containing evaluation prompts for state_machine_trace benchmark."
    }
    manifest_file = solver_bundle_dir / "SOLVER_MANIFEST.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(solver_manifest, f, indent=2)

    solver_readme = solver_bundle_dir / "README.md"
    solver_readme_content = (
        "# Solver Bundle for state_machine_trace\n\n"
        "This bundle contains the public solver packet for the `state_machine_trace` benchmark.\n\n"
        "## Files\n"
        "- `items_private_sample.jsonl`: Contains the problem prompts and metadata without ground-truth solutions.\n"
        "- `SOLVER_MANIFEST.json`: Manifest metadata describing the solver bundle contents.\n\n"
        "## Output Contract\n"
        "Solvers must output predictions in JSONL format, where each line contains:\n"
        "```json\n"
        "{\"item_id\": \"item_001\", \"prediction\": \"{\\\"R0\\\": 10, \\\"R1\\\": -5, \\\"R2\\\": 0, \\\"R3\\\": 12}\"}\n"
        "```\n"
        "or with integer register dict as `prediction`.\n"
    )
    with open(solver_readme, "w", encoding="utf-8") as f:
        f.write(solver_readme_content)

    print(f"Successfully generated {args.sample_count} items with seed {args.seed} in {out_path}")

if __name__ == "__main__":
    main()
