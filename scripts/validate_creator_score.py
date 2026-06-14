#!/usr/bin/env python3
"""Validate creator_score and creator_score_difficulty against real BenchBench data.

This script reproduces the validation of both creator score implementations
against the canonical Round 3 grid (the same grid documented in
experiments/canonical/README.md). It prints:

  1. The grid rows being analyzed (creator, benchmark, solver scores).
  2. The mapping from creator rows to solver columns (used to exclude
     each creator's own cell when computing creator_score_difficulty).
  3. Three rankings side by side:
     - creator_score        (bands-based, see creator_score.py)
     - creator_score_difficulty  (continuous, see creator_score.py)
     - best_creator_signal_row   (lexicographic, see build_6x6_result_artifacts.py)
  4. A side-by-side comparison table.

Run from the repo root:

    python scripts/validate_creator_score.py

No arguments. Pure read-only: does not modify any files.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_6x6_result_artifacts import (
    SOLVERS_CURRENT,
    best_creator_signal_row,
    build_grid,
    incumbent_carry_forward_grid,
)
from scripts.creator_score import (
    creator_score,
    creator_score_difficulty,
    creator_score_difficulty_ranking,
    creator_score_ranking,
)


def load_canonical_round3_grid() -> list[list[str]]:
    """Rebuild the canonical Round 3 grid (same logic as build_6x6_result_artifacts.main)."""
    exp004_rows = build_grid(
        "experiments/004_feedback_sweep_20260522_225208",
        "experiments/006_claude_opus_feedback_style_20260523_125611",
        [
            ("gpt-5.2", "GPT-5.2", "Reimbursement Forensics"),
            ("gpt-5.4", "GPT-5.4", "release_packet_arbitration"),
            ("gpt-5.5", "GPT-5.5", "Cross-Document Obligation Resolution"),
            ("gemini-3.1-pro", "Gemini 3.1 Pro", "Corrupted LZ77 Recovery"),
            ("gemini-3.5-flash-high", "Gemini 3.5 Flash", "MFN-Cascade"),
            ("opus", "Claude Opus", "Conlang Rosetta"),
        ],
        skip={("gpt-5.5", "opus"): "skip"},
    )
    exp007_rows = build_grid(
        "experiments/007_full_feedback_6x6_20260523_172919",
        None,
        [
            ("gpt-5.2", "GPT-5.2", "Service Credit Forensics"),
            ("gpt-5.4", "GPT-5.4", "Catalog Royalty Forensics"),
            ("gpt-5.5", "GPT-5.5", "Prior Authorization Forensics"),
            ("gemini-3.1-pro", "Gemini 3.1 Pro", "Commercial Lease CAM Reconciliation"),
            ("gemini-3.5-flash-high", "Gemini 3.5 Flash", "Maritime Freight & Customs Audit"),
            ("claude-opus", "Claude Opus", "Construction Progress Payment Certification"),
        ],
        solvers=[
            ("gpt-5.2", "GPT-5.2"),
            ("gpt-5.4", "GPT-5.4"),
            ("gpt-5.5", "GPT-5.5"),
            ("gemini-3.1-pro", "Gemini 3.1 Pro"),
            ("gemini-3.5-flash-high", "Gemini 3.5 Flash"),
            ("claude-opus", "Claude Opus"),
        ],
    )
    return incumbent_carry_forward_grid(exp004_rows, exp007_rows)


def format_score(score: float) -> str:
    pct = score * 100.0
    return f"{score:.2f} ({pct:.1f}%)"


def normalize_creator_label(label: str) -> str:
    """Strip presentation suffixes so row labels match solver column labels."""
    return label.replace(" (frozen)", "").strip()


def resolve_creator_indices(
    grid: list[list[str]],
    solvers: list[tuple[str, str]],
) -> list[int | None]:
    """Map each grid row to the solver column index for that creator's own attempt."""
    solver_labels = [label for _solver_id, label in solvers]
    indices: list[int | None] = []
    print("=" * 72)
    print("Solver column order (SOLVERS_CURRENT)")
    print("=" * 72)
    for idx, (solver_id, label) in enumerate(solvers):
        print(f"  col {idx}: {solver_id:24} -> {label}")
    print()
    print("Creator row -> solver column mapping")
    print("-" * 72)
    for row in grid:
        creator_label = row[0] if row else ""
        normalized = normalize_creator_label(creator_label)
        if normalized in solver_labels:
            creator_index = solver_labels.index(normalized)
            indices.append(creator_index)
            print(
                f"  row '{creator_label}' -> col {creator_index} "
                f"({solvers[creator_index][1]}, id={solvers[creator_index][0]})"
            )
        else:
            indices.append(None)
            print(f"  row '{creator_label}' -> NO MATCH (creator_index=None)")
    print()
    return indices


