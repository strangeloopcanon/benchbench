"""Tests for scripts/creator_score.py"""

import unittest

from scripts.creator_score import (
    creator_score,
    creator_score_difficulty,
    creator_score_difficulty_ranking,
    creator_score_quality,
    creator_score_quality_ranking,
    creator_score_ranking,
    quality_index,
    zero_count,
)


class CreatorScoreTests(unittest.TestCase):
    """Tests for the creator_score function."""

    def _make_row(self, *scores: int) -> list[str]:
        """Helper: build a grid row in the expected format.

        Format: [creator_label, benchmark_name, "N/30", "N/30", ...]
        """
        return ["creator", "bench_name"] + [f"{s}/30" for s in scores]

    def test_perfect_score_all_solvers_in_low_with_mean_one(self) -> None:
        """Theoretical max: all solvers at 1/30 → score ≈ 1.0."""
        row = self._make_row(1, 1, 1, 1, 1)
        self.assertAlmostEqual(creator_score(row), 1.0, places=4)

    def test_zero_score_all_solvers_at_zero(self) -> None:
        """Broken/impossible benchmark: all solvers at 0 → score = 0."""
        row = self._make_row(0, 0, 0, 0, 0)
        self.assertEqual(creator_score(row), 0.0)

    def test_zero_score_all_solvers_in_high_band(self) -> None:
        """Trivial benchmark: all solvers in high band (≥15) → score = 0."""
        row = self._make_row(20, 25, 30, 28, 22)
        self.assertEqual(creator_score(row), 0.0)

    def test_partial_score_mixed_distribution(self) -> None:
        """Mixed distribution: score should be strictly between 0 and 1."""
        row = self._make_row(5, 8, 12, 20, 25)
        score = creator_score(row)
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_empty_row_returns_zero(self) -> None:
        """Defensive: empty row or row with only labels returns 0."""
        self.assertEqual(creator_score([]), 0.0)
        self.assertEqual(creator_score(["creator", "bench_name"]), 0.0)

    def test_row_with_no_valid_cells_returns_zero(self) -> None:
        """Defensive: row with malformed score cells returns 0."""
        row = ["creator", "bench_name", "invalid", "N/A", ""]
        self.assertEqual(creator_score(row), 0.0)

    def test_low_band_boundary_14_counts_as_useful(self) -> None:
        """Boundary: 14/30 is the last value in the useful band."""
        row = self._make_row(14, 14, 14)
        score = creator_score(row)
        self.assertGreater(score, 0.0)

    def test_high_band_boundary_15_does_not_count_as_useful(self) -> None:
        """Boundary: 15/30 is no longer in the useful band → score = 0."""
        row = self._make_row(15, 15, 15)
        self.assertEqual(creator_score(row), 0.0)

    def test_ignores_first_two_columns(self) -> None:
        """The first two columns (creator label, benchmark name) must be ignored."""
        # If column parsing were wrong, "30/30" in the label position would skew results.
        row_normal = ["any_label", "any_name", "5/30", "8/30", "12/30"]
        row_weird_labels = ["30/30", "0/30", "5/30", "8/30", "12/30"]
        self.assertEqual(creator_score(row_normal), creator_score(row_weird_labels))


class CreatorScoreRankingTests(unittest.TestCase):
    """Tests for the creator_score_ranking function."""

    def test_ranking_sorts_descending(self) -> None:
        """Ranking must order creators by score, highest first."""
        rows = [
            ["weak_creator", "b1", "20/30", "25/30", "30/30"],   # all in high
            ["strong_creator", "b2", "2/30", "3/30", "5/30"],    # all in low, very hard
            ["broken_creator", "b3", "0/30", "0/30", "0/30"],    # all zeros
        ]
        ranking = creator_score_ranking(rows)
        self.assertEqual(ranking[0][0], "strong_creator")
        self.assertEqual(ranking[-1][0], "broken_creator")

    def test_ranking_preserves_all_creators(self) -> None:
        """Every input row must appear in the output ranking exactly once."""
        rows = [
            ["a", "b1", "5/30", "8/30"],
            ["b", "b2", "10/30", "12/30"],
            ["c", "b3", "0/30", "0/30"],
        ]
        ranking = creator_score_ranking(rows)
        labels = [label for label, _ in ranking]
        self.assertEqual(sorted(labels), ["a", "b", "c"])
        self.assertEqual(len(ranking), 3)

    def test_ranking_empty_input(self) -> None:
        """Empty input returns empty ranking."""
        self.assertEqual(creator_score_ranking([]), [])

    def test_ranking_scores_are_floats_in_unit_interval(self) -> None:
        """All scores in the ranking must be floats in [0, 1]."""
        rows = [
            ["a", "b1", "5/30", "8/30", "12/30"],
            ["b", "b2", "0/30", "0/30", "0/30"],
            ["c", "b3", "1/30", "1/30", "1/30"],
        ]
        ranking = creator_score_ranking(rows)
        for _, score in ranking:
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


