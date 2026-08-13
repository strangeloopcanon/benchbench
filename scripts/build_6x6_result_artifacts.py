#!/usr/bin/env python3
"""Build the canonical BenchBench status from the adjudication registry.

Raw experiment folders are historical evidence.  They are never a source of a
current benchmark claim by themselves: promotion requires an explicit,
digest-backed ``validated`` registry entry.
"""

from __future__ import annotations

import hashlib
import json
import sys
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchbench_results import parse_score_data
from benchbench_run_state import (
    SOURCE_SNAPSHOT_SCHEMA,
    config_fingerprint,
    verify_source_snapshot,
)
from benchbench_schema import benchmark_package_digest, validate_artifact_tree


REGISTRY_PATH = ROOT / "experiments" / "registry.v1.json"
CANONICAL_DIR = ROOT / "experiments" / "canonical"
LEGACY_MD = ROOT / "experiments" / "result_grids_6x6_20260523.md"
FIGURE_NAMES = (
    "canonical_status.svg",
)
FRONTIER_FOUR_POLICY = "benchbench.frontier-four/2026-08-01"
FRONTIER_FOUR_INVOCATION_IDS = [
    "codex__gpt_5_6_sol__effort_high",
    "codex__gpt_5_6_terra__effort_xhigh",
    "antigravity__gemini_3_6_flash_high__effort_high",
    "cursor__claude_opus_5_thinking_high__effort_high",
]
ALLOWED_OUTCOMES = {
    "validated",
    "historical_noncanonical",
    "rejected",
    "invalid",
    "infrastructure_incomplete",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence_path(root: Path, item: dict[str, str]) -> Path:
    if set(item) != {"path", "sha256"}:
        raise ValueError("evidence entries must contain exactly path and sha256")
    resolved_root = root.resolve()
    unresolved = root / item["path"]
    cursor = unresolved
    while cursor != root and cursor.is_relative_to(root):
        if cursor.is_symlink():
            raise ValueError(f"evidence path contains a symbolic link: {item['path']}")
        cursor = cursor.parent
    path = unresolved.resolve()
    if not path.is_relative_to(resolved_root):
        raise ValueError(f"evidence escapes repository root: {item['path']}")
    return path


def _validate_evidence(root: Path, evidence: list[dict[str, str]]) -> None:
    for item in evidence:
        path = _evidence_path(root, item)
        if not path.is_file():
            raise ValueError(f"missing adjudication evidence: {item['path']}")
        if path.stat().st_nlink != 1:
            raise ValueError(f"adjudication evidence is hard-linked: {item['path']}")
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"adjudication evidence digest changed: {item['path']}")


def _validated_package(root: Path, candidate: dict[str, Any]) -> tuple[Path, str]:
    package = candidate.get("benchmark_package")
    if not isinstance(package, dict) or set(package) != {"path", "sha256"}:
        raise ValueError(f"validated candidate lacks a digest-backed benchmark package: {candidate.get('id')}")
    package_path = (root / str(package["path"])).resolve()
    if not package_path.is_relative_to(root.resolve()) or not package_path.is_dir():
        raise ValueError(f"validated candidate package is missing or outside the repository: {candidate.get('id')}")
    validate_artifact_tree(package_path)
    package_digest = benchmark_package_digest(package_path)
    if package_digest != package["sha256"]:
        raise ValueError(f"validated candidate package digest changed: {candidate.get('id')}")
    return package_path, package_digest


