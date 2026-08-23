#!/usr/bin/env python3
"""Monte Carlo sweep of creator quality_index calibration parameters.

Simulates synthetic 6x6 BenchBench-style grids (6 creator rows, 5 non-creator
solver scores per row, integers 0-30) under five row-generation scenarios, sweeps
``gamma`` and ``floor_val``, and measures how often the quality metric inverts
sensible row ordering.

Scenarios:
  A (uniform): each cell is uniform on 0..30.
  B (adverse): creator-type mix good/easy/mixed/broken = 40/30/20/10; each row
     draws a type, then each cell samples a band and score within it.
  C (clean homogeneous): same mechanics as B, mix 55/40/5/0 (no broken creators).
  D (weak solver): same row types as B, but one random solver column per grid is
     weak: that cell is forced to 0 with probability 0.6, else keeps its drawn
     value (column-correlated zeros, unlike B's dispersed zeros).
  E (stress): same mechanics as B, mix 20/20/20/40 (heavy broken population).

Inversion rates (per grid, averaged over N grids):
  inv_zero_over_useful: a broken row (2+ zeros) scores higher than a useful row
     (3+ cells in 1-14).
  inv_high_over_low: a high row (3+ cells in 15-30) scores higher than a useful
     row (3+ cells in 1-14).
  inv_zero_over_trivial: a broken row scores higher than a high/trivial row
     (3+ cells in 15-30).

Secondary metric:
  gap_useful_trivial: median(useful row scores) - median(high row scores), averaged
     across grids where both row types exist.

Paired comparison:
  Within each scenario, the same N grids are reused for every (gamma, floor)
  combination. Row classification (broken/useful/high) is computed once per grid;
  only quality scores are recomputed per parameter combo. This isolates parameter
  effects from sampling noise and speeds up the sweep. Scenarios are not paired
  across each other (different generative processes). Seeds: scenario *i* in
  ``SCENARIOS`` uses ``seed + i`` (A=seed, B=seed+1, ...).

Run from the repo root:

    python scripts/simulate_creator_score.py
    python scripts/simulate_creator_score.py --n 2000
"""

from __future__ import annotations

import argparse
import csv
import random
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collections.abc import Callable

from scripts.creator_score import creator_score_quality, quality_index

# --- Configuration (edit here) ------------------------------------------------

RANDOM_SEED = 42
N_GRIDS = 50_000
GAMMAS = [4, 7, 10, 13]
FLOORS = [1, 3, 5, 8, 10, 20]
SCENARIOS = ("A", "B", "C", "D", "E")

N_CREATORS = 6
N_SOLVER_CELLS = 5

OUTPUT_CSV = Path(__file__).resolve().parent / "creator_score_analysis" / "creator_score_simulation_results.csv"

# Band probabilities per creator type: (P(zero), P(useful 1-14), P(high 15-30))
TYPE_BANDS: dict[str, tuple[float, float, float]] = {
    "good": (0.03, 0.82, 0.15),
    "easy": (0.02, 0.20, 0.78),
    "mixed": (0.05, 0.45, 0.50),
    "broken": (0.65, 0.25, 0.10),
}

# Population mix per typed scenario (must sum to 1.0)
SCENARIO_MIXES: dict[str, dict[str, float]] = {
    "B": {"good": 0.40, "easy": 0.30, "mixed": 0.20, "broken": 0.10},
    "C": {"good": 0.55, "easy": 0.40, "mixed": 0.05, "broken": 0.00},
    "E": {"good": 0.20, "easy": 0.20, "mixed": 0.20, "broken": 0.40},
}

WEAK_SOLVER_ZERO_PROB = 0.6

# --- Types --------------------------------------------------------------------

Grid = list[list[int]]
RowFlags = tuple[bool, bool, bool]  # (broken, useful, high)


@dataclass(frozen=True)
class SweepResult:
    scenario: str
    gamma: float
    floor: float
    n_grids: int
    inv_zero_over_useful: float
    inv_high_over_low: float
    inv_zero_over_trivial: float
    gap_useful_trivial: float


@dataclass(frozen=True)
class PrecomputedGrid:
    """Raw solver scores and row flags for one synthetic grid."""

    rows: list[list[int]]
    flags: list[RowFlags]


def scenario_seed(base_seed: int, scenario: str) -> int:
    """Deterministic seed per scenario (A=base, B=base+1, ...)."""
    return base_seed + SCENARIOS.index(scenario)


