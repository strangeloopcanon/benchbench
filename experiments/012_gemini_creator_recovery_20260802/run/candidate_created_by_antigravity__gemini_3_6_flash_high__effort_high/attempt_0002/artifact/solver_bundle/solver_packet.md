# RADN-Sim: Reconfigurable Asynchronous Dataflow Network Benchmark

## Overview

**RADN-Sim** is a cycle-accurate dataflow microarchitecture simulation benchmark. Each item describes a network of computing nodes connected by directed communication channels with finite queue capacities. Nodes process incoming data packets, update local 32-bit registers using custom opcodes, and forward packets dynamically based on dynamic routing policies and backpressure constraints.

Your task as a solver is to parse the `network_spec` for each problem instance, simulate the deterministic clock-cycle execution for `max_cycles`, construct the canonical system trace log, and output the SHA-256 hex checksum of that trace string.

---

## Microarchitecture Specification

All arithmetic operations are performed on **32-bit unsigned integers** (mod $2^{32}$, using bitwise `val & 0xFFFFFFFF`).

### Network Topology & State

1. **Nodes**: $N$ nodes indexed $0 \dots N-1$.
   - Each node $v$ contains 4 registers: $R_0, R_1, R_2, R_3$, initialized to `initial_registers[v]`.
   - Node input capacity: $C_v$. The total number of packets across all input queues of node $v$ cannot exceed $C_v$.
   - Node output buffer: Holds at most 1 packet pending egress forwarding.
2. **Channels & Input Queues**:
   - For each directed edge $(u, v)$, node $v$ maintains a FIFO input queue for packets arriving from $u$.
   - Injection into node $v$ uses a dedicated external injection queue $(-1, v)$.

---

## Cycle Clock Execution Order

Every cycle $t = 0, 1, \dots, \text{max\_cycles} - 1$ proceeds sequentially through 4 distinct phases:

### Phase 1: Ingress (Packet Injection)
- Packets scheduled for cycle $t$ in `injections` are processed in schedule order.
- For each scheduled packet targeting node $v$:
  - If the total packet count currently in all input queues of node $v$ is `< C_v`:
    - The packet enters the injection queue `(-1, v)`.
  - Else:
    - The packet overflows and is dropped immediately, appended to the `DROPPED LOG`: `cycle:node_id:packet_id:payload`.

### Phase 2: Retirement (Destination Check)
- For each node $v \in 0 \dots N-1$:
  - Iterate over all incoming queues of node $v$ (sorted by source node ID $u = -1, 0, 1 \dots$).
  - While the head packet of a queue has `destination == v`:
    - Pop the packet from the queue (retiring it).
    - Append to `RETIRED LOG`: `cycle:node_id:packet_id:payload:priority`.
    - Retirement immediately frees input queue capacity at node $v$.

### Phase 3: Node Computation (Opcode Processing)
- For each node $v \in 0 \dots N-1$:
  - If node $v$'s output buffer is NOT empty (contains a stalled packet from a previous backpressure cycle), node $v$ stalls and cannot execute a new packet this cycle.
  - Otherwise, node $v$ checks all its input queues for available packets.
  - If no packets are available across any input queues, node $v$ remains idle this cycle.
  - If packets are available:
    - Candidate selection: Select the head packet with the **highest priority** (`priority` value).
    - Tie-breaking: If multiple head packets have equal maximum priority, select the one from the queue with the **lowest source node ID** $u$.
    - Pop the selected packet from its queue.
    - Execute opcode `opcodes[v]` on registers $R = \text{registers}[v]$ and `payload` $P$:
      - `ADD_REG`: $R_0 = (R_0 + P) \bmod 2^{32}$; $P = (R_0 \oplus P) \bmod 2^{32}$
      - `XOR_SHIFT`: $R_1 = (R_1 \oplus (P \ll 3)) \bmod 2^{32}$; $P = (R_1 + R_0) \bmod 2^{32}$
      - `MUL_MOD`: $R_2 = (R_2 \times 31 + P) \bmod 2^{32}$; $P = R_2 \oplus R_3$
      - `ROTATE_BIT`: $R_3 = ((R_3 \ll 5) \mid (R_3 \gg 27)) \bmod 2^{32}$; $P = P \oplus R_3$
      - `COND_SWAP`: If $R_0 > R_1$, swap $R_2$ and $R_3$; $P = (R_0 + R_1 + R_2 + R_3) \bmod 2^{32}$
      - `AND_OR_MIX`: $R_0 = ((R_0 \mathbin{\&} P) \mid R_1) \bmod 2^{32}$; $P = (R_0 \oplus ((P \ll 7) \mid (P \gg 25))) \bmod 2^{32}$
      - `SUB_WRAP`: $R_1 = (R_1 - P) \bmod 2^{32}$; $P = (R_1 + R_2) \bmod 2^{32}$
    - Update packet payload to $P$.
    - Place packet into node $v$'s output buffer.