def _validate_mechanical_gate(
    root: Path,
    candidate: dict[str, Any],
    package_digest: str,
) -> None:
    mechanical = candidate.get("mechanical_validation")
    evidence = mechanical.get("evidence") if isinstance(mechanical, dict) else None
    if mechanical is None or mechanical.get("valid") is not True or not isinstance(evidence, list):
        raise ValueError(f"validated candidate lacks a passing mechanical gate: {candidate.get('id')}")
    _validate_evidence(root, evidence)
    records: list[dict[str, Any]] = []
    report_digests: set[str] = set()
    for item in evidence:
        path = _evidence_path(root, item)
        if path.suffix == ".json":
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if value.get("schema_version") == "benchbench.validation/v1":
                records.append(value)
        else:
            report_digests.add(item["sha256"])
    if len(records) != 1:
        raise ValueError(f"validated candidate lacks one structured mechanical record: {candidate.get('id')}")
    record = records[0]
    if (
        record.get("valid") is not True
        or record.get("candidate_digest") != package_digest
        or record.get("deterministic") is not True
        or record.get("frozen_package_match") is not True
        or record.get("leak_match_count") != 0
        or record.get("report_sha256") not in report_digests
    ):
        raise ValueError(f"validated candidate mechanical record is not bound to the package: {candidate.get('id')}")