# --- Row generation -----------------------------------------------------------

def _sample_band(rng: random.Random, probs: tuple[float, float, float]) -> int:
    p_zero, p_useful, p_high = probs
    roll = rng.random()
    if roll < p_zero:
        return 0
    if roll < p_zero + p_useful:
        return rng.randint(1, 14)
    return rng.randint(15, 30)


def _sample_row(rng: random.Random, mix: dict[str, float]) -> list[int]:
    types = list(mix.keys())
    weights = [mix[t] for t in types]
    band_probs = TYPE_BANDS[rng.choices(types, weights=weights, k=1)[0]]
    return [_sample_band(rng, band_probs) for _ in range(N_SOLVER_CELLS)]


def generate_grid_uniform(rng: random.Random) -> Grid:
    return [[rng.randint(0, 30) for _ in range(N_SOLVER_CELLS)] for _ in range(N_CREATORS)]


def generate_grid_typed(rng: random.Random, mix: dict[str, float]) -> Grid:
    return [_sample_row(rng, mix) for _ in range(N_CREATORS)]


def generate_grid_weak_solver(rng: random.Random, mix: dict[str, float]) -> Grid:
    """Typed rows (B mix) with one weak solver column forced to 0 with high probability."""
    weak_col = rng.randrange(N_SOLVER_CELLS)
    grid: Grid = []
    for _ in range(N_CREATORS):
        row = _sample_row(rng, mix)
        if rng.random() < WEAK_SOLVER_ZERO_PROB:
            row[weak_col] = 0
        grid.append(row)
    return grid


def _build_scenario_generators() -> dict[str, Callable[[random.Random], Grid]]:
    generators: dict[str, Callable[[random.Random], Grid]] = {
        "A": generate_grid_uniform,
    }
    for name, mix in SCENARIO_MIXES.items():
        generators[name] = lambda rng, m=mix: generate_grid_typed(rng, m)
    generators["D"] = lambda rng: generate_grid_weak_solver(rng, SCENARIO_MIXES["B"])
    return generators


SCENARIO_GENERATORS = _build_scenario_generators()


def generate_grid(scenario: str, rng: random.Random) -> Grid:
    try:
        return SCENARIO_GENERATORS[scenario](rng)
    except KeyError as exc:
        raise ValueError(f"unknown scenario: {scenario}") from exc


# --- Row scoring and classification -------------------------------------------

def row_score(cells: list[int], gamma: float, floor: float) -> float:
    """Average quality_index over solver cells (floor sweep uses quality_index directly)."""
    return sum(quality_index(s, gamma=gamma, floor_val=floor) for s in cells) / len(cells)


def classify_row(cells: list[int]) -> RowFlags:
    zeros = sum(1 for s in cells if s == 0)
    useful = sum(1 for s in cells if 1 <= s <= 14)
    high = sum(1 for s in cells if 15 <= s <= 30)
    broken = zeros >= 2
    low = useful >= 3
    high_row = high >= 3
    return broken, low, high_row


def grid_inversions(scores: list[float], flags: list[RowFlags]) -> tuple[bool, bool, bool]:
    broken_idx = [i for i, f in enumerate(flags) if f[0]]
    useful_idx = [i for i, f in enumerate(flags) if f[1]]
    high_idx = [i for i, f in enumerate(flags) if f[2]]

    inv_zero = any(
        scores[b] > scores[u] for b in broken_idx for u in useful_idx if b != u
    )
    inv_high = any(
        scores[h] > scores[l] for h in high_idx for l in useful_idx if h != l
    )
    inv_zero_trivial = any(
        scores[b] > scores[h] for b in broken_idx for h in high_idx if b != h
    )
    return inv_zero, inv_high, inv_zero_trivial


def grid_gap(scores: list[float], flags: list[RowFlags]) -> float | None:
    useful_scores = [scores[i] for i, f in enumerate(flags) if f[1]]
    high_scores = [scores[i] for i, f in enumerate(flags) if f[2]]
    if not useful_scores or not high_scores:
        return None
    return statistics.median(useful_scores) - statistics.median(high_scores)


# --- Precomputation and evaluation --------------------------------------------