class CreatorScoreDifficultyTests(unittest.TestCase):
    """Tests for the creator_score_difficulty function."""

    def _make_row(self, *scores: int) -> list[str]:
        """Helper: build a grid row in the expected format."""
        return ["creator", "bench_name"] + [f"{s}/30" for s in scores]

    def test_excludes_creator_cell_when_index_provided(self) -> None:
        """Excluding creator_index=0 computes mean over the other five cells."""
        row = self._make_row(10, 14, 11, 12, 11, 11)
        self.assertAlmostEqual(creator_score_difficulty(row, creator_index=0), 0.6067, places=3)

    def test_includes_all_cells_when_index_is_none(self) -> None:
        """With creator_index=None, all six score cells enter the mean (1 - 11.5/30)."""
        row = self._make_row(10, 14, 11, 12, 11, 11)
        self.assertAlmostEqual(creator_score_difficulty(row, creator_index=None), 0.6167, places=3)

    def test_returns_zero_when_all_others_zero(self) -> None:
        """Creator scored 5/30 but all others at 0 → broken benchmark → 0."""
        row = self._make_row(5, 0, 0, 0, 0, 0)
        self.assertEqual(creator_score_difficulty(row, creator_index=0), 0.0)

    def test_returns_zero_when_all_cells_zero_and_no_index(self) -> None:
        """All-zero row with no exclusion → broken benchmark → 0."""
        row = self._make_row(0, 0, 0, 0, 0, 0)
        self.assertEqual(creator_score_difficulty(row, creator_index=None), 0.0)

    def test_max_practical_score_when_all_others_score_one(self) -> None:
        """Others all at 1/30 with creator excluded → score ≈ 1 - 1/30."""
        row = self._make_row(20, 1, 1, 1, 1, 1)
        self.assertAlmostEqual(creator_score_difficulty(row, creator_index=0), 0.9667, places=3)

    def test_empty_row_returns_zero(self) -> None:
        """Empty row or labels-only row returns 0."""
        self.assertEqual(creator_score_difficulty([]), 0.0)
        self.assertEqual(creator_score_difficulty(["creator", "bench_name"]), 0.0)

    def test_invalid_creator_index_returns_zero(self) -> None:
        """Out-of-range creator_index is defensive → 0."""
        row = self._make_row(5, 8, 12)
        self.assertEqual(creator_score_difficulty(row, creator_index=10), 0.0)

    def test_creator_index_at_last_position(self) -> None:
        """Excluding the last score cell leaves mean over [12, 8, 5]."""
        row = self._make_row(12, 8, 5, 30)
        self.assertAlmostEqual(creator_score_difficulty(row, creator_index=3), 0.7222, places=3)

    def test_only_creator_cell_returns_zero(self) -> None:
        """Single score cell excluded entirely → empty others → 0."""
        row = self._make_row(10)
        self.assertEqual(creator_score_difficulty(row, creator_index=0), 0.0)

    def test_score_is_continuous_unlike_bands(self) -> None:
        """Small score differences produce distinct difficulty scores."""
        row_a = self._make_row(5, 5, 5, 5, 5)
        row_b = self._make_row(5, 5, 5, 5, 6)
        self.assertNotEqual(
            creator_score_difficulty(row_a),
            creator_score_difficulty(row_b),
        )


