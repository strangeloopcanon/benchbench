import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from benchbench_schema import benchmark_package_digest
from run_existing_solver_extension import (
    charged_tokens,
    extension_budget_allows_call,
    repair_frozen_source_evidence,
    require_missing_source_cell,
    snapshot_candidate,
    source_candidate_dirs,
    verify_frozen_source_evidence,
)


def write_candidate(path: Path) -> None:
    (path / "solver_bundle").mkdir(parents=True)
    (path / "generator.py").write_text("# immutable package\n", encoding="utf-8")
    (path / "gold_private_sample.jsonl").write_text('{"id":"x","answer":"a"}\n', encoding="utf-8")
    (path / "solver_bundle" / "items_private_sample.jsonl").write_text(
        '{"id":"x","prompt":"p"}\n', encoding="utf-8"
    )
    (path / "predictions_solver_old.jsonl").write_text('{"id":"x","answer":"old"}\n', encoding="utf-8")
    (path / "score_solver_old.json").write_text('{"correct":0,"total":1}\n', encoding="utf-8")


class ExtensionIntegrityTests(unittest.TestCase):
    def test_failed_source_cell_requires_explicit_retry_and_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "candidate"
            write_candidate(artifact)
            manifest = [
                {
                    "phase": "solver",
                    "creator_model": "creator",
                    "solver_artifact_id": "solver",
                    "cell_state": "invalid_output",
                    "returncode": 0,
                }
            ]
            with self.assertRaises(ValueError):
                require_missing_source_cell(manifest, "creator", artifact, "solver")
            require_missing_source_cell(
                manifest,
                "creator",
                artifact,
                "solver",
                allow_failed_retry=True,
            )
            result_dir = artifact.parent / "solver_results"
            result_dir.mkdir()
            (result_dir / "score_solver_solver.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                require_missing_source_cell(
                    manifest,
                    "creator",
                    artifact,
                    "solver",
                    allow_failed_retry=True,
                )

    def test_unknown_telemetry_is_charged_by_reservation(self) -> None:
        manifest = [{"tokens_used": 100}, {"tokens_used": 0}]
        self.assertEqual(charged_tokens(manifest, 5_000_000), 5_000_100)
        self.assertTrue(extension_budget_allows_call(manifest, 6_000_000, 5_000_000))
        self.assertFalse(extension_budget_allows_call(manifest, 5_000_000, 5_000_000))

    def test_snapshot_preserves_source_and_excludes_old_solver_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            write_candidate(source)
            before = {path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()}
            before_digest = benchmark_package_digest(source)

            snapshot = snapshot_candidate(source, root / "overlay", "gpt-5.4")

            after = {path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()}
            self.assertEqual(before, after)
            self.assertNotEqual(before_digest, benchmark_package_digest(snapshot))
            self.assertEqual(
                (snapshot / "generator.py").read_bytes(),
                (source / "generator.py").read_bytes(),
            )
            self.assertFalse((snapshot / "predictions_solver_old.jsonl").exists())
            self.assertFalse((snapshot / "score_solver_old.json").exists())
            self.assertTrue((snapshot.parent / "source.json").exists())

    def test_source_discovery_resolves_flat_and_active_attempt_layouts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            flat = root / "run" / "candidate_created_by_gpt_5_4"
            write_candidate(flat)
            modern = root / "run" / "candidate_created_by_codex__gpt_5_6_sol__effort_high"
            artifact = modern / "attempt_0001" / "artifact"
            write_candidate(artifact)
            (modern / "active").symlink_to("attempt_0001/artifact", target_is_directory=True)

            found = source_candidate_dirs(root, None)

            self.assertEqual([name for name, _ in found], ["gpt-5.6-sol", "gpt-5.4"])
            self.assertEqual(found[0][1], artifact.resolve())

    def test_source_evidence_repair_separates_source_manifest_from_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            source_manifest = source / "manifest.json"
            source_manifest.write_text('[{"phase":"solver"}]\n', encoding="utf-8")
            source_hash = hashlib.sha256(source_manifest.read_bytes()).hexdigest()
            overlay = root / "overlay"
            evidence = overlay / "source_evidence"
            evidence.mkdir(parents=True)
            source_state = evidence / "run_state.json"
            source_state.write_text('{"schema_version":1}\n', encoding="utf-8")
            source_state_hash = hashlib.sha256(source_state.read_bytes()).hexdigest()
            (overlay / "run_state.json").write_text(
                json.dumps({"config": {"source_manifest_sha256": source_hash}}) + "\n",
                encoding="utf-8",
            )
            (evidence / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "files": [
                            {"path": "source_evidence/run_state.json", "sha256": source_state_hash},
                            {"path": "source_evidence/manifest.json", "sha256": source_hash},
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            repaired = repair_frozen_source_evidence(overlay, source)

            self.assertEqual(
                {item["path"] for item in repaired["files"]},
                {"source_evidence/run_state.json", "source_evidence/source_manifest.json"},
            )
            self.assertEqual(
                hashlib.sha256((evidence / "source_manifest.json").read_bytes()).hexdigest(),
                source_hash,
            )
            self.assertEqual(verify_frozen_source_evidence(overlay), repaired)


if __name__ == "__main__":
    unittest.main()