def precompute_grids(scenario: str, n_grids: int, seed: int) -> list[PrecomputedGrid]:
    """Generate N grids once for a scenario; classify rows from raw scores only."""
    rng = random.Random(scenario_seed(seed, scenario))
    precomputed: list[PrecomputedGrid] = []
    for _ in range(n_grids):
        grid = generate_grid(scenario, rng)
        flags = [classify_row(row) for row in grid]
        precomputed.append(PrecomputedGrid(rows=grid, flags=flags))
    return precomputed


def evaluate_combination(
    scenario: str,
    gamma: float,
    floor: float,
    grids: list[PrecomputedGrid],
) -> SweepResult:
    """Score precomputed grids for one (gamma, floor) combo; reuse row flags."""
    inv_zero_count = 0
    inv_high_count = 0
    inv_zero_trivial_count = 0
    gaps: list[float] = []

    for grid in grids:
        scores = [row_score(row, gamma, floor) for row in grid.rows]
        inv_zero, inv_high, inv_zero_trivial = grid_inversions(scores, grid.flags)
        inv_zero_count += int(inv_zero)
        inv_high_count += int(inv_high)
        inv_zero_trivial_count += int(inv_zero_trivial)

        gap = grid_gap(scores, grid.flags)
        if gap is not None:
            gaps.append(gap)

    n_grids = len(grids)
    return SweepResult(
        scenario=scenario,
        gamma=gamma,
        floor=floor,
        n_grids=n_grids,
        inv_zero_over_useful=inv_zero_count / n_grids,
        inv_high_over_low=inv_high_count / n_grids,
        inv_zero_over_trivial=inv_zero_trivial_count / n_grids,
        gap_useful_trivial=statistics.mean(gaps) if gaps else float("nan"),
    )


def run_sweep(n_grids: int, seed: int) -> list[SweepResult]:
    results: list[SweepResult] = []
    for scenario in SCENARIOS:
        grids = precompute_grids(scenario, n_grids, seed)
        for gamma in GAMMAS:
            for floor in FLOORS:
                results.append(evaluate_combination(scenario, gamma, floor, grids))
    return results


# --- Output -------------------------------------------------------------------

def print_table(results: list[SweepResult]) -> None:
    header = (
        f"{'scenario':>8}  {'gamma':>5}  {'floor':>5}  "
        f"{'inv_zero%':>10}  {'inv_high%':>10}  {'inv_z>triv%':>12}  {'gap_util':>10}"
    )
    print(header)
    print("-" * len(header))
    for row in results:
        print(
            f"{row.scenario:>8}  {row.gamma:>5.0f}  {row.floor:>5.0f}  "
            f"{row.inv_zero_over_useful * 100:>9.2f}%  "
            f"{row.inv_high_over_low * 100:>9.2f}%  "
            f"{row.inv_zero_over_trivial * 100:>11.2f}%  "
            f"{row.gap_useful_trivial:>10.2f}"
        )


def write_csv(results: list[SweepResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario",
                "gamma",
                "floor",
                "n_grids",
                "inv_zero_over_useful",
                "inv_high_over_low",
                "inv_zero_over_trivial",
                "gap_useful_trivial",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "scenario": row.scenario,
                    "gamma": row.gamma,
                    "floor": row.floor,
                    "n_grids": row.n_grids,
                    "inv_zero_over_useful": row.inv_zero_over_useful,
                    "inv_high_over_low": row.inv_high_over_low,
                    "inv_zero_over_trivial": row.inv_zero_over_trivial,
                    "gap_useful_trivial": row.gap_useful_trivial,
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monte Carlo sweep of quality_index parameters.")
    parser.add_argument(
        "--n",
        type=int,
        default=N_GRIDS,
        help=f"number of grids per scenario (default: {N_GRIDS}; reused across all gamma/floor combos)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"random seed (default: {RANDOM_SEED})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Sanity: creator_score_quality available for real rows; sweep uses quality_index.
    _ = creator_score_quality

    print(
        f"Monte Carlo sweep (paired within scenario): {len(SCENARIOS)} scenarios x "
        f"{len(GAMMAS)} gammas x {len(FLOORS)} floors = "
        f"{len(SCENARIOS) * len(GAMMAS) * len(FLOORS)} combos, "
        f"N={args.n} grids per scenario, seed={args.seed} (scenario i uses seed+i)"
    )
    print()

    results = run_sweep(n_grids=args.n, seed=args.seed)
    print_table(results)
    print()

    write_csv(results, OUTPUT_CSV)
    print(f"Wrote CSV: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
