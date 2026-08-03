#!/usr/bin/env python3
"""Shared result parsing helpers for BenchBench runners."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


SCORE_FRACTION_RE = re.compile(r"(?<![\d.])(\d+)\s*/\s*(\d+)(?!\d)")


class ScoreParseError(ValueError):
    """Raised when a scorer report cannot be normalized without guessing."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")


def _as_nonnegative_int(value: Any, field: str, *, strict_type: bool = False) -> int:
    if strict_type and (isinstance(value, bool) or not isinstance(value, int)):
        raise ScoreParseError(f"{field} must be an integer")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScoreParseError(f"{field} must be an integer")
    if not math.isfinite(float(value)) or int(value) != value or int(value) < 0:
        raise ScoreParseError(f"{field} must be a non-negative integer")
    return int(value)


def _as_accuracy(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScoreParseError("accuracy must be numeric")
    accuracy = float(value)
    if not math.isfinite(accuracy) or not 0.0 <= accuracy <= 1.0:
        raise ScoreParseError("accuracy must be between 0 and 1")
    return accuracy


def _validated_score(
    total: Any,
    correct: Any,
    accuracy: Any | None = None,
    *,
    accuracy_tolerance: float = 1e-9,
    strict_integer_types: bool = False,
) -> dict[str, Any]:
    total_int = _as_nonnegative_int(total, "total", strict_type=strict_integer_types)
    correct_int = _as_nonnegative_int(correct, "correct", strict_type=strict_integer_types)
    if correct_int > total_int:
        raise ScoreParseError("correct cannot exceed total")
    expected = 0.0 if total_int == 0 else correct_int / total_int
    if accuracy is not None:
        reported = _as_accuracy(accuracy)
        if not math.isclose(reported, expected, rel_tol=1e-9, abs_tol=accuracy_tolerance):
            raise ScoreParseError(
                f"accuracy {reported!r} is inconsistent with {correct_int}/{total_int}"
            )
    return {"total": total_int, "correct": correct_int, "accuracy": expected}


def _score_from_fraction(text: str) -> dict[str, Any] | None:
    matches = SCORE_FRACTION_RE.findall(text)
    if not matches:
        return None
    fractions = {(int(correct), int(total)) for correct, total in matches}
    if len(fractions) != 1:
        raise ScoreParseError("score text contains conflicting count fractions")
    correct, total = fractions.pop()
    return _validated_score(total, correct)


def _count_from_rate(value: Any, total: Any, field: str) -> int:
    rate = _as_accuracy(value)
    total_int = _as_nonnegative_int(total, "total")
    count = rate * total_int
    rounded = round(count)
    if not math.isclose(count, rounded, rel_tol=1e-9, abs_tol=1e-9):
        raise ScoreParseError(f"{field} rate does not map to an integral count")
    return int(rounded)


def parse_score_data(data: Any, *, allow_legacy: bool = True) -> dict[str, Any]:
    """Normalize one score object, rejecting ambiguous or impossible values.

    New score reports should use ``schema_version``, ``total``, ``correct`` and
    ``accuracy``.  ``allow_legacy`` exists only for preserved historical
    generated scorers; it accepts their known field names but never truncates
    floats or accepts inconsistent totals.
    """

    if not isinstance(data, dict):
        raise ScoreParseError("score report must be a JSON object")

    if not allow_legacy and data.get("schema_version") != 2:
        raise ScoreParseError("new score reports require schema_version 2")

    total = data.get("total")
    correct = data.get("correct")
    accuracy = data.get("accuracy")

    if not allow_legacy and accuracy is None:
        raise ScoreParseError("new score reports require accuracy")

    if allow_legacy:
        if total is None:
            total = data.get("n_items", data.get("total_gold", data.get("total_items")))
        if correct is None:
            for key in ("n_correct", "correct_predictions"):
                if data.get(key) is not None:
                    correct = data[key]
                    break

        metrics = data.get("metrics")
        if isinstance(metrics, dict) and (total is None or correct is None):
            for total_key, correct_key in (
                ("total_items", "correct_items"),
                ("total_tenants_evaluated", "correct_tenants"),
            ):
                if metrics.get(total_key) is not None and metrics.get(correct_key) is not None:
                    total = metrics[total_key]
                    correct = metrics[correct_key]
                    if accuracy is None:
                        accuracy = metrics.get("accuracy")
                    break

        details = data.get("details", data.get("per_item", data.get("results")))
        if (total is None or correct is None) and isinstance(details, list):
            if all(isinstance(row, dict) and isinstance(row.get("correct"), bool) for row in details):
                total = len(details)
                correct = sum(1 for row in details if row["correct"])
            elif all(isinstance(row, dict) and isinstance(row.get("item_correct"), bool) for row in details):
                total = len(details)
                correct = sum(1 for row in details if row["item_correct"])
            else:
                raise ScoreParseError("per-item details must contain boolean correct fields")

        exact_match = data.get("exact_match")
        if correct is None and exact_match is not None:
            if total is None:
                raise ScoreParseError("exact_match requires total")
            if isinstance(exact_match, (int, float)) and not isinstance(exact_match, bool):
                if 0 <= float(exact_match) <= 1:
                    correct = _count_from_rate(exact_match, total, "exact_match")
                else:
                    correct = exact_match
            else:
                raise ScoreParseError("exact_match must be numeric")

        score = data.get("score")
        if correct is None and isinstance(score, str):
            parsed = _score_from_fraction(score)
            if parsed is None:
                raise ScoreParseError("string score must contain an exact count fraction")
            if total is not None and _as_nonnegative_int(total, "total") != parsed["total"]:
                raise ScoreParseError("score fraction total conflicts with total field")
            total, correct = parsed["total"], parsed["correct"]
        elif correct is None and isinstance(score, (int, float)) and not isinstance(score, bool):
            if total is None:
                raise ScoreParseError("numeric score requires total")
            if isinstance(score, float) and not score.is_integer():
                if 0 <= score <= 1:
                    correct = _count_from_rate(score, total, "score")
                else:
                    raise ScoreParseError("fractional numeric score is neither a rate nor a count")
            else:
                correct = score

    if total is None or correct is None:
        raise ScoreParseError("score report is missing total or correct")
    return _validated_score(
        total,
        correct,
        accuracy,
        accuracy_tolerance=5e-5 if allow_legacy else 1e-9,
        strict_integer_types=not allow_legacy,
    )


def score_summary(path: Path, *, allow_legacy: bool = True) -> dict[str, Any] | None:
    """Parse a score report without converting malformed data into a score."""

    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(text)
    except Exception:
        try:
            return _score_from_fraction(text) if allow_legacy else None
        except ScoreParseError:
            return None
    try:
        return parse_score_data(data, allow_legacy=allow_legacy)
    except ScoreParseError:
        return None


def extract_predictions(raw: str, item_ids: list[str]) -> list[dict[str, Any]]:
    """Extract strict BenchBench prediction rows from noisy model output."""

    wanted = set(item_ids)
    by_id: dict[str, Any] = {}
    for line in raw.splitlines():
        stripped = line.strip().strip(",")
        if not (stripped.startswith("{") and stripped.endswith("}")):
            continue
        try:
            obj = json.loads(stripped)
        except Exception:
            continue
        if not isinstance(obj, dict) or set(obj) != {"id", "answer"}:
            continue
        row_id = str(obj.get("id"))
        if row_id in wanted:
            by_id[row_id] = obj["answer"]
    return [{"id": item_id, "answer": by_id[item_id]} for item_id in item_ids if item_id in by_id]


def extract_solver_predictions(raw_out_path: Path, solver_dir: Path, item_ids: list[str]) -> tuple[list[dict[str, Any]], str]:
    """Prefer a solver-written predictions.jsonl when it has more usable rows."""

    raw = raw_out_path.read_text(encoding="utf-8", errors="replace") if raw_out_path.exists() else ""
    stdout_predictions = extract_predictions(raw, item_ids)

    file_path = solver_dir / "predictions.jsonl"
    file_predictions: list[dict[str, Any]] = []
    if file_path.exists():
        file_predictions = extract_predictions(file_path.read_text(encoding="utf-8", errors="replace"), item_ids)

    if len(file_predictions) > len(stdout_predictions):
        return file_predictions, str(file_path)
    if stdout_predictions:
        return stdout_predictions, str(raw_out_path)
    return [], str(raw_out_path)


def candidate_title(candidate_dir: Path) -> str:
    spec = candidate_dir / "benchmark_spec.json"
    if spec.exists():
        try:
            data = json.loads(spec.read_text(encoding="utf-8"))
        except Exception:
            data = None
        if isinstance(data, dict):
            for key in ["benchmark_name", "name", "title", "benchmark_id", "benchmark"]:
                if data.get(key):
                    return str(data[key])

    readme = candidate_dir / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("#"):
                return line.lstrip("#").strip()
    return candidate_dir.name
