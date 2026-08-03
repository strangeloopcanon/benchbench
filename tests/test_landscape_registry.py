import hashlib
import json
from pathlib import Path

import pytest

from scripts.build_benchmark_landscape_pack import ROOT, registry_landscape_sources, registry_run_roots


def test_only_explicit_historical_diagnostics_feed_the_local_landscape() -> None:
    assert [path.relative_to(ROOT).as_posix() for path in registry_run_roots()] == [
        "experiments/001_three_model_grid_pilot/run",
        "experiments/002_broad_sweep_20260515_220653/run",
    ]


def test_local_landscape_uses_exact_digest_verified_score_set() -> None:
    sources = registry_landscape_sources()
    assert sum(len(source["score_paths"]) for source in sources) == 23
    assert all(path.is_file() for source in sources for path in source["score_paths"])


def _write_landscape_fixture(root: Path, *, duplicate_entry: bool = False) -> Path:
    run = root / "experiments" / "fixture" / "run" / "candidate"
    run.mkdir(parents=True)
    spec = run / "benchmark_spec.json"
    score = run / "score_solver_gpt_5_6_sol.json"
    spec.write_text('{"name":"fixture"}\n', encoding="utf-8")
    score.write_text('{"schema_version":2,"total":1,"correct":1,"accuracy":1.0}\n', encoding="utf-8")

    def item(role: str, path: Path) -> dict[str, str]:
        return {
            "role": role,
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    files = [item("benchmark_spec", spec), item("score", score)]
    if duplicate_entry:
        files.append(item("score", score))
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "benchbench.landscape-evidence/v1",
                "experiment_id": "fixture",
                "run_path": "experiments/fixture/run",
                "files": files,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry = root / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "schema_version": "benchbench.experiment-registry/v1",
                "experiments": [
                    {
                        "id": "fixture",
                        "run_path": "experiments/fixture",
                        "outcome": "historical_noncanonical",
                        "include_in_landscape": True,
                        "landscape_evidence": {
                            "path": "manifest.json",
                            "sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                        },
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return registry


def test_landscape_manifest_rejects_duplicate_evidence_entries(tmp_path: Path) -> None:
    registry = _write_landscape_fixture(tmp_path, duplicate_entry=True)
    with pytest.raises(ValueError, match="duplicate landscape evidence entry"):
        registry_landscape_sources(registry, root=tmp_path)


def test_landscape_registry_rejects_reused_run_paths(tmp_path: Path) -> None:
    registry_path = _write_landscape_fixture(tmp_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    first = registry["experiments"][0]
    manifest_two = tmp_path / "manifest-two.json"
    manifest_data = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    manifest_data["experiment_id"] = "fixture-two"
    manifest_two.write_text(json.dumps(manifest_data) + "\n", encoding="utf-8")
    second = dict(first)
    second["id"] = "fixture-two"
    second["landscape_evidence"] = {
        "path": "manifest-two.json",
        "sha256": hashlib.sha256(manifest_two.read_bytes()).hexdigest(),
    }
    registry["experiments"].append(second)
    registry_path.write_text(json.dumps(registry) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="run path is reused"):
        registry_landscape_sources(registry_path, root=tmp_path)
