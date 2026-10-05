from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from benchbench_run_state import create_source_snapshot, record_source_snapshot
from run_existing_solver_extension import verify_frozen_source_evidence


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_6x6_result_artifacts.py"
SPEC = importlib.util.spec_from_file_location("canonical_artifacts", SCRIPT)
assert SPEC and SPEC.loader
canonical_artifacts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(canonical_artifacts)


def test_registry_has_no_validated_incumbent_and_preserves_invalid_history() -> None:
    registry = canonical_artifacts.load_registry()
    state = canonical_artifacts.canonical_state(registry)
    history = canonical_artifacts.public_history(registry)

    assert state["status"] == "no_validated_incumbent"
    assert state["incumbents"] == []
    assert {item["id"] for item in history} == {
        "004-reimbursement-forensics",
        "007-service-credit-forensics",
        "008-rosetta-fieldwork",
        "009-counterfeit-clock",
        "009-patchwork-access-logic",
        "010-auditweave",
        "010-counterfactual-firewall-policy-synthesis",
        "010-gemini-empty-artifact",
        "010-consolidation-point",
        "013-cloudsla-forensics",
        "014-maritime-general-average-forensics",
        "015-reimbursement-forensics-v2",
    }
    fable = next(item for item in history if item["id"] == "008-rosetta-fieldwork")
    assert {cell["state"] for cell in fable["cell_states"]} == {"provider_error", "timeout"}
    reimbursement = next(
        item for item in history if item["id"] == "004-reimbursement-forensics"
    )
    assert reimbursement["outcome"] == "invalid"
    assert reimbursement["historical_comparison"] == {
        "rank": 1,
        "verdict": "win_over_challengers",
            "read": "Best corrected historical candidate: all six retained solver scores remain low and nonzero (11-16/30), while later challengers reach at least 25/30, are invalid, or have incomplete panels; every completed Experiment 010 and Experiment 013 challenger cell is 30/30.",
    }
    experiment_009 = [item for item in history if item["experiment_id"] == "009"]
    assert {item["outcome"] for item in experiment_009} == {"invalid"}
    assert all(item["historical_scores"] == [] for item in experiment_009)
    experiment_010 = [item for item in history if item["experiment_id"] == "010"]
    assert {item["outcome"] for item in experiment_010} == {
        "invalid",
        "infrastructure_incomplete",
    }
    assert all(
        score.endswith("30/30") or "30/30" in score
        for item in experiment_010
        for score in item["historical_scores"]
    )
    assert {
        cell["state"]
        for item in experiment_010
        for cell in item["cell_states"]
    } == {"timeout", "invalid_output"}
    consolidation = next(item for item in experiment_010 if item["id"] == "010-consolidation-point")
    assert "completed cells" in consolidation["historical_scores"][0]
    assert registry["historical_comparison"]["leader_candidate_id"] == reimbursement["id"]


def test_experiment_010_combined_result_is_typed_and_budgeted() -> None:
    path = ROOT / "experiments" / "010_four_model_panel_20260801_120442" / "combined_result.v1.json"
    result = json.loads(path.read_text(encoding="utf-8"))

    assert result["schema_version"] == "benchbench.combined-result/v1"
    assert result["outcome"] == "infrastructure_incomplete"
    assert result["usage"] == {
        "source_run_reported_tokens": 6_344_511,
        "completion_overlays_reported_tokens": 692_362,
        "combined_reported_tokens": 7_036_873,
        "zero_telemetry_timeouts": 2,
        "conservative_reservation_per_zero_telemetry_timeout": 5_000_000,
        "charged_equivalent_tokens": 17_036_873,
        "dispatch_ceiling_tokens": 20_000_000,
        "qualification": "Charged-equivalent tokens are conservative controller accounting, not provider-reported consumption.",
    }
    cells = [
        cell
        for candidate in result["candidates"]
        for cell in candidate["cells"].values()
    ]
    assert {cell["state"] for cell in cells} == {
        "success",
        "invalid_output",
        "timeout",
    }
    assert all(
        cell["score"] == {"correct": 30, "total": 30}
        for cell in cells
        if cell["state"] == "success"
    )
    for overlay in result["completion_overlays"]:
        overlay_root = ROOT / overlay["path"]
        index_path = overlay_root / "source_evidence" / "manifest.json"
        assert hashlib.sha256(index_path.read_bytes()).hexdigest() == overlay[
            "source_evidence_index_sha256"
        ]
        index = verify_frozen_source_evidence(overlay_root)
        source_manifest = next(
            item for item in index["files"] if item["path"].endswith("source_manifest.json")
        )
        assert source_manifest["sha256"] == result["source_run"]["manifest_sha256"]


