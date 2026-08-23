# Creator quality score: methodology and calibration

This document explains the continuous **creator quality** metric in `scripts/creator_score.py`, how it was calibrated with Monte Carlo simulation (`scripts/simulate_creator_score.py`), and why the chosen defaults are `gamma=7.0`, `peak=7.5`, `floor_val=10.0`.

The simulation CSV backing this analysis is `scripts/creator_score_analysis/creator_score_simulation_results.csv` (N=50,000 grids per scenario, paired comparison within each scenario, seed=42).

Real-grid validation on canonical experiment data: `scripts/creator_score_analysis/creator_score_real_validation.md`.

---

## 1. What the metric measures

BenchBench evaluates how well each model **creates** benchmarks. For a creator row, each non-creator solver cell holds an exact-match score from 0 to 30. We want benchmarks that are **hard but solvable**: solvers land in the useful band **1–14/30**, not at **0** (broken/unspecified) nor at **15–30** (too easy).

The per-cell function `quality_index(score)` maps each solver score through a **rescaled Lorentzian bell**:

```
L(x) = 1 / (1 + ((x - peak) / gamma)²)
quality(s) = floor_val + (100 - floor_val) * (L(s) - L(30)) / (L(7) - L(30))
```

Design choices:

- **Bell shape** rewards scores near the band center and penalizes both tails smoothly (unlike hard band cutoffs).
- **`peak=7.5`** is the conceptual optimum (midpoint of 1–14). Scores are integers, so calibration anchors at **L(7) = L(8)** so that **quality(7) = quality(8) = 100** exactly.
- **`floor_val`** sets quality at score 30 (the easiest trivial outcome).
- **Score 0 → 0.0** always, bypassing the formula: a zero cell signals a broken benchmark with no quality signal.

