"""Strict contracts used by the controller, independent of creator code."""

from __future__ import annotations

import hashlib
import json
import csv
import re
import stat
from pathlib import Path
from typing import Any


def validate_artifact_tree(
    root: Path,
    *,
    max_files: int = 20_000,
    max_bytes: int = 512 * 1024 * 1024,
) -> dict[str, int]:
    """Reject links, special files, and unbounded model-produced trees."""

    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"artifact root is not a real directory: {root}")
    file_count = 0
    total_bytes = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"artifact contains a symbolic link: {path.relative_to(root)}")
        file_stat = path.stat(follow_symlinks=False)
        mode = file_stat.st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(f"artifact contains a special file: {path.relative_to(root)}")
        if file_stat.st_nlink != 1:
            raise ValueError(f"artifact contains a hard-linked file: {path.relative_to(root)}")
        file_count += 1
        total_bytes += file_stat.st_size
        if file_count > max_files:
            raise ValueError(f"artifact exceeds file limit: {file_count} > {max_files}")
        if total_bytes > max_bytes:
            raise ValueError(f"artifact exceeds byte limit: {total_bytes} > {max_bytes}")
    return {"file_count": file_count, "total_bytes": total_bytes}


def read_jsonl_strict(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            raise ValueError(f"{path}: blank JSONL line {line_number}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: invalid JSON at line {line_number}: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}: line {line_number} is not an object")
        rows.append(value)
    return rows


def validate_answer_rows(path: Path, *, expected_ids: set[str] | None = None, count: int | None = None) -> list[dict[str, Any]]:
    rows = read_jsonl_strict(path)
    if count is not None and len(rows) != count:
        raise ValueError(f"{path}: expected {count} rows, found {len(rows)}")
    ids: list[str] = []
    for index, row in enumerate(rows, start=1):
        if set(row) != {"id", "answer"}:
            raise ValueError(f"{path}: row {index} must contain exactly id and answer")
        if not isinstance(row["id"], str) or not row["id"]:
            raise ValueError(f"{path}: row {index} has invalid id")
        # BenchBench answer keys may be strings, numbers, booleans, arrays, or
        # objects.  JSONL parsing above already guarantees serializability;
        # exact-key and id contracts are the controller's invariant.
        ids.append(row["id"])
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate ids")
    if expected_ids is not None and set(ids) != expected_ids:
        raise ValueError(f"{path}: ids do not exactly match declared item ids")
    return rows


def validate_item_rows(path: Path, *, count: int, expected_ids: set[str] | None = None) -> list[dict[str, Any]]:
    rows = read_jsonl_strict(path)
    if len(rows) != count:
        raise ValueError(f"{path}: expected {count} rows, found {len(rows)}")
    ids: list[str] = []
    for index, row in enumerate(rows, start=1):
        if "id" not in row or not isinstance(row["id"], str) or not row["id"]:
            raise ValueError(f"{path}: row {index} has no valid id")
        ids.append(row["id"])
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate ids")
    if expected_ids is not None and set(ids) != expected_ids:
        raise ValueError(f"{path}: ids do not exactly match gold")
    return rows


def tree_digest(root: Path) -> str:
    """Hash a generated tree deterministically, ignoring Python bytecode."""

    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def benchmark_package_digest(root: Path) -> str:
    """Hash the complete immutable creator artifact.

    Controller predictions, scores, and validation evidence live outside this
    artifact. Filename-based exclusions would let creator-authored files evade
    the digest, so the package hash intentionally covers every regular file.
    """

    return tree_digest(root)


def generated_payload_digest(root: Path) -> str:
    """Hash exactly the generator-owned gold and solver-bundle payload."""

    digest = hashlib.sha256()
    gold = root / "gold_private_sample.jsonl"
    paths = [gold] if gold.is_file() else []
    bundle = root / "solver_bundle"
    if bundle.is_dir():
        paths.extend(
            sorted(
                path
                for path in bundle.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
            )
        )
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def bundle_leaks(bundle: Path, gold_rows: list[dict[str, Any]]) -> list[str]:
    """Catch solution-bearing files and answer mappings in public artifacts."""

    prohibited = ("gold_private", "private_audit", "generator.py", "verifier.py", "scorer.py", "answer_key")
    prohibited_stems = {
        "answers",
        "gold",
        "gold_answers",
        "labels",
        "reference_answers",
        "solution",
        "solution_key",
        "solutions",
    }
    text_suffixes = {
        ".csv", ".html", ".json", ".jsonl", ".md", ".text", ".tsv", ".txt", ".yaml", ".yml",
    }

    def canonical(value: Any) -> str:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))

    gold_by_id = {str(row["id"]): canonical(row["answer"]) for row in gold_rows}
    raw_answer_by_id = {str(row["id"]): row["answer"] for row in gold_rows}
    leaks: list[str] = []

    def scan_json(value: Any, relative: str, location: str = "$") -> None:
        if isinstance(value, dict):
            row_id = value.get("id")
            if isinstance(row_id, (str, int)):
                answer = gold_by_id.get(str(row_id))
                if answer is not None:
                    for key, nested in value.items():
                        if key != "id" and canonical(nested) == answer:
                            leaks.append(f"answer-leak:{relative}:{row_id}:{location}.{key}")
            for key, nested in value.items():
                mapped_answer = gold_by_id.get(str(key))
                if mapped_answer is not None and canonical(nested) == mapped_answer:
                    leaks.append(f"answer-map:{relative}:{key}:{location}")
                scan_json(nested, relative, f"{location}.{key}")
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                scan_json(nested, relative, f"{location}[{index}]")

    def scan_delimited(text: str, relative: str, delimiter: str) -> None:
        try:
            rows = csv.DictReader(text.splitlines(), delimiter=delimiter)
            for row in rows:
                row_id = row.get("id") or row.get("ID")
                answer = gold_by_id.get(str(row_id)) if row_id is not None else None
                if answer is None:
                    continue
                for key, value in row.items():
                    if key not in {"id", "ID"} and canonical(value) == answer:
                        leaks.append(f"answer-leak:{relative}:{row_id}:{key}")
        except (csv.Error, TypeError):
            return

    def scan_text_mapping(text: str, relative: str) -> None:
        for row_id, raw_answer in raw_answer_by_id.items():
            if isinstance(raw_answer, (dict, list)):
                rendered = canonical(raw_answer)
            elif isinstance(raw_answer, str):
                rendered = raw_answer
            else:
                rendered = json.dumps(raw_answer, ensure_ascii=True)
            pattern = (
                rf"(?m)^\s*{re.escape(row_id)}\s*(?:,|\t|:|=|->)\s*"
                rf"{re.escape(rendered)}\s*(?:[,;#]|$)"
            )
            if re.search(pattern, text):
                leaks.append(f"answer-text-map:{relative}:{row_id}")
            labelled_record = (
                rf"(?ims)(?:^|\n)\s*(?:[-*]\s*)?(?:id|item(?:_id)?)\s*[:=]\s*"
                rf"{re.escape(row_id)}\s*$"
                rf"(?:\n[^\n]*){{0,4}}?\n\s*(?:answer|solution|label)\s*[:=]\s*"
                rf"{re.escape(rendered)}\s*$"
            )
            if re.search(labelled_record, text):
                leaks.append(f"answer-labelled-record:{relative}:{row_id}")

    for path in bundle.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(bundle).as_posix()
        lower_name = relative.lower()
        if any(term in lower_name for term in prohibited) or path.stem.lower() in prohibited_stems:
            leaks.append(f"prohibited-path:{relative}")
            continue
        suffix = path.suffix.lower()
        if suffix not in text_suffixes or path.stat().st_size > 8_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if suffix == ".jsonl":
            for index, line in enumerate(text.splitlines()):
                if not line.strip():
                    continue
                try:
                    scan_json(json.loads(line), relative, f"$[{index}]")
                except json.JSONDecodeError:
                    pass
        elif suffix == ".json":
            try:
                scan_json(json.loads(text), relative)
            except json.JSONDecodeError:
                pass
        if suffix in {".csv", ".tsv"}:
            scan_delimited(text, relative, "\t" if suffix == ".tsv" else ",")
        scan_text_mapping(text, relative)
    return sorted(set(leaks))
