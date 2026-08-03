#!/usr/bin/env python3
"""
Generator for RADN (Reconfigurable Asynchronous Dataflow Network) Benchmark.
Generates solver items and gold ground truth answers.
"""

import argparse
import hashlib
import json
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple


# --- RADN Microarchitecture Reference Simulator ---

MASK32 = 0xFFFFFFFF

def uint32(val: int) -> int:
    return val & MASK32

def rotl32(val: int, count: int) -> int:
    val = uint32(val)
    count = count % 32
    return uint32((val << count) | (val >> (32 - count)))

class RADNSimulator:
    def __init__(self, spec: Dict[str, Any]):
        self.num_nodes = spec["num_nodes"]
        self.edges = spec["edges"]  # List of [u, v]
        self.capacities = spec["capacities"]  # List of capacity per node or dict
        self.opcodes = spec["opcodes"]  # List of opcode names for each node
        self.routing_rules = spec["routing_rules"]  # Routing spec per node
        self.initial_registers = [list(r) for r in spec["initial_registers"]]  # List of 4 ints per node
        self.injections = spec["injections"]  # List of dicts: cycle, node_id, packet_id, payload, priority, destination
        self.max_cycles = spec["max_cycles"]

        # Adjacency structures
        self.out_neighbors = {i: [] for i in range(self.num_nodes)}
        self.in_neighbors = {i: [] for i in range(self.num_nodes)}
        for u, v in self.edges:
            self.out_neighbors[u].append(v)
            self.in_neighbors[v].append(u)

        # State initialization
        self.registers = [list(r) for r in self.initial_registers]

        # Dedicated FIFO queue per incoming edge (u -> v): key (u, v) -> List of packets
        self.input_queues: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
        for u, v in self.edges:
            self.input_queues[(u, v)] = []

        # Dedicated queue for initial injection into node v: ( -1, v ) -> List of packets
        for v in range(self.num_nodes):
            self.input_queues[(-1, v)] = []

        # Output buffer per node: node_id -> Optional packet dict
        self.output_buffers: Dict[int, Any] = {i: None for i in range(self.num_nodes)}

        # Logs
        self.retired_log: List[Dict[str, Any]] = []
        self.dropped_log: List[Dict[str, Any]] = []

    def get_node_capacity(self, node_id: int) -> int:
        if isinstance(self.capacities, list):
            return self.capacities[node_id]
        return self.capacities.get(str(node_id), self.capacities.get(node_id, 4))

    def run(self) -> str:
        for cycle in range(self.max_cycles):
            self._step_phase1_ingress(cycle)
            self._step_phase2_retirement(cycle)
            self._step_phase3_computation(cycle)
            self._step_phase4_forwarding(cycle)

        return self._compute_checksum()

    def _step_phase1_ingress(self, cycle: int):
        # Inject packets scheduled for this cycle
        current_injections = [p for p in self.injections if p["cycle"] == cycle]
        for p in current_injections:
            v = p["node_id"]
            cap = self.get_node_capacity(v)
            # Count total packets currently in all input queues of node v
            total_in_v = sum(len(self.input_queues[key]) for key in self.input_queues if key[1] == v)
            if total_in_v < cap:
                packet_obj = {
                    "packet_id": p["packet_id"],
                    "payload": uint32(p["payload"]),
                    "priority": p["priority"],
                    "origin": p["node_id"],
                    "destination": p["destination"]
                }
                self.input_queues[(-1, v)].append(packet_obj)
            else:
                self.dropped_log.append({
                    "cycle": cycle,
                    "node_id": v,
                    "packet_id": p["packet_id"],
                    "payload": uint32(p["payload"])
                })

    def _step_phase2_retirement(self, cycle: int):
        # Check all input queues at each node v; if head packet destination == v, retire it immediately
        for v in range(self.num_nodes):
            incoming_keys = [k for k in self.input_queues if k[1] == v]
            # Order incoming keys deterministically (e.g. key[0] ascending)
            incoming_keys.sort(key=lambda k: k[0])
            for k in incoming_keys:
                q = self.input_queues[k]
                while q and q[0]["destination"] == v:
                    retired_packet = q.pop(0)
                    self.retired_log.append({
                        "cycle": cycle,
                        "node_id": v,
                        "packet_id": retired_packet["packet_id"],
                        "payload": uint32(retired_packet["payload"]),
                        "priority": retired_packet["priority"]
                    })

    def _step_phase3_computation(self, cycle: int):
        # Process node computation in order 0 ... num_nodes - 1
        for v in range(self.num_nodes):
            # If node v already has a packet stalled in its output buffer, it cannot compute a new one
            if self.output_buffers[v] is not None:
                continue

            # Gather head packets across all input queues of node v
            candidates = []
            incoming_keys = [k for k in self.input_queues if k[1] == v and len(self.input_queues[k]) > 0]

            if not incoming_keys:
                continue

            for k in incoming_keys:
                head_pkt = self.input_queues[k][0]
                candidates.append((head_pkt["priority"], k[0], k, head_pkt))

            # Highest priority first. Tie-break: lowest source node ID (k[0])
            candidates.sort(key=lambda item: (-item[0], item[1]))
            selected_item = candidates[0]
            selected_key = selected_item[2]

            # Pop the selected packet
            packet = self.input_queues[selected_key].pop(0)

            # Execute opcode
            r = self.registers[v]
            op = self.opcodes[v]
            p_val = packet["payload"]

            if op == "ADD_REG":
                r[0] = uint32(r[0] + p_val)
                p_val = uint32(r[0] ^ p_val)
            elif op == "XOR_SHIFT":
                r[1] = uint32(r[1] ^ (p_val << 3))
                p_val = uint32(r[1] + r[0])
            elif op == "MUL_MOD":
                r[2] = uint32(r[2] * 31 + p_val)
                p_val = uint32(r[2] ^ r[3])
            elif op == "ROTATE_BIT":
                r[3] = rotl32(r[3], 5)
                p_val = uint32(p_val ^ r[3])
            elif op == "COND_SWAP":
                if r[0] > r[1]:
                    r[2], r[3] = r[3], r[2]
                p_val = uint32(r[0] + r[1] + r[2] + r[3])
            elif op == "AND_OR_MIX":
                r[0] = uint32((r[0] & p_val) | r[1])
                p_val = uint32(r[0] ^ rotl32(p_val, 7))
            elif op == "SUB_WRAP":
                r[1] = uint32(r[1] - p_val)
                p_val = uint32(r[1] + r[2])
            else:
                # Default fallback
                r[0] = uint32(r[0] + 1)
                p_val = uint32(p_val + r[0])

            packet["payload"] = p_val
            self.output_buffers[v] = packet

    def _step_phase4_forwarding(self, cycle: int):
        # Forward packets from output buffers in order 0 ... num_nodes - 1
        for v in range(self.num_nodes):
            pkt = self.output_buffers[v]
            if pkt is None:
                continue

            neighbors = self.out_neighbors[v]
            if not neighbors:
                # Terminal node with no outgoing edges: packet is dropped as unroutable
                self.dropped_log.append({
                    "cycle": cycle,
                    "node_id": v,
                    "packet_id": pkt["packet_id"],
                    "payload": uint32(pkt["payload"])
                })
                self.output_buffers[v] = None
                continue

            # Determine target neighbor
            rule = self.routing_rules[v]
            rule_type = rule.get("type", "STATIC")

            target_neighbor = neighbors[0]

            if rule_type == "STATIC":
                dest_map = rule.get("dest_map", {})
                str_dest = str(pkt["destination"])
                if str_dest in dest_map:
                    target_neighbor = dest_map[str_dest]
                elif pkt["destination"] in dest_map:
                    target_neighbor = dest_map[pkt["destination"]]
                else:
                    # Fallback: shortest index or modular
                    target_neighbor = neighbors[pkt["destination"] % len(neighbors)]

            elif rule_type == "DYNAMIC_THRESHOLD":
                thresh = rule.get("threshold", 1000)
                reg_idx = rule.get("register", 0)
                if self.registers[v][reg_idx] >= thresh:
                    target_neighbor = rule.get("primary", neighbors[0])
                else:
                    target_neighbor = rule.get("secondary", neighbors[-1])

            elif rule_type == "ADAPTIVE_LOAD":
                # Pick neighbor with lowest total occupation in its input queues
                best_n = neighbors[0]
                best_occ = float("inf")
                for n in neighbors:
                    occ = sum(len(self.input_queues[k]) for k in self.input_queues if k[1] == n)
                    if occ < best_occ:
                        best_occ = occ
                        best_n = n
                    elif occ == best_occ and n < best_n:
                        best_n = n
                target_neighbor = best_n

            elif rule_type == "PRIORITY_PREFERENTIAL":
                if pkt["priority"] >= rule.get("high_priority_threshold", 5):
                    target_neighbor = rule.get("high_port", neighbors[0])
                else:
                    target_neighbor = rule.get("low_port", neighbors[-1])

            # Check capacity at target neighbor input queue (v, target_neighbor)
            target_cap = self.get_node_capacity(target_neighbor)
            total_in_target = sum(len(self.input_queues[k]) for k in self.input_queues if k[1] == target_neighbor)

            if total_in_target < target_cap:
                # Forward packet
                self.input_queues[(v, target_neighbor)].append(pkt)
                self.output_buffers[v] = None
            else:
                # Backpressure: packet stays in output buffer of node v
                pass

    def _compute_checksum(self) -> str:
        # Construct canonical trace string
        lines = []
        lines.append("=== RETIRED LOG ===")
        for r in self.retired_log:
            lines.append(f"{r['cycle']}:{r['node_id']}:{r['packet_id']}:{r['payload']}:{r['priority']}")

        lines.append("=== DROPPED LOG ===")
        for d in self.dropped_log:
            lines.append(f"{d['cycle']}:{d['node_id']}:{d['packet_id']}:{d['payload']}")

        lines.append("=== FINAL REGISTERS ===")
        for v in range(self.num_nodes):
            regs_str = ",".join(str(r) for r in self.registers[v])
            lines.append(f"Node_{v}:{regs_str}")

        canonical_str = "\n".join(lines)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


