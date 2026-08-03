import json
from pathlib import Path
import tempfile

import pytest

from benchbench_results import ScoreParseError, parse_score_data, score_summary


def write_score(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "score.json"
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"total": 30, "exact_match": 0.5}, {"total": 30, "correct": 15, "accuracy": 0.5}),
        ({"total": 30, "score": 0.8}, {"total": 30, "correct": 24, "accuracy": 0.8}),
        ({"total": 30, "score": 8}, {"total": 30, "correct": 8, "accuracy": 8 / 30}),
        ({"total": 30, "score": "2/30"}, {"total": 30, "correct": 2, "accuracy": 2 / 30}),
    ],
)
def test_legacy_score_rates_are_not_truncated(
    tmp_path: Path, payload: object, expected: dict[str, object]
) -> None:
    assert score_summary(write_score(tmp_path, payload)) == expected


@pytest.mark.parametrize(
    "payload",
    [
        {"total": 30, "correct": 45},
        {"total": 30, "correct": 2.5},
        {"total": 30, "correct": True},
        {"total": 30, "correct": 15, "accuracy": 0.4},
        {"total": 30, "exact_match": 0.51},
        {"total": 30, "score": 1.7},
        "Score: 45/30\n",
    ],
)
def test_impossible_or_ambiguous_scores_are_rejected(tmp_path: Path, payload: object) -> None:
    assert score_summary(write_score(tmp_path, payload)) is None


def test_conflicting_text_fractions_are_not_guessed(tmp_path: Path) -> None:
    payload = "Processed 30/30 rows. Final score: 0/30.\n"
    assert score_summary(write_score(tmp_path, payload)) is None


def test_new_score_schema_is_explicit_and_consistent() -> None:
    assert parse_score_data(
        {"schema_version": 2, "total": 30, "correct": 6, "accuracy": 0.2, "diagnostic": "allowed"},
        allow_legacy=False,
    ) == {"total": 30, "correct": 6, "accuracy": 0.2}

    with pytest.raises(ScoreParseError, match="schema_version"):
        parse_score_data({"total": 30, "correct": 6}, allow_legacy=False)


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": "2", "total": 30, "correct": 6, "accuracy": 0.2},
        {"schema_version": 2, "total": 30.0, "correct": 6, "accuracy": 0.2},
        {"schema_version": 2, "total": 30, "correct": 6.0, "accuracy": 0.2},
        {"schema_version": 2, "total": 30, "correct": 6},
        {"schema_version": 2, "total": 30, "exact_match": 0.2, "accuracy": 0.2},
    ],
)
def test_new_score_schema_rejects_legacy_or_noncanonical_values(payload: dict[str, object]) -> None:
    with pytest.raises(ScoreParseError):
        parse_score_data(payload, allow_legacy=False)