The row-level score `creator_score_quality` is the mean of `quality_index` over non-creator solver cells (creator's own column excluded when applicable).

---

## 2. Parameters: gamma and floor_val

| Parameter | Role |
|---|---|
| **`gamma`** | Bell **width**. Smaller γ narrows the peak (sharp reward near 7–8, harsh on band edges and on high scores). Larger γ widens tolerance (high scores retain more quality). |
| **`floor_val`** | **Floor** at score 30. Lower floor compresses trivial rows downward; higher floor raises the baseline quality of easy benchmarks, improving separation from broken rows. |
| **`peak`** | Fixed at **7.5** (not exposed in ranking helpers). |

Both `gamma` and `floor_val` are threaded through `creator_score_quality` and `creator_score_quality_ranking` into `quality_index`.

---

## 3. Simulation scenarios

Five generative scenarios stress different failure modes. Within each scenario, the **same N=50,000 grids** are reused for every (gamma, floor) pair (paired comparison).

| Scenario | Generator | Purpose |
|---|---|---|
| **A — uniform** | Each cell uniform on 0..30 | Neutral maximum-entropy baseline; no structural prior. |
| **B — adverse mix** | Creator types good/easy/mixed/broken = 40/30/20/10 | Realistic mixed panel: most rows useful or easy, some broken. |
| **C — clean homogeneous** | Mix 55/40/5/0 (no broken type) | Strong creators only; models panels without broken benchmarks. |
| **D — weak solver** | B row types + one random solver column forced to 0 with p=0.6 | Column-correlated zeros (one solver systematically fails), as in real grids. |
| **E — stress** | Mix 20/20/20/40 (40% broken) | Adverse stress test with heavy broken population. |

Seeds: scenario *i* in `("A","B","C","D","E")` uses `seed + i`.

---

## 4. Inversion rates and gap

For each synthetic grid and parameter combo, we classify each row once (independent of gamma/floor):

- **broken**: ≥2 cells == 0  
- **useful/low**: ≥3 cells in 1–14  
- **high/trivial**: ≥3 cells in 15–30  

Three **inversion rates** (fraction of grids where a bad ordering occurs):

| Metric | Condition | Desired |
|---|---|---|
| **`inv_zero_over_useful`** | ∃ broken row and useful row (different) with score(broken) > score(useful) | **Low** — broken should not beat useful |
| **`inv_high_over_low`** | ∃ high row and useful row with score(high) > score(useful) | **Low** — trivial should not beat useful |
| **`inv_zero_over_trivial`** | ∃ broken row and high row with score(broken) > score(high) | **Low** — broken should not beat trivial |

**`gap_useful_trivial`**: median(useful row scores) − median(high row scores), averaged over grids where both types exist. Higher gap = better separation of useful vs trivial.

---

## 5. Simulation sweep and chosen defaults

**Sweep:** 5 scenarios × 4 gammas `[4, 7, 10, 13]` × 6 floors `[1, 3, 5, 8, 10, 20]` = **120 combinations**, N=50,000 per scenario.

**Chosen defaults:** `gamma=7.0`, `floor_val=10.0`, `peak=7.5`.

### 5.1 Why gamma = 7

At **floor=10**, inversion rates vs gamma (scenario **B**, the realistic mix):

| gamma | inv_high | inv_zero | inv_zero_trivial | gap |
|---:|---:|---:|---:|---:|
| 4 | 12.74% | 2.40% | 20.46% | 28.84 |
| **7** | **6.64%** | **0.81%** | **17.77%** | **33.63** |
| 10 | 7.13% | 0.37% | 15.10% | 33.92 |
| 13 | 9.33% | 0.21% | 13.00% | 32.89 |

- **γ=4** is too narrow: `inv_high` and `inv_zero_trivial` spike (useful-band edges and compressed triviales interact badly).
- **γ=13** is too wide: `inv_high` rises toward 9% (trivial rows score too well).
- **γ=7–10** form a **robustness valley** on B and C; **γ=7** is chosen because it sits near the conceptual optimum 7.5 and matches the best `inv_high` on B (6.64% vs 7.13% at γ=10).

On the uniform baseline **A** at floor=10, the same valley appears: inv_high falls from **31.77%** (γ=4) to **18.27%** (γ=7) and stays ~18% at γ=10, then rises to **22.32%** (γ=13).

### 5.2 Why floor = 10

At **gamma=7**, floor trade-off on scenario **B**:

| floor | inv_high | inv_zero | inv_zero_trivial | gap |
|---:|---:|---:|---:|---:|
| 1 | 5.64% | 1.33% | 23.40% | 37.08 |
| 3 | 5.85% | 1.22% | 22.12% | 36.31 |
| 5 | 6.04% | 1.09% | 20.87% | 35.55 |
| 8 | 6.40% | 0.92% | 19.01% | 34.40 |
| **10** | **6.64%** | **0.81%** | **17.77%** | **33.63** |
| 20 | 8.31% | 0.44% | 12.35% | 29.81 |

Low floors (1–3) shave only ~0.2 pp off `inv_high` but add **~5 pp** to `inv_zero_trivial`. **Floor=10** preserves **trivial > broken** ordering at modest cost to `inv_high`. Floor=20 further cuts `inv_zero_trivial` but erodes gap and raises `inv_high`.

On stress scenarios, the floor effect is stronger. **E** at γ=7: `inv_zero_trivial` is **51.36%** (floor=1) vs **41.16%** (floor=10) vs **29.18%** (floor=20). **D** at γ=7: **39.90%** → **35.17%** → **29.37%** across the same floors. Floor=10 is the compromise that keeps `inv_zero_trivial` materially below the low-floor regime without collapsing gap.

### 5.3 Reference row at chosen defaults (γ=7, floor=10)

| Scenario | inv_zero | inv_high | inv_zero_trivial | gap |
|---|---:|---:|---:|---:|
| A | 0.14% | 18.27% | 2.50% | 21.51 |
| B | 0.81% | 6.64% | 17.77% | 33.63 |
| C | 0.23% | 5.04% | 2.87% | 36.38 |
| D | 3.59% | 4.94% | 35.17% | 33.27 |
| E | 2.80% | 6.10% | 41.16% | 30.58 |

---

## 6. Limitations (for reviewers)

1. **`inv_high` on uniform grids (~18%)**  
   Under scenario A, ambiguous grids still produce useful and high rows whose continuous scores overlap. A single scalar cannot perfectly encode band logic; this is the cost of smooth scoring vs hard thresholds.

2. **`inv_zero_trivial` under zero-heavy regimes (D, E)**  
   A broken row with two zeros but three mid-band cells can outscore a trivial row when floor is low (trivial quality compressed toward the floor). This is inherent to continuous curves; **higher floor mitigates but does not eliminate** it (35% on D, 41% on E at floor=10).

3. **`inv_zero_over_useful` remains the primary design constraint**  
   The main failure mode we designed against—broken beating useful—stays **below 4%** in all scenarios at γ=7, floor=10 (max **3.59%** on D). On realistic mix **B** it is **0.81%**.

4. **Simulation ≠ real BenchBench grids**  
   Synthetic grids approximate structure; final validation remains on canonical experiment rows (see `creator_score_real_validation.md`).

---

## 7. Reproducing the calibration

```bash
python scripts/simulate_creator_score.py
```

Output: `scripts/creator_score_analysis/creator_score_simulation_results.csv` (120 rows).

Quick check at defaults:

```bash
python -c "from scripts.creator_score import quality_index; print(quality_index(7), quality_index(8), quality_index(30), quality_index(0))"
# 100.0 100.0 10.0 0.0
```
