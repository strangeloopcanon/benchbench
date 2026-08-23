# Creator quality score: real-grid validation

This document validates `creator_score_quality` on **one** complete BenchBench grid where all creators were evaluated by the **same six-solver panel**. Scores are **not** comparable across different experiments (different sweeps may use different solver sets or conditions).

Computed with defaults: `gamma=7.0`, `floor_val=10.0`, `peak=7.5`. Each creator's own solver column is excluded via `creator_index` (square grid).

Implementation: `scripts/creator_score.py`. Grid rebuilt with the same logic as `scripts/build_6x6_result_artifacts.py` and `scripts/validate_creator_score.py`.

---

## 1. Grid chosen

**Canonical Round 3 (6×6)** — presentation layer documented in `experiments/canonical/README.md`.

| Property | Value |
|---|---|
| Primary raw run | `experiments/007_full_feedback_6x6_20260523_172919` |
| Incumbent row source | `experiments/004_feedback_sweep_20260522_225208` (GPT-5.2 Reimbursement Forensics carried forward) |
| Solver panel | GPT-5.2, GPT-5.4, GPT-5.5, Gemini 3.1 Pro, Gemini 3.5 Flash, Claude Opus (`SOLVERS_CURRENT`) |
| Creators in grid | 6 (one benchmark per creator, same run) |

**Why this grid:** It is the most complete and representative **single-matrix** result in the repo: six creators from one challenger sweep (007), plus the frozen incumbent row from 004 so the comparison matches Rohit's canonical narrative. Raw 007 alone would include GPT-5.2's broken Service Credit row; the canonical merge is the intended evaluation grid.

Score cells are read from `score_solver_*.json` under each `candidate_created_by_*` directory (via `build_grid()`).

---

## 2. Per-creator results (canonical Round 3)

Solver column order: GPT-5.2, GPT-5.4, GPT-5.5, Gemini 3.1 Pro, Gemini 3.5 Flash, Claude Opus.

| Rank | Creator | Benchmark | Solver scores (6 cells) | quality | difficulty | zero_count | Rohit verdict | Score source |
|---:|---|---|---|---:|---:|---:|---|---|
| 1 | GPT-5.2 (frozen) | Reimbursement Forensics | 10, 14, 11, 12, 11, 11 | **73.59** | 0.6067 | 0 | current target to beat | `experiments/004_feedback_sweep_20260522_225208/run/candidate_created_by_gpt_5_2/score_solver_*.json` |
| 2 | Gemini 3.5 Flash | Maritime Freight & Customs Audit | 4, 23, 15, 21, 25, 25 | **36.67** | 0.4133 | 0 | separates solvers, too easy at top | `experiments/007_full_feedback_6x6_20260523_172919/run/candidate_created_by_gemini_3_5_flash_high/score_solver_*.json` |
| 3 | Gemini 3.1 Pro | Commercial Lease CAM Reconciliation | 1, 26, 26, 16, 18, 26 | **25.47** | 0.3533 | 0 | separates solvers, too easy at top | `experiments/007_full_feedback_6x6_20260523_172919/run/candidate_created_by_gemini_3_1_pro/score_solver_*.json` |
| 4 | GPT-5.5 | Prior Authorization Forensics | 25, 24, 24, 23, 24, 24 | **16.43** | 0.2000 | 0 | too easy | `experiments/007_full_feedback_6x6_20260523_172919/run/candidate_created_by_gpt_5_5/score_solver_*.json` |
| 5 | GPT-5.4 | Catalog Royalty Forensics | 27, 30, 27, 25, 27, 25 | **13.52** | 0.1267 | 0 | too easy | `experiments/007_full_feedback_6x6_20260523_172919/run/candidate_created_by_gpt_5_4/score_solver_*.json` |
| 6 | Claude Opus | Construction Progress Payment Certification | 30, 30, 30, 30, 29, 30 | **10.15** | 0.0067 | 0 | saturated | `experiments/007_full_feedback_6x6_20260523_172919/run/candidate_created_by_claude_opus/score_solver_*.json` |

Rohit verdicts from `experiments/canonical/README.md` (completion proxy table and Round 3 notes).

**Ranking by `creator_score_quality`:** GPT-5.2 (frozen) → Gemini 3.5 Flash → Gemini 3.1 Pro → GPT-5.5 → GPT-5.4 → Claude Opus.

### Comparison with Rohit's judgments

The metric **aligns with the headline creator story**: Reimbursement Forensics (GPT-5.2) ranks first by a wide margin (73.59 vs 36.67 for the next row), matching the frozen incumbent as "current target to beat." Saturated and too-easy rows (Claude Opus, GPT-5.4, GPT-5.5) land at the bottom with quality 10–16, consistent with reject/too-easy reads. The two Round 3 **challengers** (Gemini lease and freight) rank second and third—above the easy/saturated rows but well below the incumbent—which matches Rohit's framing that they "separated solvers" yet did **not** beat Reimbursement Forensics because top solvers still scored too high. The metric does not fully encode *how much* top-end saturation matters (e.g. 26/30 peaks); it compresses that into lower quality rather than a separate reject flag.

---

## 3. Case study: Claude Fable 5 (Experiment 008) — separate, not in grid ranking

Experiment `experiments/008_fable_creator_sweep_20260610_085405` is a **single-creator** run (not a multi-creator grid). It must **not** be merged into the Round 3 ranking above.

Benchmark: **Rosetta Fieldwork**. Solver scores from `experiments/008_fable_creator_sweep_20260610_085405/summary.md`:

| Solver | Score |
|---|---:|
| gpt-5.2 | 0/30 |
| gpt-5.4 | 14/30 |
| gpt-5.5 | 11/30 |
| Gemini 3.1 Pro | 24/30 |
| Gemini 3.5 Flash | 27/30 |
| claude-opus | 0/30 |

Fable is not in the solver panel → `creator_index=None` (all six cells count).

| Variant | Cells used | quality | zero_count | Rohit read |
|---|---|---:|---:|---|
| **Raw (6 solvers)** | 0, 14, 11, 24, 27, 0 | **27.36** | **2** | reject; max 27/30 |
| **Usable (4 solvers)** | 14, 11, 24, 27 (exclude gpt-5.2 and claude-opus infra failures) | **41.04** | **0** | same reject on max score |

Infrastructure note from `summary.md`: gpt-5.2 and claude-opus zeros are **infra failures** (Codex 400, solver timeout), not benchmark difficulty. Rohit reads the row as a four-solver result.

**Interpretation:** The raw quality (27.36) is depressed by two infra zeros that `quality_index` treats as broken signal (0 quality per cell). That pulls the row toward broken-benchmark territory despite mid-band scores from the four working solvers. Excluding those cells yields 41.04—still below a strong incumbent (~74) and consistent with reject (max 27/30 = trivial). This illustrates why **`zero_count` is informational, not structural**: it flags two zeros for human review without hard-penalizing the row beyond what the quality curve already does; a structural infra penalty would wrongly attribute solver infrastructure failures to benchmark quality.

---

## 4. Reproducing these numbers

```bash
python scripts/validate_creator_score.py   # prints canonical grid rows
```

Or recompute quality/difficulty/zero_count from the grid loader in `scripts/validate_creator_score.py` with `creator_score_quality(row, creator_index)`.
