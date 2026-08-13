import hashlib
import json
from pathlib import Path

from benchbench_run_state import config_fingerprint
from benchbench_schema import benchmark_package_digest
from scripts.prepare_public_evidence import (
    rebind_controller_validation,
    rebind_run_state_fingerprint,
)


def test_public_rebinding_preserves_validation_and_run_state_integrity(tmp_path: Path) -> None:
    attempt = tmp_path / "candidate_created_by_model" / "attempt_0001"
    artifact = attempt / "artifact"
    artifact.mkdir(parents=True)
    (artifact / "README.md").write_text("portable artifact\n", encoding="utf-8")
    report = attempt / "controller_validation_report.txt"
    report.write_text("portable report\n", encoding="utf-8")
    validation = attempt / "controller_validation.v1.json"
    validation.write_text(
        json.dumps(
            {
                "schema_version": "benchbench.validation/v1",
                "valid": True,
                "candidate_digest": "stale",
                "report_sha256": "stale",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    state_path = tmp_path / "run_state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "config": {"source_run_root": "./experiments/source"},
                "config_fingerprint": "stale",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    rebind_controller_validation(validation)
    rebind_run_state_fingerprint(state_path)

    rebound_validation = json.loads(validation.read_text(encoding="utf-8"))
    rebound_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert rebound_validation["candidate_digest"] == benchmark_package_digest(artifact)
    assert rebound_validation["report_sha256"] == hashlib.sha256(report.read_bytes()).hexdigest()
    assert rebound_state["config_fingerprint"] == config_fingerprint(rebound_state["config"])
