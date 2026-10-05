#!/usr/bin/env python3
"""Prepare the current frontier-panel evidence bundle for public release.

Raw provider transcripts stay local and are ignored by Git. This script makes
the retained manifests portable, replaces raw-transcript path fields with an
explicit sentinel, and then rebinds every public digest that depends on the
sanitized files.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchbench_run_state import config_fingerprint
from benchbench_schema import benchmark_package_digest

EXPERIMENT_ROOTS = (
    ROOT / "experiments/009_four_model_panel_20260801_103006",
    ROOT / "experiments/010_four_model_panel_20260801_120442",
    ROOT / "experiments/011_gemini_provider_recovery_20260802",
    ROOT / "experiments/012_gemini_creator_recovery_20260802",
    *(ROOT / "experiments").glob("013_*"),
    *(ROOT / "experiments").glob("014_*"),
    *(ROOT / "experiments").glob("015_*"),
    *(ROOT / "experiments/extensions").glob("004_*"),
    *(ROOT / "experiments/extensions").glob("010_*"),
    *(ROOT / "experiments/extensions").glob("013_*"),
    *(ROOT / "experiments/extensions").glob("014_*"),
    *(ROOT / "experiments/extensions").glob("015_*"),
)
RAW_PATH_KEYS = {
    "antigravity_log_path",
    "out_path",
    "prompt_path",
    "stderr_path",
    "stdout_path",
}
RAW_SENTINEL = "private_raw_evidence_not_published"
RAW_RESULT_RE = re.compile(r"^(creator|repair|solver)_.+\.txt$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def is_raw_evidence(path: Path) -> bool:
    return "call_evidence" in path.parts or (
        path.parent.name == "run" and RAW_RESULT_RE.fullmatch(path.name) is not None
    )


def scrub_text(text: str) -> str:
    repo = ROOT.as_posix()
    home = Path.home().as_posix()
    text = text.replace(f"{repo}/", "./").replace(repo, ".")
    text = text.replace(f"{home}/", "<local-home>/").replace(home, "<local-home>")
    text = re.sub(r"/Users/[^/\s\"']+", "<local-home>", text)
    return text.replace("/private/tmp/", "<temporary-root>/")


def redact_raw_path_fields(value: Any) -> Any:
    if isinstance(value, list):
        return [redact_raw_path_fields(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: RAW_SENTINEL if key in RAW_PATH_KEYS and isinstance(item, str) else redact_raw_path_fields(item)
        for key, item in value.items()
    }


def sanitize_public_files() -> None:
    for root in EXPERIMENT_ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path.is_symlink() or is_raw_evidence(path):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            scrubbed = scrub_text(text)
            if path.name in {"manifest.json", "run_state.json", "source_manifest.json"}:
                scrubbed = json.dumps(
                    redact_raw_path_fields(json.loads(scrubbed)),
                    indent=2,
                    sort_keys=False,
                ) + "\n"
            if scrubbed != text:
                path.write_text(scrubbed, encoding="utf-8")


def rebind_controller_validation(path: Path) -> None:
    """Rebind a validation record after path-only public sanitization."""

    artifact = path.parent / "artifact"
    report = path.parent / "controller_validation_report.txt"
    if not artifact.is_dir() or not report.is_file():
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema_version") != "benchbench.validation/v1":
        return
    record["candidate_digest"] = benchmark_package_digest(artifact)
    record["report_sha256"] = sha256(report)
    write_json(path, record)


def rebind_controller_validations() -> None:
    for root in EXPERIMENT_ROOTS:
        for path in root.glob("run/candidate_created_by_*/attempt_*/controller_validation.v1.json"):
            rebind_controller_validation(path)


def _public_path(value: Any) -> Path | None:
    if not isinstance(value, str) or value == RAW_SENTINEL or value.startswith("<"):
        return None
    relative = value[2:] if value.startswith("./") else value
    path = Path(relative)
    return path if path.is_absolute() else ROOT / path


def _record_candidate_artifact(record: dict[str, Any]) -> Path | None:
    candidate = _public_path(record.get("candidate_snapshot"))
    if candidate is not None and candidate.is_dir():
        return candidate
    validation = _public_path(record.get("validation_report_path"))
    if validation is not None and validation.name == "controller_validation.v1.json":
        artifact = validation.parent / "artifact"
        if artifact.is_dir():
            return artifact
    return None


def rebind_manifest_candidate_digests() -> None:
    """Keep manifest and normalized-score package bindings self-consistent."""

    for root in EXPERIMENT_ROOTS:
        manifest_path = root / "manifest.json"
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, list):
            continue
        changed = False
        for record in manifest:
            if not isinstance(record, dict):
                continue
            artifact = _record_candidate_artifact(record)
            if artifact is None:
                continue
            digest = benchmark_package_digest(artifact)
            if "candidate_digest" in record and record.get("candidate_digest") != digest:
                record["candidate_digest"] = digest
                changed = True
            score_path = _public_path(record.get("score_path"))
            if score_path is not None and score_path.is_file():
                score = json.loads(score_path.read_text(encoding="utf-8"))
                if isinstance(score, dict) and "candidate_digest" in score and score.get("candidate_digest") != digest:
                    score["candidate_digest"] = digest
                    write_json(score_path, score)
        if changed:
            write_json(manifest_path, manifest)


def rebind_run_state_fingerprint(path: Path) -> None:
    state = json.loads(path.read_text(encoding="utf-8"))
    config = state.get("config") if isinstance(state, dict) else None
    if state.get("schema_version") != 1 or not isinstance(config, dict):
        return
    state["config_fingerprint"] = config_fingerprint(config)
    write_json(path, state)


def rebind_run_state_fingerprints() -> None:
    for root in EXPERIMENT_ROOTS:
        path = root / "run_state.json"
        if path.is_file():
            rebind_run_state_fingerprint(path)


def rebind_source_evidence_indexes() -> None:
    overlays = [
        *(ROOT / "experiments/extensions").glob("010_*"),
        *(ROOT / "experiments/extensions").glob("013_*"),
        *(ROOT / "experiments/extensions").glob("014_*"),
        *(ROOT / "experiments/extensions").glob("015_*"),
    ]
    for overlay in overlays:
        index_path = overlay / "source_evidence/manifest.json"
        if not index_path.is_file():
            continue
        index = json.loads(index_path.read_text(encoding="utf-8"))
        for item in index["files"]:
            item["sha256"] = sha256(overlay / item["path"])
        write_json(index_path, index)


def rebind_combined_result() -> None:
    path = ROOT / "experiments/010_four_model_panel_20260801_120442/combined_result.v1.json"
    result = json.loads(path.read_text(encoding="utf-8"))
    source = ROOT / result["source_run"]["path"]
    result["source_run"]["manifest_sha256"] = sha256(source / "manifest.json")
    result["source_run"]["run_state_sha256"] = sha256(source / "run_state.json")
    for item in result["completion_overlays"]:
        overlay = ROOT / item["path"]
        item["manifest_sha256"] = sha256(overlay / "manifest.json")
        item["run_state_sha256"] = sha256(overlay / "run_state.json")
        item["source_evidence_index_sha256"] = sha256(
            overlay / "source_evidence/manifest.json"
        )
    write_json(path, result)


def recovery_result_artifacts() -> list[dict[str, str]]:
    overlay = ROOT / "experiments/extensions/010_gemini_permission_recovery_20260802"
    paths = sorted(overlay.glob("run/candidate_created_by_*/solver_results/score_*.json"))
    if len(paths) != 3:
        raise ValueError(f"expected three Gemini recovery score files, found {len(paths)}")
    return [
        {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)} for path in paths
    ]


def rebind_recovery_result() -> None:
    path = ROOT / "experiments/adjudications/010_provider_recovery_result.v1.json"
    result = json.loads(path.read_text(encoding="utf-8"))
    source = ROOT / result["source_run"]["path"]
    result["source_run"]["manifest_sha256"] = sha256(source / "manifest.json")
    result["source_run"]["run_state_sha256"] = sha256(source / "run_state.json")
    recovery = result["gemini_solver_recovery"]
    overlay = ROOT / recovery["path"]
    recovery["manifest_sha256"] = sha256(overlay / "manifest.json")
    recovery["run_state_sha256"] = sha256(overlay / "run_state.json")
    recovery["source_evidence_index_sha256"] = sha256(
        overlay / "source_evidence/manifest.json"
    )
    recovery.pop("runtime_logs", None)
    recovery["result_artifacts"] = recovery_result_artifacts()
    for item in result["gemini_creator_recovery"]:
        item["manifest_sha256"] = sha256(ROOT / item["path"] / "manifest.json")
    result["report"]["sha256"] = sha256(ROOT / result["report"]["path"])
    write_json(path, result)


def rebind_registry() -> None:
    path = ROOT / "experiments/registry.v1.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    for experiment in registry["experiments"]:
        for item in experiment.get("evidence", []):
            item["sha256"] = sha256(ROOT / item["path"])
        recovery = experiment.get("recovery_adjudication")
        if recovery:
            recovery["sha256"] = sha256(ROOT / recovery["path"])
    for candidate in registry["candidates"]:
        for item in candidate.get("evidence", []):
            item["sha256"] = sha256(ROOT / item["path"])
    write_json(path, registry)


def main() -> None:
    sanitize_public_files()
    rebind_controller_validations()
    rebind_manifest_candidate_digests()
    rebind_run_state_fingerprints()
    rebind_source_evidence_indexes()
    rebind_combined_result()
    rebind_recovery_result()
    rebind_registry()
    print("Prepared public evidence and rebound dependent digests.")


if __name__ == "__main__":
    main()
