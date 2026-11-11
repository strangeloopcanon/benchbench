# Experiment 016 — Gemini 4 Carbon

Gemini 4 Carbon (`agy:gemini-4-carbon-high`) was evaluated in November 2026 both as a **benchmark creator** in Experiment `016` (`experiments/016_gemini_4_carbon_creator_20261111`) and as a **blind solver** across all six active prior benchmarks (`015` Reimbursement Forensics v2, `014` Maritime General Average Forensics, `013` CloudSLA-Forensics, and the three mechanically valid Experiment `010` benchmarks: `AuditWeave`, `Counterfactual Firewall Policy Synthesis`, and `Consolidation Point`), plus its own newly created benchmark **`HolonomyWeave` (`holonomy_weave`)**.

## Outcome

**`Experiment 016` (`016-holonomy-weave`): `rejected` (`canonical_eligible: false`).**

`Gemini 4 Carbon (High)` authored a clean, zero-leak, deterministic 30-item discrete gauge-theory benchmark (**`HolonomyWeave`**) that passed every controller mechanical gate without manual post-hoc edits (`valid=true`, `deterministic=true`, `frozen_package_match=true`, `leak_match_count=0`, `gold_summary=30/30`, `wrong_summary=0/30`). However, when evaluated with Python tool execution enabled, all five modern frontier models (`GPT-6-Sol`, `Gemini 4 Argon`, `Gemini 4 Carbon`, `Claude Opus 5.5`, and `GLM 5.2`) wrote ~30-line lifted-bundle Dijkstra solvers on $V \times D_M$ and scored **`30/30` (`100.0%`)**. Consistent with Experiments `010`, `013`, `014`, and `015`, `HolonomyWeave` is mechanically valid but saturates at the frontier when code execution is available, so `canonical.status` remains `no_validated_incumbent`.

As a **solver**, `Gemini 4 Carbon (High)` achieved **`210 / 210` (`100.0%`)** across all seven active benchmarks in **`969,521` total reported tokens** (`4,617` tokens/item)—ranking **#2 overall** behind `GPT-6-Sol` (`304,495` tokens) while using **45.9% fewer tokens** than `Gemini 4 Argon` (`1,792,648` tokens) and **44.0% fewer reported tokens** than `Claude Opus 5.5` (`1,732,765` tokens).

## Creator Run & `HolonomyWeave` Solver Panel (`016_gemini_4_carbon_creator_20261111`)

### Benchmark Design (`holonomy_weave`)
Each of the 30 generated items (`hw_001`–`hw_030`, stratified into `tier1_tractable`, `tier2_intermediate`, and `tier3_holonomy`) specifies a finite directed cyclic weave $G = (V, E)$ with positive integer edge weights $w_e \ge 1$ and connection elements $(s_e, r_e) \in \{-1, +1\} \times \{0, \dots, M-1\}$ in the non-abelian dihedral group $D_M = \mathbb{Z}_2 \ltimes \mathbb{Z}_M$. Walks start at `source` in $(+1, 0)$ and compose edge connections on the right:

$$(s, r) \star (s_e, r_e) = \bigl(s \cdot s_e,\; (r + s \cdot r_e) \bmod M\bigr).$$

Instances apply random vertex-label permutations, Johnson scalar potential twists $\phi(u) - \phi(v)$, and non-abelian vertex gauge transformations $\gamma(u) \tilde{g}_e \gamma(v)^{-1} \in D_M$, packing three queried holonomy-sector shortest-walk costs at `sink` into an 11–12 digit integer $d^*(q_0) \cdot 10^8 + d^*(q_1) \cdot 10^4 + d^*(q_2)$. `verifier.py` independently solves every item from `solver_bundle/items_private_sample.jsonl` alone via Bellman-Ford relaxation, forward-simulates explicit primal witness walks, verifies Bellman optimality inequalities, and runs a zero-leak audit.

### Creation & Mechanical Validation
- **Attempt 1 (`attempt_0001`)**: Timed out at the creator print window (`returncode=3`, `253,465` tokens) after writing 2 files while running inside the pre-PTY Seatbelt profile (`read_file` / `write_file` only).
- **Attempt 2 (`attempt_0002`, automatic controller repair)**: Completed all 12 package files cleanly (`returncode=0`, `441,161` tokens; total creator + repair = `694,626` tokens) and passed `local_validate()` on the first repair check with zero manual intervention:
  - `valid: true`, `deterministic: true`, `frozen_package_match: true`
  - `gold_summary: {"total": 30, "correct": 30, "accuracy": 1.0}`
  - `wrong_summary: {"total": 30, "correct": 0, "accuracy": 0.0}`
  - `leak_match_count: 0`, `bundle_file_count: 4`

