# RADN-Sim Failure Modes Taxonomy

This document outlines the primary failure modes, algorithmic traps, and specification edge cases that cause AI models, LLM agents, and naive software baseline solvers to fail on the **RADN-Sim** benchmark.

---

## 1. Clock Phase Ordering & Double-Buffering Violations

### Description
Every cycle $t$ in RADN consists of 4 strict sequential phases:
`Phase 1 (Ingress) -> Phase 2 (Retirement) -> Phase 3 (Computation) -> Phase 4 (Egress Forwarding)`.

### Failure Mode
- **Phase Inversion**: Models often execute Egress Forwarding before Node Computation or Retirement after Ingress.
- **In-Place Mutation Race Condition**: When a packet is forwarded from node $u$ to node $v$ in Phase 4 of cycle $t$, a flawed simulator might immediately process that packet in Phase 3 of cycle $t$ at node $v$.
- **Correct Behavior**: Packets transferred in Phase 4 of cycle $t$ are placed in incoming queues and cannot be retired or computed until cycle $t+1$.

---

## 2. Backpressure Stall & Output Buffer Blindness

### Description
Each node $v$ has a finite input buffer capacity $C_v$ and an output buffer capable of holding at most 1 packet pending egress forwarding.

### Failure Mode
- **Capacity Overflow Bypass**: Flawed solvers naively push packets into neighbor queues regardless of whether the target queue total packet count has reached $C_v$.
- **Stall Blindness**: When a target neighbor's queue is full, the packet must remain in node $v$'s output buffer. In the subsequent cycle $t+1$, node $v$ **cannot execute computation on a new packet** because its output buffer is blocked. Flawed solvers overwrite the output buffer or compute multiple packets simultaneously.

---

## 3. Priority Queue Selection & Multi-Level Tie-Breaking Errors

### Description
In Phase 3 (Computation), if a node has multiple candidate head packets across its input queues, it must select the packet with the highest `priority`. If priorities are equal, it must break ties by picking the packet from the input queue with the **lowest source node ID** $u$.

### Failure Mode
- **Unsorted Queue Pick**: Selecting packets based on FIFO arrival order or arbitrary dictionary key iteration order.
- **Wrong Tie-Breaker**: Tie-breaking using packet ID string order or payload magnitude instead of lowest source node ID.

---

## 4. 32-Bit Unsigned Integer Arithmetic & Overflow Violations

### Description
All node registers ($R_0 \dots R_3$) and packet payloads are 32-bit unsigned integers wrapping modulo $2^{32}$.

### Failure Mode
- **Unbounded Integer Accumulation**: Python integers grow arbitrarily large without modulo truncation (`val & 0xFFFFFFFF`), leading to incorrect register values during `ADD_REG` or `MUL_MOD`.
- **Signed Shift/Wrap Errors**: Improper bitwise rotations or shifts that introduce signed negative numbers or fail to mask out upper bits.

---

## 5. Dynamic State-Triggered Routing Policy Evaluation Timing

### Description
Routing policies like `DYNAMIC_THRESHOLD` depend on current register values (e.g. $R[\text{register}] \ge \text{threshold}$).

### Failure Mode
- **Pre-Compute Evaluation**: Evaluating the routing condition before Phase 3 computation modifies the registers, rather than during Phase 4 egress forwarding.
- **Out-of-Date Register Lookup**: Reading initial register values instead of current cycle register values.

---

## 6. Canonical Trace Formatting & Hash Calculation Errors

### Description
The ground truth answer is the SHA-256 hex string of the exact canonical trace log text.

### Failure Mode
- **Delimiter / Format Deviation**: Using space instead of colon (`:`), lowercase instead of uppercase header labels (`=== RETIRED LOG ===`), or omitting section headers.
- **Log Omitting**: Failing to log dropped packets or final register states.
