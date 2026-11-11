# HolonomyWeave (`holonomy_weave`)

**HolonomyWeave** is a deterministic, parametrically generated benchmark for evaluating exact discrete mathematical reasoning and state-space optimization over **dihedral gauge fiber bundles** $D_M = \mathbb{Z}_2 \ltimes \mathbb{Z}_M$ on directed cyclic weaves.

## Overview

Each instance specifies a finite directed graph $G = (V, E)$ on $N$ vertices $\{0, \dots, N-1\}$ with modulus $M$, designated `source` and `sink` vertices, and positive integer edge costs $w_e \ge 1$. Every directed edge $e = (u \to v)$ carries a dihedral connection element $(s_e, r_e) \in \{-1, +1\} \times \{0, \dots, M-1\}$.

A walk starts at `source` in the identity fiber state $(+1, 0)$ and updates its fiber state along each traversed edge via the right-action of $D_M$:

$$(s, r) \star (s_e, r_e) = \bigl(s \cdot s_e,\; (r + s \cdot r_e) \bmod M\bigr).$$

Directed cycles (plaquettes) may be traversed any number of times to shift or conjugate the fiber state. Given three target holonomy states $q_0, q_1, q_2 \in D_M$ at `sink`, the solver must determine the exact minimum walk costs $d^*(q_0), d^*(q_1), d^*(q_2) \in (0, 10000)$ and report the packed canonical integer:

$$\text{answer} = d^*(q_0) \cdot 10^8 + d^*(q_1) \cdot 10^4 + d^*(q_2).$$

All instances apply vertex-label permutations, Johnson scalar potential twists $\phi(u) - \phi(v)$ preserving strict edge positivity, and vertex gauge transformations $\gamma(u) \tilde{g}_e \gamma(v)^{-1} \in D_M$ so that local greedy heuristics and edge-level inspection fail without global holonomy reasoning.

## Package Layout

```text
.
├── README.md
├── benchmark_spec.json
├── generator.py
├── verifier.py
├── scorer.py
├── gold_private_sample.jsonl
├── failure_modes.md
├── validation_report.md
└── solver_bundle/
    ├── README.md
    ├── SOLVER_MANIFEST.json
    ├── items_private_sample.jsonl
    └── solver_packet.md
```

## CLI Usage

### 1. Deterministic Sample Generation

```bash
python3 generator.py --sample-count 30 --seed 20260516 --out-dir .
```

Generates `gold_private_sample.jsonl` at the package root and populates the isolated `solver_bundle/` directory (`items_private_sample.jsonl`, `SOLVER_MANIFEST.json`, `README.md`, `solver_packet.md`). Gold answers are computed dynamically via Dijkstra search over the lifted fiber bundle $V \times D_M$.

### 2. Independent Package & Instance Verification

```bash
python3 verifier.py --root .
```

Independently solves all items from `solver_bundle/items_private_sample.jsonl` alone via Bellman-Ford relaxation on $V \times D_M$, reconstructs and forward-simulates explicit primal witness walks for every queried holonomy sector, verifies Bellman optimality inequalities, checks exact agreement with `gold_private_sample.jsonl`, and audits `solver_bundle/` for zero gold leakage.

### 3. Exact-Match Prediction Scoring

```bash
python3 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

Outputs a `schema_version: 2` JSON report containing integer `total`, integer `correct`, numeric `accuracy` (`correct / total`), error diagnostics, and per-tier breakdowns (`tier1_tractable`, `tier2_intermediate`, `tier3_holonomy`).
