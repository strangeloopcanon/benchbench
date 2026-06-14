"""Creator score: continuous metric for benchmark creation quality.

Quantifies how good each model is at *creating* benchmarks (not solving them).
Complements `best_creator_signal_row` from `build_6x6_result_artifacts.py`:
that function selects the best creator categorically (lexicographic ranking),
this one produces a continuous score in [0, 1] for ranking and comparison.

The score is the product of two normalized components:
- useful_rate: fraction of solvers that landed in the useful band (1-14/30)
- difficulty: inverse of the row mean, normalized to [0, 1]

Divided by the theoretical max (all solvers in low with mean=1) to ensure
the score lives in [0, 1].
"""

import re

_TOTAL_ITEMS = 30
_MAX_POSSIBLE_RAW_SCORE = (_TOTAL_ITEMS - 1) / _TOTAL_ITEMS  # ≈ 0.967


def _score_value(cell: str) -> int | None:
    """Parse a cell of the form 'N/30' to int N, else None."""
    match = re.fullmatch(rf"(\d+)/{_TOTAL_ITEMS}", cell)
    return int(match.group(1)) if match else None


def _score_values(row: list[str]) -> list[int]:
    """Extract score integers from a grid row (skipping the first 2 label columns)."""
    return [value for cell in row[2:] if (value := _score_value(cell)) is not None]


def creator_score(row: list[str]) -> float:
    """Continuous score in [0, 1] quantifying benchmark creation quality.

    Higher = the creator produced a harder, well-specified benchmark that
    kept solvers in the useful band (1-14/30) with a low mean.

    Returns 0.0 when no valid scores are found.

    Args:
        row: A grid row in the format [creator_label, benchmark_name, "N/30", "N/30", ...]

    Returns:
        Score in [0, 1] where 1 = all solvers in low band with mean=1.
    """
    values = _score_values(row)
    if not values:
        return 0.0

    n_solvers = len(values)
    useful_count = sum(1 for v in values if 1 <= v <= 14)
    mean = sum(values) / n_solvers

    useful_rate = useful_count / n_solvers
    difficulty = 1 - (mean / _TOTAL_ITEMS)

    return (useful_rate * difficulty) / _MAX_POSSIBLE_RAW_SCORE


def creator_score_ranking(rows: list[list[str]]) -> list[tuple[str, float]]:
    """Compute creator_score for each row, return [(creator_label, score), ...] sorted descending.

    Assumes row[0] is the creator label, consistent with the convention in
    `build_6x6_result_artifacts.py`.

    Args:
        rows: List of grid rows, each in the format expected by `creator_score`.

    Returns:
        List of (creator_label, score) tuples sorted by score descending.
    """
    scored = [(row[0] if row else "unknown", creator_score(row)) for row in rows]
    return sorted(scored, key=lambda x: x[1], reverse=True)


def creator_score_difficulty(row: list[str], creator_index: int | None = None) -> float:
    """Continuous creator score based purely on benchmark difficulty for other solvers.

    Unlike `creator_score` (which uses discrete bands), this score treats solver
    performance as a continuum. Higher = the benchmark was harder for other
    models (excluding the creator's own attempt).

    The score is `1 - mean_others/30`, clamped to [0, 1].

    Args:
        row: A grid row in the format [creator_label, benchmark_name, "N/30", ...]
        creator_index: Position of the creator's own cell within the SCORE cells
            (i.e., index 0 = first solver column = row[2]). If None, all cells
            are included in the mean (use for asymmetric panels where the
            creator is not among the solvers).

    Returns:
        Score in [0, 1] where:
        - 1.0 (unreachable): all others scored 0 → broken benchmark by our definition,
          but mathematically the formula would give max(0, 1) = 1. To preserve the
          "broken = 0" semantic, we explicitly return 0.0 when mean_others == 0.
        - Close to 0.967 (max practical): all others scored 1/30
        - 0.0: all others scored 0/30 (broken benchmark)
        - 0.0: no valid score cells found
    """
    values = _score_values(row)
    if not values:
        return 0.0

    if creator_index is not None:
        if creator_index < 0 or creator_index >= len(values):
            return 0.0
        others = [v for i, v in enumerate(values) if i != creator_index]
    else:
        others = values

    if not others:
        return 0.0

    mean_others = sum(others) / len(others)
    if mean_others == 0:
        return 0.0

    return max(0.0, 1 - mean_others / _TOTAL_ITEMS)


def creator_score_difficulty_ranking(
    rows: list[list[str]],
    creator_indices: list[int | None] | None = None,
) -> list[tuple[str, float]]:
    """Compute creator_score_difficulty for each row, return sorted ranking.

    Args:
        rows: List of grid rows.
        creator_indices: Optional list mapping each row to its creator_index.
            If provided, must have the same length as rows. If None, all rows
            are computed with creator_index=None (no exclusion).

    Returns:
        List of (creator_label, score) tuples sorted by score descending.
    """
    scored: list[tuple[str, float]] = []
    for i, row in enumerate(rows):
        creator_index = creator_indices[i] if creator_indices is not None else None
        label = row[0] if row else "unknown"
        scored.append((label, creator_score_difficulty(row, creator_index)))

    return sorted(scored, key=lambda x: x[1], reverse=True)