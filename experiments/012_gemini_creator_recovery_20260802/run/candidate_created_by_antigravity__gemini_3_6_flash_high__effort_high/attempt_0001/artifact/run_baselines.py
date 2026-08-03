#!/usr/bin/env python3
"""
Baseline solver scripts to test weak and shortcut baselines against gold answers.
"""

import json
import hashlib
from pathlib import Path
from generator import RADNSimulator, uint32, rotl32


def run_random_baseline(items_file: Path, out_file: Path):
    preds = []
    with open(items_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                # Random hash based on item id string
                h = hashlib.sha256(f"dummy_guess_{item['id']}".encode()).hexdigest()
                preds.append({"id": item["id"], "answer": h})

    with open(out_file, "w", encoding="utf-8") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")


class NaiveFlawedSimulator(RADNSimulator):
    """
    A baseline solver that ignores backpressure capacity stalls in Phase 4 (always forces forward),
    simulating a naive software agent implementation error.
    """
    def _step_phase4_forwarding(self, cycle: int):
        for v in range(self.num_nodes):
            pkt = self.output_buffers[v]
            if pkt is None:
                continue

            neighbors = self.out_neighbors[v]
            if not neighbors:
                self.output_buffers[v] = None
                continue

            # Naively pick first neighbor ignoring capacities & complex dynamic rules
            target_neighbor = neighbors[0]
            # Force forward ignoring queue full capacity
            self.input_queues[(v, target_neighbor)].append(pkt)
            self.output_buffers[v] = None


def run_flawed_solver_baseline(items_file: Path, out_file: Path):
    preds = []
    with open(items_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                spec = item["network_spec"]
                flawed_sim = NaiveFlawedSimulator(spec)
                ans = flawed_sim.run()
                preds.append({"id": item["id"], "answer": ans})

    with open(out_file, "w", encoding="utf-8") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")


def main():
    items_file = Path("solver_bundle/items_private_sample.jsonl")
    gold_file = Path("gold_private_sample.jsonl")

    # 1. Random Baseline
    pred_random = Path("predictions_random.jsonl")
    run_random_baseline(items_file, pred_random)

    # 2. Flawed Simulator Baseline
    pred_flawed = Path("predictions_flawed.jsonl")
    run_flawed_solver_baseline(items_file, pred_flawed)

    print("Baseline prediction files generated successfully.")


if __name__ == "__main__":
    main()