### Five-Model Frontier Solver Sweep on `HolonomyWeave` (Python Enabled)

| Solver | Provider | Score | Accuracy | Reported Tokens | Non-Cache (`in+out`) Tokens | Evidence Root |
|---|---|---:|---:|---:|---:|---|
| **GPT-6-Sol (High)** | Codex (`codex:gpt-6-sol@high`) | **30/30** | **100.0%** | 23,739 | 23,739 | `experiments/016_gemini_4_carbon_creator_20261111` |
| **Gemini 4 Argon (High)** | Antigravity (`agy:gemini-4-argon-high`) | **30/30** | **100.0%** | 56,449 | 56,449 | `experiments/extensions/016_gemini_4_argon_solver_20261111` |
| **Gemini 4 Carbon (High)** | Antigravity (`agy:gemini-4-carbon-high`) | **30/30** | **100.0%** | 62,150 | 62,150 | `experiments/extensions/016_gemini_4_carbon_solver_20261111` |
| **Claude Opus 5.5 (High)** | Cursor (`cursor:claude-opus-5-5-high`) | **30/30** | **100.0%** | 151,656 | 2,689 | `experiments/016_gemini_4_carbon_creator_20261111` |
| **GLM 5.2 (High)** | Cursor (`cursor:glm-5.2-high`) | **30/30** | **100.0%** | 194,357 | 27,029 | `experiments/016_gemini_4_carbon_creator_20261111` |

*(Before `allow_pseudo_tty` was enabled for `agy 1.5.5` inside outer Seatbelt in `benchbench_sandbox.py`, the initial `agy` solver invocations in `016_gemini_4_carbon_creator_20261111` lacked shell/Python execution and exited non-zero (`Carbon` `rc=3`, `Argon` `rc=78`); remarkably, `Gemini 4 Argon` still hand-computed all 30 dihedral holonomy answers accurately (`30/30` against `scorer.py` in `281,565` tokens) before hitting the output-cutoff exit code. With PTY/Python restored, both `Carbon` and `Argon` completed cleanly (`rc=0`) in `62,150` and `56,449` tokens via `--retry-failed-source-cells` overlays.)*

## `Gemini 4 Carbon (High)` Solver Extensions Across Existing Benchmarks

| Benchmark | Source Experiment | Score | Accuracy | Reported Tokens | Execution Notes & Overlay |
|---|---|---:|---:|---:|---|
| **Reimbursement Forensics v2** | `015` | **30/30** | **100.0%** | 165,647 | Solved `30/30` (`rc=0`) even without Python (`experiments/extensions/015_gemini_4_carbon_solver_20261110`) |
| **AuditWeave** | `010` | **30/30** | **100.0%** | 84,932 | Python-enabled (`rc=0`, `experiments/extensions/010_gemini_4_carbon_python_recovery_20261111`) |
| **Counterfactual Firewall Policy Synthesis** | `010` | **30/30** | **100.0%** | 245,897 | Python-enabled (`rc=0`, `experiments/extensions/010_gemini_4_carbon_python_recovery_20261111`) |
| **Consolidation Point** | `010` | **30/30** | **100.0%** | 87,702 | Solved `30/30` (`rc=0`) even without Python (`experiments/extensions/010_gemini_4_carbon_solver_20261111`) |
| **CloudSLA-Forensics** | `013` | **30/30** | **100.0%** | 184,078 | Python-enabled (`rc=0`, `experiments/extensions/013_gemini_4_carbon_solver_20261111`; also scored `30/30` without Python) |
| **Maritime General Average Forensics** | `014` | **30/30** | **100.0%** | 139,115 | Solved `30/30` (`rc=0`) even without Python (`experiments/extensions/014_gemini_4_carbon_solver_20261111`) |
| **HolonomyWeave** | `016` | **30/30** | **100.0%** | 62,150 | Python-enabled (`rc=0`, `experiments/extensions/016_gemini_4_carbon_solver_20261111`) |
| **Total (7 Active Benchmarks)** | — | **210/210** | **100.0%** | **969,521** | **`4,617` tokens/item; `90/90` (`100%`) on No-Python Stress Test (`013`+`014`+`015`)** |
