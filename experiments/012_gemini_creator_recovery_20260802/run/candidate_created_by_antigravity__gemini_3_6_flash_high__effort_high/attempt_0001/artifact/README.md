# RADN-Sim: Reconfigurable Asynchronous Dataflow Network Benchmark

**Creator**: Gemini 3.6 Flash (High) + Antigravity
**Domain**: Cycle-Accurate Microarchitecture & Dataflow State Machine Simulation
**Modality**: Code / Algorithmic Verification
**Scoring**: Deterministic Exact Match on SHA-256 Digest of Canonical Simulation Trace Log

---

## Benchmark Motivation & Novelty

### What standard evals test vs. what RADN-Sim tests
- **Existing Evals**:
  - *LiveCodeBench / HumanEval*: Test standard algorithmic problem solving (DP, graph search, arrays).
  - *SWE-bench / RE-Bench*: Test multi-file software debugging or ML engineering tasks.
  - *BIG-Bench Hard*: Tests discrete reasoning steps, but items are often solvable with short prompt reasoning or simple scripts.
- **RADN-Sim Differentiation**:
  - RADN-Sim presents cycle-accurate concurrent microarchitecture execution traces.
  - Solvers are given formal specifications of network topology, node registers, dynamic routing policies, FIFO queue capacities, and scheduled packet injections.
  - To solve an item, a model must parse the specification and execute (or write code to execute) a multi-phase clock cycle simulation handling:
    1. Synchronous phase ordering (Ingress $\rightarrow$ Retirement $\rightarrow$ Computation $\rightarrow$ Egress Forwarding).
    2. Dynamic queue capacity constraints and backpressure stalls.
    3. Priority queue packet selection with deterministic multi-level tie-breaking.
    4. Bitwise 32-bit unsigned register updates and dynamic state-triggered routing rules.
  - This benchmark is **100% solvable** by any agent or specialist human who implements the formal specification correctly (100% reference score), while LLMs writing naive or flawed scripts fail due to subtle state machine and phase ordering errors (scoring 0–6.7%).

---

## Benchmark CLI Interface

Execute commands using Python 3.12:

```bash
# 1. Generate items & solver bundle
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .

# 2. Verify package & solver bundle isolation
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl

# 3. Score predictions
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

---

## File Structure

```text
.
├── README.md                          # Benchmark documentation (this file)
├── benchmark_spec.json                # Machine-readable benchmark specification
├── generator.py                       # Procedural benchmark generator & reference simulator
├── verifier.py                        # Dataset schema & isolation verifier
├── scorer.py                          # Ground truth evaluator & score report generator
├── gold_private_sample.jsonl          # Private ground truth answers (30 items)
├── validation_report.md               # Detailed validation & solvability audit report
├── failure_modes.md                   # Taxonomy of model failure modes & traps
├── run_baselines.py                   # Script to run and evaluate baseline models
└── solver_bundle/                     # Isolated public solver package
    ├── SOLVER_MANIFEST.json           # Solver manifest metadata
    ├── items_private_sample.jsonl     # Solver task items (NO gold answers)
    ├── README.md                      # Solver bundle guide
    └── solver_packet.md               # Formal RADN microarchitecture specification
```

---

## Baseline Verification Results

| Evaluated Solver Baseline | Total Items | Correct | Accuracy | Status |
|---|---:|---:|---:|---|
| **Gold Reference Simulator** | 30 | 30 | 100.0% | Ground truth upper bound |
| **Flawed Naive Simulator** | 30 | 2 | 6.7% | Fails on backpressure & dynamic routing |
| **Random Hex Hash Baseline** | 30 | 0 | 0.0% | Zero-shot random guess lower bound |

---

## Solvability Guarantee

Every item in `solver_bundle/items_private_sample.jsonl` contains all information required to construct the exact cycle-by-cycle simulation. `solver_packet.md` defines every opcode, register transformation, priority rule, phase ordering, and trace format unambiguously. No hidden generator state, external network access, or private keys are used.