class CreatorScoreDifficultyRankingTests(unittest.TestCase):
    """Tests for the creator_score_difficulty_ranking function."""

    def test_ranking_sorts_descending(self) -> None:
        """Hardest benchmark ranks first when no creator exclusion."""
        rows = [
            ["easy_creator", "b1", "25/30", "28/30", "30/30"],
            ["hard_creator", "b2", "2/30", "3/30", "5/30"],
            ["mid_creator", "b3", "10/30", "12/30", "14/30"],
        ]
        ranking = creator_score_difficulty_ranking(rows)
        self.assertEqual(ranking[0][0], "hard_creator")
        self.assertEqual(ranking[-1][0], "easy_creator")

    def test_ranking_with_creator_indices(self) -> None:
        """Per-row creator_index exclusion affects ranking order."""
        rows = [
            ["hard", "b1", "25/30", "2/30", "2/30", "2/30"],
            ["easy", "b2", "3/30", "28/30", "28/30", "28/30"],
            ["mid", "b3", "10/30", "10/30", "10/30", "10/30"],
        ]
        creator_indices = [0, 0, None]
        ranking = creator_score_difficulty_ranking(rows, creator_indices)
        self.assertEqual(ranking[0][0], "hard")
        self.assertEqual(ranking[1][0], "mid")
        self.assertEqual(ranking[2][0], "easy")

    def test_ranking_preserves_all_rows(self) -> None:
        """Every input row appears exactly once in the output."""
        rows = [
            ["a", "b1", "5/30", "8/30"],
            ["b", "b2", "10/30", "12/30"],
            ["c", "b3", "0/30", "0/30"],
        ]
        ranking = creator_score_difficulty_ranking(rows)
        labels = [label for label, _ in ranking]
        self.assertEqual(len(ranking), 3)
        self.assertEqual(sorted(labels), ["a", "b", "c"])

    def test_ranking_empty_input(self) -> None:
        """Empty input returns empty ranking."""
        self.assertEqual(creator_score_difficulty_ranking([]), [])

    def test_ranking_scores_in_unit_interval(self) -> None:
        """All difficulty scores must be floats in [0, 1]."""
        rows = [
            ["a", "b1", "5/30", "8/30", "12/30"],
            ["b", "b2", "0/30", "0/30", "0/30"],
            ["c", "b3", "1/30", "1/30", "1/30"],
        ]
        ranking = creator_score_difficulty_ranking(rows)
        for _, score in ranking:
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


class QualityIndexTests(unittest.TestCase):
    """Tests for the quality_index function."""

    def test_anchor_scores_with_defaults(self) -> None:
        """Calibration anchors: 7 and 8 → 100, 0 → 0, 30 → floor 10."""
        self.assertAlmostEqual(quality_index(7), 100.0, places=4)
        self.assertAlmostEqual(quality_index(8), 100.0, places=4)
        self.assertEqual(quality_index(0), 0.0)
        self.assertAlmostEqual(quality_index(30), 10.0, places=4)

    def test_symmetry_around_peak_7_5(self) -> None:
        """Scores equidistant from peak 7.5 receive equal quality."""
        self.assertAlmostEqual(quality_index(6), quality_index(9), places=4)
        self.assertAlmostEqual(quality_index(1), quality_index(14), places=4)

    def test_monotonicity_within_useful_band(self) -> None:
        """Quality rises from 1 to 7 and falls from 8 to 14."""
        rising = [quality_index(s) for s in range(1, 8)]
        for lower, higher in zip(rising, rising[1:]):
            self.assertLess(lower, higher)

        falling = [quality_index(s) for s in range(8, 15)]
        for higher, lower in zip(falling, falling[1:]):
            self.assertGreater(higher, lower)

    def test_invalid_gamma_raises_value_error(self) -> None:
        """Non-positive gamma is rejected."""
        with self.assertRaises(ValueError):
            quality_index(7, gamma=0.0)
        with self.assertRaises(ValueError):
            quality_index(7, gamma=-1.0)

    def test_floor_val_respected_at_score_30(self) -> None:
        """floor_val sets quality at score 30."""
        self.assertAlmostEqual(quality_index(30, floor_val=5.0), 5.0, places=4)