def main() -> None:
    grid = load_canonical_round3_grid()

    print("=" * 72)
    print("Canonical Round 3 grid (source: build_grid + incumbent_carry_forward_grid)")
    print("  exp004: experiments/004_feedback_sweep_20260522_225208 (+ opus from 006)")
    print("  exp007: experiments/007_full_feedback_6x6_20260523_172919")
    print("  merge:  incumbent_carry_forward_grid() in build_6x6_result_artifacts.py")
    print("=" * 72)
    print()
    print(f"Rows: {len(grid)}  |  Solvers per row: {len(grid[0]) - 2 if grid else 0}")
    print()
    for row in grid:
        cells = ", ".join(row[2:])
        print(f"  {row[0]:28} | {row[1]:45} | {cells}")
    print()

    creator_indices = resolve_creator_indices(grid, SOLVERS_CURRENT)

    print("=" * 72)
    print("creator_score_ranking (bands-based, current MVP)")
    print("=" * 72)
    bands_ranking = creator_score_ranking(grid)
    for rank, (creator, score) in enumerate(bands_ranking, start=1):
        print(f"  {rank}. {creator:28}  {format_score(score)}")
    print()

    print("=" * 72)
    print("creator_score_difficulty_ranking (continuous, difficulty-based)")
    print("=" * 72)
    difficulty_ranking = creator_score_difficulty_ranking(grid, creator_indices)
    for rank, (creator, score) in enumerate(difficulty_ranking, start=1):
        print(f"  {rank}. {creator:28}  {format_score(score)}")
    print()

    print("=" * 72)
    print("best_creator_signal_row (lexicographic winner)")
    print("=" * 72)
    best_row, best_stats = best_creator_signal_row(grid)
    print(f"  Winner: {best_row[0]}")
    print(f"  Benchmark: {best_row[1]}")
    print(f"  Cells: {', '.join(best_row[2:])}")
    print(f"  Stats: low={best_stats['low']}, zero={best_stats['zero']}, high={best_stats['high']}, mean={best_stats['mean']}")
    print()

    bands_winner = bands_ranking[0][0] if bands_ranking else None
    difficulty_winner = difficulty_ranking[0][0] if difficulty_ranking else None
    signal_winner = best_row[0]
    winners = {
        "creator_score_ranking": bands_winner,
        "creator_score_difficulty_ranking": difficulty_winner,
        "best_creator_signal_row": signal_winner,
    }
    unique_winners = set(winners.values())

    print("=" * 72)
    print("Winner comparison")
    print("=" * 72)
    print(f"  creator_score_ranking #1:            {bands_winner}")
    print(f"  creator_score_difficulty_ranking #1: {difficulty_winner}")
    print(f"  best_creator_signal_row:             {signal_winner}")
    if len(unique_winners) == 1:
        print("  >>> MATCH: all three methods pick the same creator label.")
    else:
        print("  >>> DIFFER: at least one method disagrees on the winner.")
        if bands_winner != difficulty_winner:
            print("      bands vs difficulty: different #1")
        if bands_winner != signal_winner:
            print(f"      bands top: {format_score(bands_ranking[0][1])}")
            for label, score in bands_ranking:
                if label == signal_winner:
                    pos = next(i for i, (l, _) in enumerate(bands_ranking, 1) if l == label)
                    print(f"      signal winner ranks #{pos} in bands: {format_score(score)}")
        if difficulty_winner != signal_winner:
            print(f"      difficulty top: {format_score(difficulty_ranking[0][1])}")
            for label, score in difficulty_ranking:
                if label == signal_winner:
                    pos = next(i for i, (l, _) in enumerate(difficulty_ranking, 1) if l == label)
                    print(f"      signal winner ranks #{pos} in difficulty: {format_score(score)}")
    print()

    bands_by_label = {label: score for label, score in bands_ranking}
    difficulty_by_label = {label: score for label, score in difficulty_ranking}
    print("=" * 72)
    print("Side-by-side comparison")
    print("=" * 72)
    header_creator = "Creator"
    header_bands = "Bands score"
    header_diff = "Difficulty score"
    print(f"  {header_creator:28}  {header_bands:18}  {header_diff}")
    for row, creator_index in zip(grid, creator_indices):
        label = row[0]
        bands_score = bands_by_label.get(label, creator_score(row))
        diff_score = difficulty_by_label.get(
            label,
            creator_score_difficulty(row, creator_index),
        )
        print(f"  {label:28}  {format_score(bands_score):18}  {format_score(diff_score)}")
    print()


if __name__ == "__main__":
    main()