def test_experiment_010_recovery_is_digest_bound_in_registry() -> None:
    registry = json.loads((ROOT / "experiments" / "registry.v1.json").read_text(encoding="utf-8"))
    experiment = next(item for item in registry["experiments"] if item["id"] == "010")
    recovery_ref = experiment["recovery_adjudication"]
    recovery_path = ROOT / recovery_ref["path"]
    assert hashlib.sha256(recovery_path.read_bytes()).hexdigest() == recovery_ref["sha256"]
    recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
    assert recovery["schema_version"] == "benchbench.recovery-adjudication/v1"
    assert [cell["state"] for cell in recovery["gemini_solver_recovery"]["cells"]] == [
        "success",
        "success",
        "success",
    ]
    assert all(
        (cell["correct"], cell["total"]) == (30, 30)
        for cell in recovery["gemini_solver_recovery"]["cells"]
    )
    assert recovery["opus"]["did_not_complete_original_solver_cells"] == 2
    assert recovery["usage"]["recovery_aware_reported_tokens"] == 8_050_744
    artifacts = recovery["gemini_solver_recovery"]["result_artifacts"]
    assert len(artifacts) == 3
    for artifact in artifacts:
        assert hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest() == artifact[
            "sha256"
        ]


def test_historical_leader_must_reference_a_registered_candidate() -> None:
    registry = canonical_artifacts.load_registry()
    malformed = copy.deepcopy(registry)
    malformed["historical_comparison"]["leader_candidate_id"] = "missing-candidate"

    with pytest.raises(ValueError, match="invalid historical comparison"):
        canonical_artifacts.validate_registry(malformed, ROOT)


def test_invalid_candidate_cannot_be_promoted() -> None:
    registry = canonical_artifacts.load_registry()
    invalid_promotion = copy.deepcopy(registry)
    invalid_promotion["candidates"][0]["canonical_eligible"] = True

    with pytest.raises(ValueError, match="ineligible candidate promoted"):
        canonical_artifacts.validate_registry(invalid_promotion, ROOT)