def _declared_solver_panel(
    root: Path,
    candidate: dict[str, Any],
) -> tuple[list[str], Path, list[dict[str, Any]]]:
    evidence = candidate.get("run_state_evidence")
    if not isinstance(evidence, dict):
        raise ValueError(f"validated candidate lacks run-state evidence: {candidate.get('id')}")
    _validate_evidence(root, [evidence])
    try:
        state = json.loads(_evidence_path(root, evidence).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"validated candidate has invalid run-state evidence: {candidate.get('id')}") from exc
    config = state.get("config")
    expected = config.get("solver_models") if isinstance(config, dict) else None
    if (
        state.get("schema_version") != 1
        or not isinstance(config, dict)
        or state.get("config_fingerprint") != config_fingerprint(config)
        or not isinstance(expected, list)
        or len(expected) < 2
        or not all(isinstance(identity, str) and "__effort_" in identity for identity in expected)
        or len(expected) != len(set(expected))
    ):
        raise ValueError(f"validated candidate has no complete declared solver panel: {candidate.get('id')}")
    if candidate.get("experiment_id") == "010" and (
        config.get("panel_policy") != FRONTIER_FOUR_POLICY
        or config.get("creator_models") != FRONTIER_FOUR_INVOCATION_IDS
        or expected != FRONTIER_FOUR_INVOCATION_IDS
    ):
        raise ValueError(
            f"Experiment 010 candidate does not use the exact frontier-four panel: {candidate.get('id')}"
        )
    state_path = _evidence_path(root, evidence)
    manifest_evidence = candidate.get("run_manifest_evidence")
    if not isinstance(manifest_evidence, dict):
        raise ValueError(f"validated candidate lacks run-manifest evidence: {candidate.get('id')}")
    _validate_evidence(root, [manifest_evidence])
    manifest_path = _evidence_path(root, manifest_evidence)
    if state_path.name != "run_state.json" or manifest_path.name != "manifest.json":
        raise ValueError(f"validated candidate has noncanonical run evidence paths: {candidate.get('id')}")
    if state_path.parent != manifest_path.parent:
        raise ValueError(f"validated candidate run state and manifest are from different runs: {candidate.get('id')}")
    run_root = state_path.parent
    source_snapshot = state.get("source_snapshot")
    source_snapshot_digest = (
        source_snapshot.get("digest") if isinstance(source_snapshot, dict) else None
    )
    if (
        not isinstance(source_snapshot, dict)
        or source_snapshot.get("schema_version") != SOURCE_SNAPSHOT_SCHEMA
        or source_snapshot.get("path") != "source_snapshot"
        or source_snapshot.get("manifest_path") != "source_snapshot/manifest.json"
        or not isinstance(source_snapshot_digest, str)
        or len(source_snapshot_digest) != 64
        or not isinstance(source_snapshot.get("file_count"), int)
        or isinstance(source_snapshot.get("file_count"), bool)
    ):
        raise ValueError(
            f"validated candidate lacks a bound source snapshot: {candidate.get('id')}"
        )
    try:
        verified_snapshot = verify_source_snapshot(
            run_root,
            expected_digest=source_snapshot_digest,
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(
            f"validated candidate has an invalid source snapshot: {candidate.get('id')}"
        ) from exc
    if (
        verified_snapshot.get("schema_version") != source_snapshot.get("schema_version")
        or verified_snapshot.get("digest") != source_snapshot_digest
        or len(verified_snapshot.get("files", [])) != source_snapshot.get("file_count")
    ):
        raise ValueError(
            f"validated candidate source snapshot conflicts with run state: {candidate.get('id')}"
        )
    if config.get("harness_digest") != source_snapshot_digest:
        raise ValueError(
            f"validated candidate source snapshot does not match harness digest: {candidate.get('id')}"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"validated candidate has invalid run-manifest evidence: {candidate.get('id')}") from exc
    if not isinstance(manifest, list) or not all(isinstance(item, dict) for item in manifest):
        raise ValueError(f"validated candidate has invalid run-manifest evidence: {candidate.get('id')}")
    return expected, run_root, manifest


def _expected_solver_result_dir(package_path: Path) -> Path:
    if package_path.name != "artifact":
        raise ValueError("validated candidate package must use the immutable artifact layout")
    if package_path.parent.name.startswith("attempt_"):
        return package_path.parent.parent / "solver_results"
    return package_path.parent / "solver_results"


def _validate_successful_panel(
    root: Path,
    candidate: dict[str, Any],
    package_path: Path,
    package_digest: str,
    expected_identities: list[str],
    run_root: Path,
    manifest: list[dict[str, Any]],
) -> None:
    panel = candidate.get("solver_panel")
    if not isinstance(panel, list) or not panel:
        raise ValueError(f"validated candidate lacks a solver panel: {candidate.get('id')}")
    identities: set[str] = set()
    score_paths: set[Path] = set()
    prediction_paths: set[Path] = set()
    if not package_path.is_relative_to(run_root):
        raise ValueError(f"validated candidate package is outside its declared run: {candidate.get('id')}")
    result_dir = _expected_solver_result_dir(package_path).resolve()
    for cell in panel:
        if not isinstance(cell, dict) or cell.get("state") != "success":
            raise ValueError(f"validated candidate has an incomplete solver panel: {candidate.get('id')}")
        identity = cell.get("identity")
        if not isinstance(identity, str) or "__effort_" not in identity or identity in identities:
            raise ValueError(f"validated candidate has an invalid solver identity: {candidate.get('id')}")
        identities.add(identity)
        score_evidence = cell.get("score_evidence")
        prediction_evidence = cell.get("prediction_evidence")
        if not isinstance(score_evidence, dict) or not isinstance(prediction_evidence, dict):
            raise ValueError(f"validated candidate has undigested solver evidence: {candidate.get('id')}")
        _validate_evidence(root, [score_evidence, prediction_evidence])
        score_path = _evidence_path(root, score_evidence)
        prediction_path = _evidence_path(root, prediction_evidence)
        expected_score_path = (result_dir / f"score_solver_{identity}.json").resolve()
        expected_prediction_path = (result_dir / f"predictions_solver_{identity}.jsonl").resolve()
        if score_path != expected_score_path or prediction_path != expected_prediction_path:
            raise ValueError(f"validated candidate solver evidence is not controller-owned: {candidate.get('id')}")
        if score_path.is_relative_to(package_path) or prediction_path.is_relative_to(package_path):
            raise ValueError(f"validated candidate solver evidence is inside the benchmark package: {candidate.get('id')}")
        if score_path in score_paths or prediction_path in prediction_paths:
            raise ValueError(f"validated candidate reuses solver evidence: {candidate.get('id')}")
        score_paths.add(score_path)
        prediction_paths.add(prediction_path)
        try:
            raw_score = json.loads(score_path.read_text(encoding="utf-8"))
            parsed = parse_score_data(raw_score, allow_legacy=False)
        except Exception as exc:
            raise ValueError(f"validated candidate has an invalid normalized score: {candidate.get('id')}") from exc
        declared_score = cell.get("score")
        if not isinstance(declared_score, dict) or parsed != declared_score:
            raise ValueError(f"validated candidate score conflicts with evidence: {candidate.get('id')}")
        if raw_score.get("candidate_digest") != package_digest:
            raise ValueError(f"validated candidate score has the wrong package digest: {candidate.get('id')}")
        if raw_score.get("prediction_digest") != sha256_file(prediction_path):
            raise ValueError(f"validated candidate score has the wrong prediction digest: {candidate.get('id')}")
        gold_path = package_path / "gold_private_sample.jsonl"
        if not gold_path.is_file() or raw_score.get("gold_digest") != sha256_file(gold_path):
            raise ValueError(f"validated candidate score has the wrong gold digest: {candidate.get('id')}")
        if raw_score.get("invocation_id") != identity:
            raise ValueError(f"validated candidate score has the wrong invocation identity: {candidate.get('id')}")
        matching_manifest_cells = [
            item
            for item in manifest
            if item.get("solver_artifact_id") == identity
            and item.get("cell_state") == "success"
            and item.get("phase") in {"solver", "solver_extension"}
            and Path(str(item.get("score_path", ""))).resolve() == score_path
            and Path(str(item.get("predictions_path", ""))).resolve() == prediction_path
        ]
        if len(matching_manifest_cells) != 1:
            raise ValueError(f"validated candidate solver evidence is not bound to one manifest cell: {candidate.get('id')}")
        manifest_cell = matching_manifest_cells[0]
        if (
            manifest_cell.get("score_summary") != declared_score
            or manifest_cell.get("candidate_digest") != package_digest
            or manifest_cell.get("gold_digest") != raw_score.get("gold_digest")
            or manifest_cell.get("prediction_digest") != raw_score.get("prediction_digest")
        ):
            raise ValueError(f"validated candidate manifest cell conflicts with solver evidence: {candidate.get('id')}")
        snapshot = manifest_cell.get("candidate_snapshot")
        if snapshot is not None and Path(str(snapshot)).resolve() != package_path:
            raise ValueError(f"validated candidate manifest cell points to a different package: {candidate.get('id')}")
    if identities != set(expected_identities) or len(panel) != len(expected_identities):
        raise ValueError(f"validated candidate has an incomplete solver panel: {candidate.get('id')}")


def validate_registry(registry: dict[str, Any], root: Path = ROOT) -> None:
    """Fail closed on malformed, stale, or implicitly promoted registry data."""
    if registry.get("schema_version") != "benchbench.experiment-registry/v1":
        raise ValueError("unsupported experiment registry schema")
    declared_status = registry.get("canonical", {}).get("status")
    if declared_status not in {"no_validated_incumbent", "validated_incumbent"}:
        raise ValueError("registry must state a supported canonical status explicitly")
    experiment_entries = registry.get("experiments", [])
    experiment_id_list = [entry.get("id") for entry in experiment_entries]
    experiment_ids = set(experiment_id_list)
    if not experiment_ids:
        raise ValueError("registry has no experiments")
    if len(experiment_ids) != len(experiment_id_list):
        raise ValueError("registry contains duplicate experiment ids")
    candidate_ids = [entry.get("id") for entry in registry.get("candidates", [])]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("registry contains duplicate candidate ids")
    historical_comparison = registry.get("historical_comparison")
    if historical_comparison is not None:
        if not isinstance(historical_comparison, dict) or set(historical_comparison) != {
            "leader_candidate_id",
            "rank",
            "verdict",
            "basis",
            "qualification",
        }:
            raise ValueError("registry has a malformed historical comparison")
        if (
            historical_comparison.get("leader_candidate_id") not in candidate_ids
            or historical_comparison.get("rank") != 1
            or historical_comparison.get("verdict") != "win_over_challengers"
            or not isinstance(historical_comparison.get("basis"), str)
            or not isinstance(historical_comparison.get("qualification"), str)
        ):
            raise ValueError("registry has an invalid historical comparison")
    for entry in registry["experiments"]:
        if entry.get("outcome") not in ALLOWED_OUTCOMES:
            raise ValueError(f"unknown experiment outcome: {entry.get('id')}")
        _validate_evidence(root, entry.get("evidence", []))
        if entry.get("include_in_landscape") is True:
            if entry.get("outcome") not in {"historical_noncanonical", "validated"}:
                raise ValueError(f"invalid experiment included in landscape: {entry.get('id')}")
            pointer = entry.get("landscape_evidence")
            if not isinstance(pointer, dict):
                raise ValueError(f"landscape experiment lacks evidence: {entry.get('id')}")
            _validate_evidence(root, [pointer])
    for candidate in registry.get("candidates", []):
        if candidate.get("experiment_id") not in experiment_ids:
            raise ValueError(f"candidate references unknown experiment: {candidate.get('id')}")
        outcome = candidate.get("outcome")
        if outcome not in ALLOWED_OUTCOMES:
            raise ValueError(f"unknown candidate outcome: {candidate.get('id')}")
        if candidate.get("canonical_eligible"):
            if outcome != "validated":
                raise ValueError(f"ineligible candidate promoted: {candidate.get('id')}")
            if not candidate.get("evidence"):
                raise ValueError(f"validated candidate lacks evidence: {candidate.get('id')}")
            package_path, package_digest = _validated_package(root, candidate)
            _validate_mechanical_gate(root, candidate, package_digest)
            expected_panel, run_root, manifest = _declared_solver_panel(root, candidate)
            _validate_successful_panel(
                root,
                candidate,
                package_path,
                package_digest,
                expected_panel,
                run_root,
                manifest,
            )
        _validate_evidence(root, candidate.get("evidence", []))
    derived_status = (
        "validated_incumbent"
        if any(candidate.get("canonical_eligible") for candidate in registry.get("candidates", []))
        else "no_validated_incumbent"
    )
    if declared_status != derived_status:
        raise ValueError(
            f"canonical status {declared_status!r} conflicts with derived status {derived_status!r}"
        )


def load_registry(registry_path: Path = REGISTRY_PATH) -> dict[str, Any]:
    """Load and fail closed on malformed or stale canonical registry data."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    validate_registry(registry, registry_path.parents[1])
    return registry


def canonical_state(registry: dict[str, Any]) -> dict[str, Any]:
    eligible = [c for c in registry.get("candidates", []) if c.get("canonical_eligible")]
    if eligible:
        return {
            "status": "validated_incumbent",
            "message": "Every listed incumbent passed the registry's mechanical, adjudication, and complete-panel gates.",
            "incumbents": [
                {"id": c["id"], "name": c["name"], "creator": c["creator"]}
                for c in eligible
            ],
        }
    return {
        "status": "no_validated_incumbent",
        "message": "No benchmark has passed the current validity and infrastructure gates.",
        "incumbents": [],
    }


def public_history(registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the intentionally visible noncanonical findings in registry order."""
    rows: list[dict[str, Any]] = []
    for candidate in registry.get("candidates", []):
        if candidate.get("canonical_eligible"):
            continue
        rows.append(
            {
                "id": candidate["id"],
                "experiment_id": candidate["experiment_id"],
                "name": candidate["name"],
                "creator": candidate["creator"],
                "outcome": candidate["outcome"],
                "reason": candidate["reason"],
                "historical_scores": candidate.get("historical_scores", []),
                "historical_comparison": candidate.get("historical_comparison"),
                "cell_states": candidate.get("cell_states", []),
                "required_next_step": candidate["required_next_step"],
            }
        )
    return rows


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _status_svg(
    state: dict[str, Any],
    histories: list[dict[str, Any]],
    comparison: dict[str, Any] | None,
    title: str,
) -> str:
    experiment_010 = [item for item in histories if item["experiment_id"] == "010"]
    opus_incomplete = sum(
        cell["solver"] == "Claude Opus 5 high" and cell["state"] == "timeout"
        for item in experiment_010
        for cell in item["cell_states"]
    )
    height = 226
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{height}" viewBox="0 0 1080 {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<rect x="24" y="22" width="1032" height="112" rx="8" fill="#fbe4e4" stroke="#a82b2b"/>',
        f'<text x="48" y="62" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="700" fill="#761c19">{escape(title)}</text>',
        f'<text x="48" y="96" font-family="Arial, Helvetica, sans-serif" font-size="18" fill="#333">{escape(state["message"] if state["status"] == "no_validated_incumbent" else "Validated incumbent recorded.")}</text>',
        '<text x="48" y="121" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="#555">Registry v1 separates canonical validity from corrected historical comparison.</text>',
    ]
    if comparison is not None:
        leader = next(
            item for item in histories if item["id"] == comparison["leader_candidate_id"]
        )
        lines.append(
            '<text x="48" y="151" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="700" fill="#333">'
            + escape(
                f'Historical #{comparison["rank"]}: {leader["name"]} is a {comparison["verdict"].replace("_", " ")}; original gold remains invalid.'
            )
            + "</text>"
        )
    lines.extend([
        '<text x="48" y="181" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" fill="#333">'
        + escape("Gemini 3.7 solved all three Experiment 010 candidates at 30/30.")
        + "</text>",
        '<text x="48" y="205" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="#555">'
        + escape(f"CloudSLA-Forensics was valid but both tested solvers scored 30/30; Opus still did not complete {opus_incomplete}/3.")
        + "</text>",
    ])
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_markdown(
    registry: dict[str, Any],
    state: dict[str, Any],
    histories: list[dict[str, Any]],
    comparison: dict[str, Any] | None,
) -> str:
    rows = []
    for item in histories:
        scores = item["historical_scores"]
        score_text = ", ".join(scores) if scores else "No canonical numeric score"
        states = ", ".join(
            f'{cell["solver"]}: '
            + ("did not complete (timeout)" if cell["state"] == "timeout" else cell["state"])
            for cell in item["cell_states"]
        )
        rows.append([
            item["experiment_id"],
            item["name"],
            item["creator"],
            item["outcome"],
            score_text + (f"; {states}" if states else ""),
            item["required_next_step"],
        ])
    experiment_rows = [
        [entry["id"], entry["run_path"], entry["outcome"], entry["summary"]]
        for entry in registry["experiments"]
    ]
    if state["status"] == "validated_incumbent":
        current_line = "**Validated incumbent:** " + ", ".join(
            f'{item["name"]} ({item["creator"]})' for item in state["incumbents"]
        )
    else:
        current_line = "**No validated incumbent.** No benchmark can be promoted until its public evidence, gold generation, scorer, complete solver panel, and execution state pass the registry gates."
    comparison_lines: list[str] = []
    if comparison is not None:
        leader = next(
            item for item in histories if item["id"] == comparison["leader_candidate_id"]
        )
        comparison_lines = [
            "## Corrected Historical Result",
            "",
            f'**#{comparison["rank"]}: {leader["name"]} is the best corrected historical candidate and counts as a win over the challengers.**',
            "",
            comparison["basis"],
            "",
            comparison["qualification"],
            "",
        ]
    return "\n".join([
        "# Canonical BenchBench Status",
        "",
        "Generated from `experiments/registry.v1.json`. Raw run folders remain preserved as evidence; this page does not turn a historical score into a current claim.",
        "",
        "## Current State",
        "",
        current_line,
        "",
        "![Canonical status](figures/canonical_status.svg)",
        "",
        *comparison_lines,
        "## Historical Results Excluded From Canonical Ranking",
        "",
        _table(["experiment", "benchmark", "creator", "outcome", "preserved historical evidence", "required next step"], rows),
        "",
        "The figures above are historical evidence only. In particular, `0/30` is never used for a provider error, timeout, malformed output, or incomplete panel.",
        "",
        "## Adjudications",
        "",
        "- [Reimbursement Forensics](../adjudications/004_reimbursement_forensics.md): Decimal half-up re-audit changed three gold answers and rescored the retained predictions to `12, 16, 11, 13, 11, 11`. It remains the #1 corrected historical candidate and a win over the challengers, while the original run remains invalid and noncanonical.",
        "- [Service Credit Forensics](../adjudications/007_service_credit_forensics.md): a higher-precedence public timeline contradicts gold computed from lower-precedence monitoring states.",
        "- [Fable creator sweep](../adjudications/008_fable_creator_sweep.md): GPT-5.2 was a provider error and Claude Opus timed out; neither is a `0/30` result.",
        "- [Four-model panel](../adjudications/009_four_model_panel.md): both created candidates failed the mechanical score-report contract, Antigravity then failed before inference, and no solver cell ran.",
        "- [Frontier-four panel](../adjudications/010_four_model_panel.md): original sealed result; three candidates passed the mechanical gate and every completed cell was `30/30`.",
        "- [Experiment 010 provider recovery](../adjudications/010_provider_recovery_20260802.md): Gemini recovered all three missing solver cells at `30/30`; Opus still did not complete two cells, and Gemini produced no valid candidate.",
        "- [Gemini 3.7 Flash](../adjudications/013_gemini_37_flash.md): Gemini 3.7 solved all three valid Experiment 010 candidates at `30/30`; its mechanically valid CloudSLA-Forensics candidate was also solved `30/30` by Gemini 3.6 and Gemini 3.7.",
        "",
        "## Registry Coverage",
        "",
        _table(["experiment", "raw run", "outcome", "registry read"], experiment_rows),
        "",
        "A future incumbent must be introduced by a new `validated` candidate entry with digest-verified evidence. The canonical builder rejects a candidate marked eligible with any other outcome.",
        "",
    ])


def build_canonical(
    registry_path: Path = REGISTRY_PATH,
    canonical_dir: Path = CANONICAL_DIR,
    legacy_path: Path = LEGACY_MD,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    state = canonical_state(registry)
    histories = public_history(registry)
    comparison = registry.get("historical_comparison")
    canonical_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = canonical_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": "benchbench.canonical-status/v1",
        "registry_sha256": sha256_file(registry_path),
        "current_state": state,
        "historical_comparison": comparison,
        "historical_noncanonical": histories,
    }
    (canonical_dir / "status.v1.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (canonical_dir / "README.md").write_text(
        render_markdown(registry, state, histories, comparison), encoding="utf-8"
    )
    for figure_name in FIGURE_NAMES:
        title = (
            "Canonical status: no validated incumbent"
            if state["status"] == "no_validated_incumbent"
            else "Canonical status: validated incumbent"
        )
        (figure_dir / figure_name).write_text(
            _status_svg(state, histories, comparison, title), encoding="utf-8"
        )
    legacy_path.write_text(
        "# 6x6 Result Grids - Superseded\n\n"
        "Reimbursement Forensics had invalid original gold and is not a canonical incumbent. "
        "After Decimal correction and rescoring retained predictions without a model rerun, it remains the #1 corrected historical candidate and a win over the later challengers. "
        "See [`canonical/README.md`](canonical/README.md) and `registry.v1.json` for the qualified adjudicated state.\n",
        encoding="utf-8",
    )
    return data


def main() -> None:
    data = build_canonical()
    print(f"Wrote canonical status: {data['current_state']['status']}")


if __name__ == "__main__":
    main()
