#!/usr/bin/env python3
"""Run a solver against immutable snapshots of an existing BenchBench sweep.

The source experiment is read-only.  Every extension claims a new run root,
copies benchmark packages into that root, and publishes typed solver evidence
only inside the extension overlay.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from benchbench_model_backends import ModelSpec, effective_effort, parse_model_spec, preflight_model, provider_binary, run_model, safe_name
from benchbench_results import candidate_title, extract_solver_predictions, score_summary, write_jsonl
from benchbench_run_state import (
    atomic_write_text,
    call_artifact_id,
    config_fingerprint,
    create_source_snapshot,
    publish_atomic,
    record_source_snapshot,
    require_new_run_root,
    score_temp_path,
    source_snapshot_digest,
    verify_source_snapshot,
)
from benchbench_sandbox import isolated_provider_path
from benchbench_schema import benchmark_package_digest, validate_answer_rows, validate_artifact_tree, validate_item_rows
from run_broad_three_model_sweep import (
    SAMPLE_COUNT,
    SANDBOX_PYTHON,
    SOLVER_PROMPT,
    _controller_scratch,
    _run_generated,
    freeze_call_evidence,
    normalized_score_record,
    reported_tokens,
    solver_result_dir,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE_RUN_ROOT = ROOT / "experiments" / "002_broad_sweep_20260515_220653"
DEFAULT_OUTPUT_ROOT = (
    ROOT
    / "experiments"
    / "extensions"
    / f"solver_extension_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
SOURCE_SNAPSHOT_FILES = (
    "benchbench_model_backends.py",
    "benchbench_results.py",
    "benchbench_run_state.py",
    "benchbench_sandbox.py",
    "benchbench_schema.py",
    "pyproject.toml",
    "requirements.txt",
    "run_broad_three_model_sweep.py",
    "run_existing_solver_extension.py",
    "uv.lock",
)


def extension_harness_digest() -> str:
    return source_snapshot_digest(ROOT, SOURCE_SNAPSHOT_FILES)


def charged_tokens(manifest: list[dict[str, Any]], zero_telemetry_reservation: int) -> int:
    """Charge unknown completed calls conservatively instead of treating them as free."""

    return sum(
        int(item.get("tokens_used") or 0) or zero_telemetry_reservation
        for item in manifest
    )


def extension_budget_allows_call(
    manifest: list[dict[str, Any]],
    max_total_tokens: int,
    zero_telemetry_reservation: int,
) -> bool:
    return charged_tokens(manifest, zero_telemetry_reservation) < max_total_tokens


def creator_name_from_candidate_dir(candidate_dir: Path) -> str:
    slug = candidate_dir.name.replace("candidate_created_by_", "")
    invocation = re.fullmatch(r"[^_]+__(.+)__effort_[a-z0-9_]+", slug)
    if invocation:
        slug = invocation.group(1)
    match = re.fullmatch(r"gpt_5_(\d+)(.*)", slug)
    if match:
        suffix = match.group(2).strip("_").replace("_", "-")
        return f"gpt-5.{match.group(1)}" + (f"-{suffix}" if suffix else "")
    match = re.fullmatch(r"gemini_3_(\d+)_(.+)", slug)
    if match:
        return f"gemini-3.{match.group(1)}-{match.group(2).replace('_', '-')}"
    return slug.replace("_", "-")


def source_candidate_dirs(source_run_root: Path, requested_creators: set[str] | None) -> list[tuple[str, Path]]:
    """Resolve historical flat candidates and new immutable-attempt candidates."""

    run_dir = source_run_root / "run"
    roots = sorted(path for path in run_dir.glob("candidate_created_by_*") if path.is_dir())
    wanted_slugs = {safe_name(name) for name in requested_creators or set()}
    resolved: list[tuple[str, Path]] = []
    for candidate_root in roots:
        root_slug = candidate_root.name.replace("candidate_created_by_", "")
        creator_name = creator_name_from_candidate_dir(candidate_root)
        if wanted_slugs and root_slug not in wanted_slugs and safe_name(creator_name) not in wanted_slugs:
            continue
        active = candidate_root / "active"
        artifact = active.resolve() if active.is_dir() else candidate_root.resolve()
        if not (artifact / "solver_bundle").is_dir():
            continue
        resolved.append((creator_name, artifact))
    return resolved


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_source_candidate_dirs(
    source_run_root: Path,
    requested_creators: list[str] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    """Verify a modern source run and resolve every requested creator exactly."""

    state_path = source_run_root / "run_state.json"
    manifest_path = source_run_root / "manifest.json"
    try:
        state_bytes = state_path.read_bytes()
        manifest_bytes = manifest_path.read_bytes()
        state = json.loads(state_bytes)
        manifest = json.loads(manifest_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("source run lacks readable state and manifest evidence") from exc
    config = state.get("config")
    source_snapshot = state.get("source_snapshot")
    if (
        state.get("schema_version") != 1
        or not isinstance(config, dict)
        or state.get("config_fingerprint") != config_fingerprint(config)
        or config.get("panel_policy") != "benchbench.frontier-four/2026-08-01"
        or not isinstance(config.get("creator_models"), list)
        or not isinstance(config.get("solver_models"), list)
        or not isinstance(source_snapshot, dict)
        or config.get("harness_digest") != source_snapshot.get("digest")
        or not isinstance(manifest, list)
        or not all(isinstance(item, dict) for item in manifest)
    ):
        raise ValueError("source run state, frontier policy, or manifest is not self-consistent")
    verify_source_snapshot(source_run_root, expected_digest=source_snapshot["digest"])

    candidates: list[dict[str, Any]] = []
    run_dir = source_run_root / "run"
    for creator_call_id in config["creator_models"]:
        candidate_root = run_dir / f"candidate_created_by_{creator_call_id}"
        active = candidate_root / "active"
        if not active.is_dir():
            continue
        artifact = active.resolve()
        attempt = artifact.parent
        validation_path = attempt / "controller_validation.v1.json"
        report_path = attempt / "controller_validation_report.txt"
        try:
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        digest = benchmark_package_digest(artifact)
        if (
            validation.get("schema_version") != "benchbench.validation/v1"
            or validation.get("valid") is not True
            or validation.get("candidate_digest") != digest
            or validation.get("deterministic") is not True
            or validation.get("frozen_package_match") is not True
            or validation.get("leak_match_count") != 0
            or not report_path.is_file()
            or validation.get("report_sha256") != _sha256_file(report_path)
        ):
            continue
        creator_records = [
            item
            for item in manifest
            if item.get("phase") in {"creator", "repair"}
            and item.get("artifact_id")
            and call_artifact_id(str(item["artifact_id"]), str(item.get("effort") or "high"))
            == creator_call_id
        ]
        if not creator_records:
            raise ValueError(f"source candidate lacks creator-call evidence: {creator_call_id}")
        creator_record = creator_records[-1]
        aliases = {
            creator_call_id,
            str(creator_record.get("model")),
            str(creator_record.get("requested_provider_model")),
        }
        candidates.append(
            {
                "creator_call_id": creator_call_id,
                "creator_model": str(creator_record.get("model")),
                "artifact": artifact,
                "candidate_digest": digest,
                "aliases": aliases,
                "validation_path": validation_path,
                "report_path": report_path,
                "validation_sha256": _sha256_file(validation_path),
                "report_sha256": _sha256_file(report_path),
            }
        )

    if requested_creators:
        selected: list[dict[str, Any]] = []
        for requested in requested_creators:
            matches = [candidate for candidate in candidates if requested in candidate["aliases"]]
            if len(matches) != 1:
                raise ValueError(
                    f"requested creator must resolve to exactly one validated source candidate: {requested}"
                )
            if matches[0] not in selected:
                selected.append(matches[0])
        candidates = selected
    if not candidates:
        raise ValueError("no validated source candidates matched the request")
    source_evidence = {
        "run_state_sha256": hashlib.sha256(state_bytes).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }
    return candidates, state, manifest, source_evidence


def require_missing_source_cell(
    source_manifest: list[dict[str, Any]],
    creator_model: str,
    source_artifact: Path,
    solver_call_id: str,
    *,
    allow_failed_retry: bool = False,
) -> None:
    attempts = [
        item
        for item in source_manifest
        if item.get("phase") == "solver"
        and item.get("creator_model") == creator_model
        and item.get("solver_artifact_id") == solver_call_id
    ]
    result_dir = solver_result_dir(source_artifact)
    published = (
        result_dir / f"predictions_solver_{solver_call_id}.jsonl"
    ).exists() or (result_dir / f"score_solver_{solver_call_id}.json").exists()
    retryable_states = {
        "backend_error",
        "invalid_output",
        "model_mismatch",
        "sandbox_error",
        "timeout",
    }
    retryable_attempts = bool(attempts) and all(
        item.get("cell_state") in retryable_states
        or (isinstance(item.get("returncode"), int) and item["returncode"] != 0)
        for item in attempts
    )
    if published or (attempts and not (allow_failed_retry and retryable_attempts)):
        raise ValueError(
            "source cell is neither missing nor an explicitly retryable failed cell: "
            f"creator={creator_model} solver={solver_call_id}"
        )


def freeze_source_evidence(
    output_root: Path,
    source_run_root: Path,
    source_candidates: list[dict[str, Any]],
    expected_source_evidence: dict[str, str],
) -> None:
    destination = output_root / "source_evidence"
    destination.mkdir()
    evidence: list[dict[str, str]] = []
    for source, target_name, expected_hash in (
        (
            source_run_root / "run_state.json",
            "run_state.json",
            expected_source_evidence["run_state_sha256"],
        ),
        (
            source_run_root / "manifest.json",
            "source_manifest.json",
            expected_source_evidence["manifest_sha256"],
        ),
    ):
        if _sha256_file(source) != expected_hash:
            raise ValueError(f"source run evidence changed before freezing: {source.name}")
        target = destination / target_name
        shutil.copy2(source, target)
        if _sha256_file(target) != expected_hash:
            raise ValueError(f"source run evidence changed while freezing: {source.name}")
        evidence.append({"path": target.relative_to(output_root).as_posix(), "sha256": _sha256_file(target)})
    for candidate in source_candidates:
        for source, expected_hash in (
            (candidate["validation_path"], candidate["validation_sha256"]),
            (candidate["report_path"], candidate["report_sha256"]),
        ):
            if _sha256_file(source) != expected_hash:
                raise ValueError(f"candidate validation evidence changed before freezing: {source}")
            target = destination / f"{safe_name(candidate['creator_model'])}__{source.name}"
            shutil.copy2(source, target)
            if _sha256_file(target) != expected_hash:
                raise ValueError(f"candidate validation evidence changed while freezing: {source}")
            evidence.append({"path": target.relative_to(output_root).as_posix(), "sha256": _sha256_file(target)})
    atomic_write_text(
        destination / "manifest.json",
        json.dumps({"schema_version": 1, "files": evidence}, indent=2, sort_keys=True) + "\n",
    )
    verify_frozen_source_evidence(output_root)


def verify_frozen_source_evidence(output_root: Path) -> dict[str, Any]:
    """Fail closed unless every file named by an overlay evidence index matches."""

    evidence_root = (output_root / "source_evidence").resolve()
    index_path = evidence_root / "manifest.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    files = index.get("files") if isinstance(index, dict) else None
    if index.get("schema_version") != 1 or not isinstance(files, list) or not files:
        raise ValueError("invalid frozen source-evidence index")
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise ValueError("invalid frozen source-evidence entry")
        relative = item["path"]
        if not isinstance(relative, str) or relative in seen:
            raise ValueError("duplicate or invalid frozen source-evidence path")
        seen.add(relative)
        unresolved = output_root / relative
        cursor = unresolved
        while cursor != output_root and cursor.is_relative_to(output_root):
            if cursor.is_symlink():
                raise ValueError(f"unsafe frozen source-evidence path: {relative}")
            cursor = cursor.parent
        target = unresolved.resolve()
        if (
            not target.is_relative_to(evidence_root)
            or target == index_path
            or not target.is_file()
            or target.stat().st_nlink != 1
        ):
            raise ValueError(f"unsafe frozen source-evidence path: {relative}")
        if _sha256_file(target) != item["sha256"]:
            raise ValueError(f"frozen source-evidence digest changed: {relative}")
    return index


def repair_frozen_source_evidence(output_root: Path, source_run_root: Path) -> dict[str, Any]:
    """Repair the v1 source-manifest/index name collision without model calls."""

    overlay_state = json.loads((output_root / "run_state.json").read_text(encoding="utf-8"))
    config = overlay_state.get("config") if isinstance(overlay_state, dict) else None
    expected_hash = config.get("source_manifest_sha256") if isinstance(config, dict) else None
    source_manifest = source_run_root / "manifest.json"
    if not isinstance(expected_hash, str) or _sha256_file(source_manifest) != expected_hash:
        raise ValueError("overlay source-manifest binding does not match the source run")
    evidence_root = output_root / "source_evidence"
    index_path = evidence_root / "manifest.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    files = index.get("files") if isinstance(index, dict) else None
    if index.get("schema_version") != 1 or not isinstance(files, list):
        raise ValueError("invalid frozen source-evidence index")
    old_path = "source_evidence/manifest.json"
    new_path = "source_evidence/source_manifest.json"
    matches = [item for item in files if item.get("path") in {old_path, new_path}]
    if len(matches) != 1 or matches[0].get("sha256") != expected_hash:
        raise ValueError("source-evidence index lacks one bound source manifest")
    target = evidence_root / "source_manifest.json"
    shutil.copy2(source_manifest, target)
    if _sha256_file(target) != expected_hash:
        raise ValueError("source manifest changed while repairing frozen evidence")
    matches[0]["path"] = new_path
    atomic_write_text(index_path, json.dumps(index, indent=2, sort_keys=True) + "\n")
    return verify_frozen_source_evidence(output_root)


def snapshot_candidate(
    source: Path,
    destination: Path,
    creator_model: str,
    *,
    expected_digest: str | None = None,
) -> Path:
    """Copy one benchmark package without importing prior solver evidence."""

    validate_artifact_tree(source)
    artifact = destination / f"candidate_created_by_{safe_name(creator_model)}" / "artifact"
    shutil.copytree(
        source,
        artifact,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "controller_validation_report.txt",
            "predictions_solver_*",
            "score_solver_*",
        ),
    )
    provenance = {
        "schema_version": 1,
        "source_artifact": str(source),
        "source_candidate_digest": benchmark_package_digest(source),
        "snapshot_candidate_digest": benchmark_package_digest(artifact),
    }
    if expected_digest is not None and (
        provenance["source_candidate_digest"] != expected_digest
        or provenance["snapshot_candidate_digest"] != expected_digest
    ):
        raise ValueError(f"candidate snapshot digest changed while copying: {creator_model}")
    (artifact.parent / "source.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact


def atomic_copy(source: Path, destination: Path) -> None:
    staged = score_temp_path(destination)
    try:
        shutil.copy2(source, staged)
        publish_atomic(staged, destination)
    finally:
        staged.unlink(missing_ok=True)


def run_one(
    output_run_dir: Path,
    candidate_dir: Path,
    creator_model: str,
    solver_spec: ModelSpec,
    effort: str,
    timeout: int,
) -> dict[str, Any]:
    solver_call_id = call_artifact_id(solver_spec.artifact_id, effort)
    slug = f"{safe_name(creator_model)}__solved_by__{solver_call_id}"
    raw_destination = output_run_dir / f"solver_{slug}.txt"
    result_dir = solver_result_dir(candidate_dir)
    predictions_path = result_dir / f"predictions_solver_{solver_call_id}.jsonl"
    score_path = result_dir / f"score_solver_{solver_call_id}.json"
    base: dict[str, Any] = {
        "phase": "solver_extension",
        "creator_model": creator_model,
        "solver_model": solver_spec.name,
        "solver_display_model": solver_spec.display_name,
        "solver_artifact_id": solver_call_id,
        "effort": effort,
        "benchmark": candidate_title(candidate_dir),
        "candidate_snapshot": str(candidate_dir),
        "prediction_rows": None,
        "predictions_path": str(predictions_path),
        "score_path": str(score_path),
        "score_summary": None,
        "score_returncode": None,
        "tokens_used": 0,
        "returncode": None,
    }
    if predictions_path.exists() or score_path.exists() or score_path.with_suffix(".raw.txt").exists():
        return {
            **base,
            "cell_state": "existing_attempt",
            "cell_error": "Refusing to overwrite controller-owned solver evidence",
        }
    with tempfile.TemporaryDirectory(prefix=f"benchbench-extension-{slug}-") as temporary:
        temp_root = Path(temporary)
        solver_dir = temp_root / "solver_bundle"
        shutil.copytree(candidate_dir / "solver_bundle", solver_dir)
        try:
            item_rows = validate_item_rows(
                solver_dir / "items_private_sample.jsonl",
                count=SAMPLE_COUNT,
            )
        except Exception as exc:  # noqa: BLE001
            return {**base, "cell_state": "invalid_bundle", "cell_error": str(exc), "returncode": None, "tokens_used": 0}

        item_ids = [row["id"] for row in item_rows]
        raw_temp = temp_root / "model_output.txt"
        try:
            with isolated_provider_path(provider_binary(solver_spec), temp_root):
                result = run_model(
                    solver_spec,
                    SOLVER_PROMPT.format(
                        agent_label=solver_spec.agent_label,
                        solver_bundle_path=solver_dir,
                    ),
                    raw_temp,
                    solver_dir,
                    effort,
                    timeout,
                )
        except Exception as exc:  # fail closed and retain a typed cell
            result = {
                "model": solver_spec.name,
                "display_model": solver_spec.display_name,
                "provider": solver_spec.provider,
                "artifact_id": solver_spec.artifact_id,
                "effort": effort,
                "returncode": -124 if isinstance(exc, subprocess.TimeoutExpired) else 70,
                "tokens_used": 0,
                "call_state": "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "sandbox_error",
                "call_error": str(exc),
                "out_path": str(raw_temp),
            }

        freeze_call_evidence(result, output_run_dir / "call_evidence" / raw_destination.stem)
        if raw_temp.exists():
            atomic_copy(raw_temp, raw_destination)
        result = {**base, **result}
        result["out_path"] = str(raw_destination)
        if result.get("returncode") != 0:
            result["cell_state"] = "timeout" if result.get("returncode") == -124 else "backend_error"
            return result
        if result.get("model_mismatch"):
            result["cell_state"] = "model_mismatch"
            return result

        try:
            predictions, extraction_source = extract_solver_predictions(raw_temp, solver_dir, item_ids)
            prediction_temp = temp_root / "predictions.jsonl"
            write_jsonl(prediction_temp, predictions)
            validate_answer_rows(
                prediction_temp,
                expected_ids=set(item_ids),
                count=SAMPLE_COUNT,
            )
        except Exception as exc:  # noqa: BLE001
            return {**result, "cell_state": "invalid_output", "cell_error": str(exc), "prediction_rows": None}

        with _controller_scratch(candidate_dir) as scoring_name:
            scoring_dir = Path(scoring_name) / "candidate"
            shutil.copy2(prediction_temp, scoring_dir / "predictions.jsonl")
            completed = _run_generated(
                [
                    SANDBOX_PYTHON,
                    "scorer.py",
                    "--gold",
                    "gold_private_sample.jsonl",
                    "--predictions",
                    "predictions.jsonl",
                    "--out",
                    "score.tmp.json",
                ],
                scoring_dir,
                [],
                420,
            )
            score_temp = scoring_dir / "score.tmp.json"
            if completed is None or completed.returncode != 0 or not score_temp.exists():
                return {
                    **result,
                    "cell_state": "scorer_error",
                    "score_returncode": None if completed is None else completed.returncode,
                }
            try:
                summary = score_summary(score_temp, allow_legacy=False)
                if (
                    not summary
                    or summary.get("total") != SAMPLE_COUNT
                    or not isinstance(summary.get("correct"), int)
                    or not 0 <= summary["correct"] <= SAMPLE_COUNT
                ):
                    raise ValueError("scorer did not emit a complete bounded score")
            except Exception as exc:  # noqa: BLE001
                return {
                    **result,
                    "cell_state": "invalid_score",
                    "cell_error": str(exc),
                    "score_returncode": completed.returncode,
                }

            normalized_temp = temp_root / "normalized_score.json"
            normalized = normalized_score_record(
                summary,
                candidate_dir,
                prediction_temp,
                solver_call_id,
            )
            normalized_temp.write_text(
                json.dumps(normalized, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            atomic_copy(prediction_temp, predictions_path)
            atomic_copy(normalized_temp, score_path)
            result.update(
                {
                    "cell_state": "success",
                    "prediction_rows": len(predictions),
                    "prediction_source": str(predictions_path),
                    "prediction_extraction_source": (
                        "solver_bundle_file" if Path(extraction_source) != raw_temp else "provider_output"
                    ),
                    "score_summary": summary,
                    "score_returncode": completed.returncode,
                    "candidate_digest": normalized["candidate_digest"],
                    "gold_digest": normalized["gold_digest"],
                    "prediction_digest": normalized["prediction_digest"],
                }
            )
            return result


def write_outputs(
    output_root: Path,
    source_run_root: Path,
    solver_spec: ModelSpec,
    manifest: list[dict[str, Any]],
) -> Path:
    manifest_path = output_root / "manifest.json"
    atomic_write_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    lines = [
        f"# Solver Extension: {solver_spec.display_name}",
        "",
        f"Source run (read-only): `{source_run_root}`",
        f"Extension overlay: `{output_root}`",
        f"Solver spec: `{solver_spec.name}`",
        f"Provider: `{solver_spec.provider}`",
        "",
        "| creator | benchmark | state | rows | score | tokens | returncode | actual model |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for item in manifest:
        score = item.get("score_summary") or {}
        score_text = f"{score.get('correct')}/{score.get('total')}" if score else "NA"
        actual = item.get("antigravity_actual_label") or item.get("solver_display_model") or item.get("solver_model")
        lines.append(
            f"| {item.get('creator_model')} | {item.get('benchmark')} | {item.get('cell_state')} | "
            f"{item.get('prediction_rows') or 'NA'} | {score_text} | {item.get('tokens_used', 0)} | "
            f"{item.get('returncode')} | {actual} |"
        )
    lines.extend(["", f"Total reported tokens: `{reported_tokens(manifest)}`", ""])
    summary_path = output_root / "summary.md"
    atomic_write_text(summary_path, "\n".join(lines))
    return summary_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a read-only solver extension overlay for an existing sweep.")
    parser.add_argument("--source-run-root", "--run-root", dest="source_run_root", type=Path, default=DEFAULT_SOURCE_RUN_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--solver", default="gpt-5.6-sol", help="Provider-qualified model spec; unprefixed values use Codex.")
    parser.add_argument("--creator-models", nargs="*", default=None, help="Optional source creator names to include.")
    parser.add_argument("--effort", default="high")
    parser.add_argument("--timeout-seconds", type=int, default=1500)
    parser.add_argument("--preflight-only", action="store_true", help="Check the provider CLI without model inference or filesystem writes.")
    parser.add_argument(
        "--retry-failed-source-cells",
        action="store_true",
        help="Also permit immutable-overlay retries for source cells already typed as failed.",
    )
    parser.add_argument(
        "--max-total-tokens",
        type=int,
        default=int(os.getenv("BENCHBENCH_MAX_TOTAL_TOKENS", "0")),
        help="Required live-run ceiling on reported provider tokens.",
    )
    parser.add_argument(
        "--allow-unmetered-cost",
        action="store_true",
        help="Acknowledge a provider without harness-enforced dollar telemetry.",
    )
    parser.add_argument(
        "--allow-dispatch-ceiling-overshoot",
        action="store_true",
        help="Acknowledge that one in-flight provider call can overshoot the dispatch ceiling.",
    )
    parser.add_argument(
        "--zero-telemetry-reservation",
        type=int,
        default=5_000_000,
        help="Conservative token charge for a completed call that reports zero telemetry.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_run_root = args.source_run_root if args.source_run_root.is_absolute() else ROOT / args.source_run_root
    output_root = args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    creators = list(args.creator_models) if args.creator_models else None
    try:
        source_candidates, source_state, source_manifest, source_evidence = verified_source_candidate_dirs(
            source_run_root,
            creators,
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid source run: {exc}") from exc
    for candidate in source_candidates:
        source = candidate["artifact"]
        try:
            validate_artifact_tree(source)
        except ValueError as exc:
            raise SystemExit(f"Unsafe source benchmark package {source}: {exc}") from exc

    solver_spec = parse_model_spec(args.solver)
    solver_effort = effective_effort(solver_spec, args.effort)
    solver_call_id = call_artifact_id(solver_spec.artifact_id, solver_effort)
    declared_solvers = source_state["config"]["solver_models"]
    if solver_call_id not in declared_solvers:
        raise SystemExit(
            f"Extension solver is outside the source frontier-four panel: {solver_call_id}"
        )
    try:
        for candidate in source_candidates:
            require_missing_source_cell(
                source_manifest,
                candidate["creator_model"],
                candidate["artifact"],
                solver_call_id,
                allow_failed_retry=args.retry_failed_source_cells,
            )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    preflight = preflight_model(solver_spec, ROOT)
    print(json.dumps({"preflight": preflight}, indent=2, sort_keys=True), flush=True)
    preflight_failed = (
        preflight.get("state") != "binary_ready"
        or preflight.get("model_available") is False
    )
    if args.preflight_only:
        if preflight_failed:
            raise SystemExit("Provider preflight failed")
        return
    if solver_spec.provider not in {"codex", "antigravity"}:
        raise SystemExit("Live extensions require an audited provider credential boundary")
    if preflight_failed:
        raise SystemExit("Provider preflight failed; refusing to make solver calls")
    if args.max_total_tokens <= 0:
        raise SystemExit("Live extensions require --max-total-tokens (or BENCHBENCH_MAX_TOTAL_TOKENS)")
    if not args.allow_dispatch_ceiling_overshoot:
        raise SystemExit("Pass --allow-dispatch-ceiling-overshoot after approving in-flight overshoot")
    if args.zero_telemetry_reservation <= 0:
        raise SystemExit("--zero-telemetry-reservation must be a positive integer")
    if solver_spec.provider != "claude" and not args.allow_unmetered_cost:
        raise SystemExit("This provider has no harness-enforced dollar cap; pass --allow-unmetered-cost after reviewing the token ceiling")

    run_config = {
        "schema_version": 1,
        "source_run_root": str(source_run_root.resolve()),
        "source_candidates": [
            {
                "creator_model": candidate["creator_model"],
                "creator_call_id": candidate["creator_call_id"],
                "artifact": str(candidate["artifact"]),
                "candidate_digest": candidate["candidate_digest"],
                "validation_sha256": candidate["validation_sha256"],
                "validation_report_sha256": candidate["report_sha256"],
            }
            for candidate in source_candidates
        ],
        "solver": solver_call_id,
        "timeout_seconds": args.timeout_seconds,
        "max_total_tokens": args.max_total_tokens,
        "zero_telemetry_reservation": args.zero_telemetry_reservation,
        "dispatch_ceiling_overshoot_acknowledged": args.allow_dispatch_ceiling_overshoot,
        "unmetered_cost_acknowledged": args.allow_unmetered_cost,
        "harness_digest": extension_harness_digest(),
        "source_run_state_sha256": source_evidence["run_state_sha256"],
        "source_manifest_sha256": source_evidence["manifest_sha256"],
        "retry_failed_source_cells": args.retry_failed_source_cells,
        "source_snapshot_digest": source_state["source_snapshot"]["digest"],
        "provider_preflight": [preflight],
    }
    try:
        require_new_run_root(output_root, run_config)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    try:
        snapshot = create_source_snapshot(ROOT, output_root, SOURCE_SNAPSHOT_FILES)
        if snapshot["digest"] != run_config["harness_digest"]:
            raise RuntimeError("extension controller source changed during initialization")
        record_source_snapshot(output_root, snapshot)
        freeze_source_evidence(
            output_root,
            source_run_root,
            source_candidates,
            source_evidence,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Failed to freeze extension controller source snapshot: {exc}") from exc
    output_run_dir = output_root / "run"
    output_run_dir.mkdir()

    manifest: list[dict[str, Any]] = []
    for candidate in source_candidates:
        creator_model = candidate["creator_model"]
        source = candidate["artifact"]
        if not extension_budget_allows_call(
            manifest,
            args.max_total_tokens,
            args.zero_telemetry_reservation,
        ):
            print("[budget:stop] charged token ceiling reached before next extension call", flush=True)
            break
        snapshot = snapshot_candidate(
            source,
            output_run_dir,
            creator_model,
            expected_digest=candidate["candidate_digest"],
        )
        print(f"[solver-extension:start] creator={creator_model} solver={solver_spec.name}", flush=True)
        result = run_one(
            output_run_dir,
            snapshot,
            creator_model,
            solver_spec,
            solver_effort,
            args.timeout_seconds,
        )
        manifest.append(result)
        write_outputs(output_root, source_run_root, solver_spec, manifest)
        print(
            f"[solver-extension:done] creator={creator_model} state={result.get('cell_state')} "
            f"rows={result.get('prediction_rows')} score={result.get('score_summary')} "
            f"tokens={result.get('tokens_used', 0)} rc={result.get('returncode')}",
            flush=True,
        )

    print(write_outputs(output_root, source_run_root, solver_spec, manifest), flush=True)


if __name__ == "__main__":
    main()