def test_future_promotion_requires_mechanics_and_a_complete_successful_panel(tmp_path: Path) -> None:
    run_root = tmp_path / "future_run"
    package = run_root / "run" / "candidate_created_by_sol" / "attempt_0001" / "artifact"
    package.mkdir(parents=True)
    result_dir = package.parent.parent / "solver_results"
    result_dir.mkdir()
    gold = package / "gold_private_sample.jsonl"
    mechanical_report = package.parent / "controller_validation_report.txt"
    mechanical_record = package.parent / "controller_validation.v1.json"
    run_state_path = run_root / "run_state.json"
    manifest_path = run_root / "manifest.json"
    adjudication = tmp_path / "adjudication.md"
    gold.write_text('{"id":"x","answer":"a"}\n', encoding="utf-8")
    mechanical_report.write_text("validated controls and frozen digest\n", encoding="utf-8")
    adjudication.write_text("reviewed\n", encoding="utf-8")
    package_digest = canonical_artifacts.benchmark_package_digest(package)
    mechanical_record.write_text(
        json.dumps(
            {
                "schema_version": "benchbench.validation/v1",
                "valid": True,
                "candidate_digest": package_digest,
                "deterministic": True,
                "frozen_package_match": True,
                "leak_match_count": 0,
                "report_sha256": hashlib.sha256(mechanical_report.read_bytes()).hexdigest(),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    identities = [
        "codex__gpt_5_6_sol__effort_high",
        "codex__gpt_5_6_terra__effort_high",
    ]
    config = {"solver_models": identities}
    run_state_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "config": config,
                "config_fingerprint": canonical_artifacts.config_fingerprint(config),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    harness_source = tmp_path / "harness_source"
    harness_source.mkdir()
    (harness_source / "runner.py").write_text("# frozen controller\n", encoding="utf-8")
    source_snapshot = create_source_snapshot(
        harness_source,
        run_root,
        ("runner.py",),
    )
    record_source_snapshot(run_root, source_snapshot)
    bound_state = json.loads(run_state_path.read_text(encoding="utf-8"))
    bound_state["config"]["harness_digest"] = source_snapshot["digest"]
    bound_state["config_fingerprint"] = canonical_artifacts.config_fingerprint(
        bound_state["config"]
    )
    run_state_path.write_text(json.dumps(bound_state) + "\n", encoding="utf-8")

    def evidence(path: Path) -> dict[str, str]:
        return {
            "path": path.relative_to(tmp_path).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    panel = []
    manifest = []
    for identity in identities:
        predictions = result_dir / f"predictions_solver_{identity}.jsonl"
        score_path = result_dir / f"score_solver_{identity}.json"
        predictions.write_text('{"id":"x","answer":"a"}\n', encoding="utf-8")
        normalized = {
            "schema_version": 2,
            "total": 1,
            "correct": 1,
            "accuracy": 1.0,
            "invocation_id": identity,
            "candidate_digest": package_digest,
            "gold_digest": hashlib.sha256(gold.read_bytes()).hexdigest(),
            "prediction_digest": hashlib.sha256(predictions.read_bytes()).hexdigest(),
        }
        score_path.write_text(json.dumps(normalized) + "\n", encoding="utf-8")
        panel.append(
            {
                "identity": identity,
                "state": "success",
                "score": {"total": 1, "correct": 1, "accuracy": 1.0},
                "score_evidence": evidence(score_path),
                "prediction_evidence": evidence(predictions),
            }
        )
        manifest.append(
            {
                "phase": "solver",
                "cell_state": "success",
                "solver_artifact_id": identity,
                "predictions_path": str(predictions),
                "score_path": str(score_path),
                "score_summary": {"total": 1, "correct": 1, "accuracy": 1.0},
                "candidate_digest": package_digest,
                "gold_digest": normalized["gold_digest"],
                "prediction_digest": normalized["prediction_digest"],
            }
        )
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    promoted = {
        "schema_version": "benchbench.experiment-registry/v1",
        "canonical": {"status": "validated_incumbent"},
        "experiments": [{"id": "009", "run_path": "future_run", "outcome": "validated"}],
        "candidates": [
            {
                "id": "009-candidate",
                "experiment_id": "009",
                "name": "Candidate",
                "creator": "Sol",
                "outcome": "validated",
                "canonical_eligible": True,
                "reason": "reviewed",
                "required_next_step": "none",
                "evidence": [evidence(adjudication)],
                "benchmark_package": {
                    "path": package.relative_to(tmp_path).as_posix(),
                    "sha256": package_digest,
                },
                "mechanical_validation": {
                    "valid": True,
                    "evidence": [evidence(mechanical_record), evidence(mechanical_report)],
                },
                "run_state_evidence": evidence(run_state_path),
                "run_manifest_evidence": evidence(manifest_path),
                "solver_panel": panel,
            }
        ],
    }
    canonical_artifacts.validate_registry(promoted, tmp_path)
    assert canonical_artifacts.canonical_state(promoted)["status"] == "validated_incumbent"

    wrong_panel_010 = copy.deepcopy(promoted)
    wrong_panel_010["experiments"][0]["id"] = "010"
    wrong_panel_010["candidates"][0]["experiment_id"] = "010"
    with pytest.raises(ValueError, match="exact frontier-four panel"):
        canonical_artifacts.validate_registry(wrong_panel_010, tmp_path)

    snapshot_file = run_root / "source_snapshot" / "runner.py"
    frozen_source = snapshot_file.read_bytes()
    snapshot_file.write_text("# tampered controller\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid source snapshot"):
        canonical_artifacts.validate_registry(promoted, tmp_path)
    snapshot_file.write_bytes(frozen_source)

    snapshot_manifest = run_root / "source_snapshot" / "manifest.json"
    frozen_manifest = snapshot_manifest.read_bytes()
    snapshot_manifest.unlink()
    with pytest.raises(ValueError, match="invalid source snapshot"):
        canonical_artifacts.validate_registry(promoted, tmp_path)
    snapshot_manifest.write_bytes(frozen_manifest)

    bound_state = run_state_path.read_bytes()
    state_without_snapshot = json.loads(bound_state)
    state_without_snapshot.pop("source_snapshot")
    run_state_path.write_text(json.dumps(state_without_snapshot) + "\n", encoding="utf-8")
    promoted["candidates"][0]["run_state_evidence"] = evidence(run_state_path)
    with pytest.raises(ValueError, match="lacks a bound source snapshot"):
        canonical_artifacts.validate_registry(promoted, tmp_path)
    run_state_path.write_bytes(bound_state)
    promoted["candidates"][0]["run_state_evidence"] = evidence(run_state_path)

    state_with_wrong_digest = json.loads(bound_state)
    state_with_wrong_digest["source_snapshot"]["digest"] = "0" * 64
    run_state_path.write_text(json.dumps(state_with_wrong_digest) + "\n", encoding="utf-8")
    promoted["candidates"][0]["run_state_evidence"] = evidence(run_state_path)
    with pytest.raises(ValueError, match="invalid source snapshot"):
        canonical_artifacts.validate_registry(promoted, tmp_path)
    run_state_path.write_bytes(bound_state)
    promoted["candidates"][0]["run_state_evidence"] = evidence(run_state_path)

    state_with_wrong_harness = json.loads(bound_state)
    state_with_wrong_harness["config"]["harness_digest"] = "f" * 64
    state_with_wrong_harness["config_fingerprint"] = canonical_artifacts.config_fingerprint(
        state_with_wrong_harness["config"]
    )
    run_state_path.write_text(json.dumps(state_with_wrong_harness) + "\n", encoding="utf-8")
    promoted["candidates"][0]["run_state_evidence"] = evidence(run_state_path)
    with pytest.raises(ValueError, match="does not match harness digest"):
        canonical_artifacts.validate_registry(promoted, tmp_path)
    run_state_path.write_bytes(bound_state)
    promoted["candidates"][0]["run_state_evidence"] = evidence(run_state_path)

    promoted["candidates"][0]["solver_panel"][0]["state"] = "timeout"
    with pytest.raises(ValueError, match="incomplete solver panel"):
        canonical_artifacts.validate_registry(promoted, tmp_path)

    # Invocation-shaped evidence planted by the benchmark creator is not
    # promotable even when every digest and manifest field is self-consistent.
    planted = copy.deepcopy(promoted)
    planted["candidates"][0]["solver_panel"][0]["state"] = "success"
    for index, identity in enumerate(identities):
        source_predictions = result_dir / f"predictions_solver_{identity}.jsonl"
        source_score = result_dir / f"score_solver_{identity}.json"
        planted_predictions = package / source_predictions.name
        planted_score = package / source_score.name
        planted_predictions.write_bytes(source_predictions.read_bytes())
        planted_score.write_bytes(source_score.read_bytes())
        planted["candidates"][0]["solver_panel"][index]["prediction_evidence"] = evidence(
            planted_predictions
        )
        planted["candidates"][0]["solver_panel"][index]["score_evidence"] = evidence(
            planted_score
        )
        manifest[index]["predictions_path"] = str(planted_predictions)
        manifest[index]["score_path"] = str(planted_score)
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    planted["candidates"][0]["run_manifest_evidence"] = evidence(manifest_path)
    planted_digest = canonical_artifacts.benchmark_package_digest(package)
    planted["candidates"][0]["benchmark_package"]["sha256"] = planted_digest
    planted_record = json.loads(mechanical_record.read_text(encoding="utf-8"))
    planted_record["candidate_digest"] = planted_digest
    mechanical_record.write_text(json.dumps(planted_record) + "\n", encoding="utf-8")
    planted["candidates"][0]["mechanical_validation"]["evidence"] = [
        evidence(mechanical_record),
        evidence(mechanical_report),
    ]
    with pytest.raises(ValueError, match="not controller-owned"):
        canonical_artifacts.validate_registry(planted, tmp_path)


def test_canonical_rebuild_is_deterministic(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = canonical_artifacts.build_canonical(
        canonical_dir=first_dir,
        legacy_path=tmp_path / "first.md",
    )
    second = canonical_artifacts.build_canonical(
        canonical_dir=second_dir,
        legacy_path=tmp_path / "second.md",
    )

    assert first == second
    assert (first_dir / "README.md").read_bytes() == (second_dir / "README.md").read_bytes()
    assert (first_dir / "status.v1.json").read_bytes() == (second_dir / "status.v1.json").read_bytes()
    assert (first_dir / "figures" / "canonical_status.svg").read_bytes() == (
        second_dir / "figures" / "canonical_status.svg"
    ).read_bytes()
    data = json.loads((first_dir / "status.v1.json").read_text(encoding="utf-8"))
    assert data["current_state"]["status"] == "no_validated_incumbent"
    assert data["historical_comparison"]["leader_candidate_id"] == (
        "004-reimbursement-forensics"
    )
    markdown = (first_dir / "README.md").read_text(encoding="utf-8")
    assert "best corrected historical candidate and counts as a win" in markdown
    assert "original emitted gold was wrong" in markdown
    assert "Gemini 3.7 Flash high 30/30" in markdown
    assert "CloudSLA-Forensics" in markdown
    assert "Gemini returned invalid output" not in markdown
    svg = (first_dir / "figures" / "canonical_status.svg").read_text(encoding="utf-8")
    assert "Gemini 3.7 solved all three Experiment 010 candidates at 30/30" in svg
    assert "CloudSLA-Forensics was valid" in svg
    assert "Opus still did not complete 2/3" in svg
    assert "Gemini returned invalid output" not in svg