# --- Item Generator ---

OPCODES_LIST = ["ADD_REG", "XOR_SHIFT", "MUL_MOD", "ROTATE_BIT", "COND_SWAP", "AND_OR_MIX", "SUB_WRAP"]

def generate_random_network(item_id: int, rng: random.Random) -> Tuple[Dict[str, Any], str]:
    num_nodes = rng.randint(5, 12)

    # Topology generation: create a connected directed graph
    edges = []
    # Base ring to ensure reachability
    for i in range(num_nodes):
        edges.append([i, (i + 1) % num_nodes])
    # Add cross links
    num_extra = rng.randint(num_nodes // 2, num_nodes * 2)
    for _ in range(num_extra):
        u = rng.randint(0, num_nodes - 1)
        v = rng.randint(0, num_nodes - 1)
        if u != v and [u, v] not in edges:
            edges.append([u, v])

    capacities = [rng.randint(2, 6) for _ in range(num_nodes)]
    opcodes = [rng.choice(OPCODES_LIST) for _ in range(num_nodes)]
    initial_registers = [[rng.randint(0, 0xFFFFFF) for _ in range(4)] for _ in range(num_nodes)]

    # Routing rules
    routing_rules = []
    for u in range(num_nodes):
        neighbors = [v for [x, v] in edges if x == u]
        rtype = rng.choice(["STATIC", "DYNAMIC_THRESHOLD", "ADAPTIVE_LOAD", "PRIORITY_PREFERENTIAL"])
        if rtype == "STATIC":
            dest_map = {}
            for d in range(num_nodes):
                dest_map[str(d)] = rng.choice(neighbors)
            rule = {"type": "STATIC", "dest_map": dest_map}
        elif rtype == "DYNAMIC_THRESHOLD":
            rule = {
                "type": "DYNAMIC_THRESHOLD",
                "threshold": rng.randint(0x1000, 0x800000),
                "register": rng.randint(0, 3),
                "primary": neighbors[0],
                "secondary": neighbors[-1]
            }
        elif rtype == "ADAPTIVE_LOAD":
            rule = {"type": "ADAPTIVE_LOAD"}
        else:
            rule = {
                "type": "PRIORITY_PREFERENTIAL",
                "high_priority_threshold": rng.randint(3, 8),
                "high_port": neighbors[0],
                "low_port": neighbors[-1]
            }
        routing_rules.append(rule)

    # Injections
    num_packets = rng.randint(10, 30)
    max_cycles = rng.randint(30, 60)
    injections = []
    for p_idx in range(num_packets):
        inj_cycle = rng.randint(0, max_cycles // 2)
        origin = rng.randint(0, num_nodes - 1)
        dest = rng.randint(0, num_nodes - 1)
        while dest == origin:
            dest = rng.randint(0, num_nodes - 1)
        injections.append({
            "cycle": inj_cycle,
            "node_id": origin,
            "packet_id": f"P{p_idx + 1:02d}",
            "payload": rng.randint(0x10, 0xFFFFFF),
            "priority": rng.randint(1, 10),
            "destination": dest
        })

    spec = {
        "num_nodes": num_nodes,
        "edges": edges,
        "capacities": capacities,
        "opcodes": opcodes,
        "initial_registers": initial_registers,
        "routing_rules": routing_rules,
        "injections": injections,
        "max_cycles": max_cycles
    }

    # Run simulator to get reference answer
    sim = RADNSimulator(spec)
    answer = sim.run()

    item_prompt = (
        f"Simulate the Reconfigurable Asynchronous Dataflow Network (RADN) instance specified in the problem data.\n"
        f"Network contains {num_nodes} nodes and {len(edges)} directed channels. Run for {max_cycles} cycles.\n"
        f"Compute the exact canonical trace SHA-256 hex checksum according to the RADN microarchitecture specification."
    )

    item_dict = {
        "id": f"radn_item_{item_id:03d}",
        "prompt": item_prompt,
        "network_spec": spec
    }

    return item_dict, answer


def main():
    parser = argparse.ArgumentParser(description="RADN Benchmark Generator")
    parser.add_argument("--sample-count", type=int, default=30, help="Number of items to generate")
    parser.add_argument("--seed", type=int, default=20260516, help="Random seed")
    parser.add_argument("--out-dir", type=str, default=".", help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    solver_bundle_dir = out_dir / "solver_bundle"
    solver_bundle_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)

    gold_rows = []
    solver_items = []

    for i in range(1, args.sample_count + 1):
        item_dict, answer = generate_random_network(i, rng)
        gold_rows.append({"id": item_dict["id"], "answer": answer})
        solver_items.append(item_dict)

    # Write gold_private_sample.jsonl
    gold_path = out_dir / "gold_private_sample.jsonl"
    with open(gold_path, "w", encoding="utf-8") as f:
        for row in gold_rows:
            f.write(json.dumps(row) + "\n")

    # Write solver_bundle/items_private_sample.jsonl
    items_path = solver_bundle_dir / "items_private_sample.jsonl"
    with open(items_path, "w", encoding="utf-8") as f:
        for item in solver_items:
            f.write(json.dumps(item) + "\n")

    # Write solver_bundle/SOLVER_MANIFEST.json
    manifest = {
        "benchmark_name": "RADN-Sim",
        "benchmark_version": "1.0.0",
        "description": "Reconfigurable Asynchronous Dataflow Network (RADN) Cycle-Accurate Simulation Benchmark",
        "item_count": len(solver_items),
        "items_file": "items_private_sample.jsonl",
        "packet_file": "solver_packet.md"
    }
    manifest_path = solver_bundle_dir / "SOLVER_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Copy / generate solver_bundle/solver_packet.md
    packet_src = Path(__file__).resolve().parent / "solver_bundle" / "solver_packet.md"
    packet_dest = (solver_bundle_dir / "solver_packet.md").resolve()
    if packet_src.exists() and packet_src != packet_dest:
        packet_dest.write_bytes(packet_src.read_bytes())

    # Copy / generate solver_bundle/README.md
    readme_src = Path(__file__).resolve().parent / "solver_bundle" / "README.md"
    readme_dest = (solver_bundle_dir / "README.md").resolve()
    if readme_src.exists() and readme_src != readme_dest:
        readme_dest.write_bytes(readme_src.read_bytes())

    print(f"Successfully generated {len(solver_items)} RADN items in {out_dir}")

if __name__ == "__main__":
    main()