class CreatorScoreQualityTests(unittest.TestCase):
    """Tests for the creator_score_quality function."""

    def _make_row(self, *scores: int) -> list[str]:
        return ["creator", "bench_name"] + [f"{s}/30" for s in scores]

    def test_empty_row_returns_zero(self) -> None:
        """No valid score cells → 0.0."""
        self.assertEqual(creator_score_quality([]), 0.0)
        self.assertEqual(creator_score_quality(["creator", "bench_name"]), 0.0)

    def test_excludes_creator_index_when_valid(self) -> None:
        """creator_index excludes that solver cell from the mean."""
        row = self._make_row(10, 14, 11, 12, 11, 11)
        with_exclusion = creator_score_quality(row, creator_index=0)
        without_exclusion = creator_score_quality(row, creator_index=None)
        self.assertNotEqual(with_exclusion, without_exclusion)

    def test_invalid_creator_index_returns_zero(self) -> None:
        """Out-of-range creator_index is defensive → 0.0."""
        row = self._make_row(10, 14, 11, 12, 11, 11)
        self.assertEqual(creator_score_quality(row, creator_index=10), 0.0)
        self.assertEqual(creator_score_quality(row, creator_index=-1), 0.0)

    def test_excluding_all_cells_returns_zero(self) -> None:
        """Single score cell excluded entirely → empty others → 0.0."""
        row = self._make_row(10)
        self.assertEqual(creator_score_quality(row, creator_index=0), 0.0)

    def test_reimbursement_forensics_known_score(self) -> None:
        """Canonical Round 3 incumbent row with creator_index=0."""
        row = [
            "GPT-5.2",
            "Reimbursement Forensics",
            "10/30",
            "14/30",
            "11/30",
            "12/30",
            "11/30",
            "11/30",
        ]
        self.assertAlmostEqual(
            creator_score_quality(row, creator_index=0),
            73.59,
            places=1,
        )

    def test_gamma_and_floor_val_change_result(self) -> None:
        """Parameter changes propagate into the row score."""
        row = self._make_row(10, 14, 11, 12, 11, 11)
        default_score = creator_score_quality(row, creator_index=0)
        wider_gamma = creator_score_quality(row, creator_index=0, gamma=13.0)
        lower_floor = creator_score_quality(row, creator_index=0, floor_val=5.0)
        self.assertNotEqual(default_score, wider_gamma)
        self.assertNotEqual(default_score, lower_floor)


class ZeroCountTests(unittest.TestCase):
    """Tests for the zero_count function."""

    def _make_row(self, *scores: int) -> list[str]:
        return ["creator", "bench_name"] + [f"{s}/30" for s in scores]

    def test_counts_zeros_excluding_creator(self) -> None:
        """Counts zero cells among non-creator solvers."""
        row = self._make_row(0, 5, 0, 8, 0, 12)
        self.assertEqual(zero_count(row, creator_index=0), 2)

    def test_includes_all_cells_when_index_is_none(self) -> None:
        """Without exclusion, all zero cells count."""
        row = self._make_row(0, 5, 0, 8)
        self.assertEqual(zero_count(row, creator_index=None), 2)

    def test_invalid_creator_index_returns_zero(self) -> None:
        """Out-of-range creator_index is defensive → 0."""
        row = self._make_row(0, 0, 5)
        self.assertEqual(zero_count(row, creator_index=5), 0.0)


class CreatorScoreQualityRankingTests(unittest.TestCase):
    """Tests for the creator_score_quality_ranking function."""

    def test_ranking_sorts_descending(self) -> None:
        """Higher quality rows rank first."""
        rows = [
            ["easy", "b1", "25/30", "28/30", "30/30"],
            ["strong", "b2", "7/30", "8/30", "9/30"],
            ["broken", "b3", "0/30", "0/30", "0/30"],
        ]
        ranking = creator_score_quality_ranking(rows)
        self.assertEqual(ranking[0][0], "strong")
        self.assertEqual(ranking[-1][0], "broken")
        scores = [score for _, score in ranking]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_ranking_with_creator_indices(self) -> None:
        """Per-row creator_index exclusion affects ranking order."""
        rows = [
            ["a", "b1", "10/30", "7/30", "8/30", "9/30"],
            ["b", "b2", "7/30", "25/30", "28/30", "30/30"],
        ]
        ranking_no_indices = creator_score_quality_ranking(rows)
        ranking_with_indices = creator_score_quality_ranking(rows, creator_indices=[0, 0])
        self.assertNotEqual(ranking_no_indices, ranking_with_indices)


if __name__ == "__main__":
    unittest.main()