### Phase 4: Egress & Forwarding (Routing & Backpressure)
- For each node $v \in 0 \dots N-1$:
  - If node $v$'s output buffer contains a packet:
    - If node $v$ has no outgoing edges in `edges`, the packet is unroutable: append to `DROPPED LOG` (`cycle:node_id:packet_id:payload`) and clear output buffer.
    - Otherwise, select target outgoing neighbor $w$ based on `routing_rules[v]`:
      - `STATIC`: Map destination to neighbor using `dest_map[str(destination)]`. Fallback: `neighbors[destination % len(neighbors)]`.
      - `DYNAMIC_THRESHOLD`: If $R[\text{register}] \ge \text{threshold}$, select `primary` neighbor; else `secondary`.
      - `ADAPTIVE_LOAD`: Select neighbor $w$ with the lowest current total packet count across its input queues. Tie-break: lowest neighbor node ID.
      - `PRIORITY_PREFERENTIAL`: If packet `priority` $\ge \text{high\_priority\_threshold}$, select `high_port`; else `low_port`.
    - Capacity & Backpressure Check:
      - Count total packets currently in all input queues of target neighbor $w$.
      - If total packets `< C_w`:
        - Transfer packet into queue $(v, w)$ at neighbor $w$.
        - Clear output buffer of node $v$.
      - Else (Target queue full):
        - Packet remains in output buffer of node $v$ (Backpressure stall).

---

## Canonical Trace Log & Hash Output

After running for `max_cycles`, construct the canonical trace text string:

```text
=== RETIRED LOG ===
<cycle>:<node_id>:<packet_id>:<payload>:<priority>
...
=== DROPPED LOG ===
<cycle>:<node_id>:<packet_id>:<payload>
...
=== FINAL REGISTERS ===
Node_0:<R0>,<R1>,<R2>,<R3>
Node_1:<R0>,<R1>,<R2>,<R3>
...
Node_N-1:<R0>,<R1>,<R2>,<R3>
```

- Each log entry is on its own line (separated by newline `\n`).
- Retired and dropped logs appear in exact chronological order as logged.
- Nodes in `FINAL REGISTERS` are ordered $0 \dots N-1$.
- `answer` string = Lowercase 64-character SHA-256 hex digest of this canonical trace string (`hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()`).

---

## Problem Input Format (`items_private_sample.jsonl`)

Each line contains a JSON object:
```json
{
  "id": "radn_item_001",
  "prompt": "Simulate the RADN instance...",
  "network_spec": {
    "num_nodes": 6,
    "edges": [[0, 1], [1, 2], [2, 3], ...],
    "capacities": [4, 4, 4, 4, 4, 4],
    "opcodes": ["ADD_REG", "XOR_SHIFT", ...],
    "initial_registers": [[10, 20, 30, 40], ...],
    "routing_rules": [...],
    "injections": [
      {
        "cycle": 0,
        "node_id": 0,
        "packet_id": "P01",
        "payload": 12345,
        "priority": 5,
        "destination": 3
      }
    ],
    "max_cycles": 50
  }
}
```

---

## Output Predictions Format (`predictions.jsonl`)

Each line must contain a JSON object:
```json
{"id": "radn_item_001", "answer": "fa4c36eb767ea683b9447a39982082c38a5e870d36b66bdc451027ef52ce7bd7"}
```
