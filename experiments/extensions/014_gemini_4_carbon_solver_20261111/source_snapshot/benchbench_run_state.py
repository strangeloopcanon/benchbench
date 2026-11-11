"""Immutable run-root and score-publication helpers."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


def config_fingerprint(config: dict[str, Any]) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


SOURCE_SNAPSHOT_SCHEMA = "benchbench.source_snapshot/v1"


def _validated_relative_path(relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"source snapshot path must be relative and contained: {relative!r}")
    return path


def _source_entries(source_root: Path, relative_paths: tuple[str, ...]) -> list[dict[str, Any]]:
    root = source_root.resolve()
    entries: list[dict[str, Any]] = []
    for relative in sorted(set(relative_paths)):
        rel_path = _validated_relative_path(relative)
        source = source_root / rel_path
        if source.is_symlink() or not source.is_file() or root not in source.resolve().parents:
            raise ValueError(f"source snapshot entry is not a contained regular file: {relative}")
        content = source.read_bytes()
        entries.append(
            {
                "path": rel_path.as_posix(),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return entries


def source_snapshot_digest(source_root: Path, relative_paths: tuple[str, ...]) -> str:
    """Digest an explicit, credential-free source allowlist."""

    entries = _source_entries(source_root, relative_paths)
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def create_source_snapshot(
    source_root: Path,
    run_root: Path,
    relative_paths: tuple[str, ...],
) -> dict[str, Any]:
    """Copy the exact controller harness allowlist into a new run root."""

    entries = _source_entries(source_root, relative_paths)
    digest = hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    destination = run_root / "source_snapshot"
    if destination.exists():
        raise RuntimeError(f"Source snapshot already exists: {destination}")
    staged = Path(tempfile.mkdtemp(prefix=".source_snapshot.", dir=run_root))
    try:
        for entry in entries:
            relative = Path(entry["path"])
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            source = source_root / relative
            if source.is_symlink():
                raise ValueError(f"source snapshot entry became a symbolic link: {relative}")
            content = source.read_bytes()
            if len(content) != entry["bytes"] or hashlib.sha256(content).hexdigest() != entry["sha256"]:
                raise RuntimeError(f"source snapshot entry changed while copying: {relative}")
            target.write_bytes(content)
        manifest = {
            "schema_version": SOURCE_SNAPSHOT_SCHEMA,
            "digest": digest,
            "files": entries,
        }
        (staged / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(staged, destination)
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    return {
        "schema_version": SOURCE_SNAPSHOT_SCHEMA,
        "path": "source_snapshot",
        "manifest_path": "source_snapshot/manifest.json",
        "digest": digest,
        "file_count": len(entries),
    }


def verify_source_snapshot(run_root: Path, expected_digest: str | None = None) -> dict[str, Any]:
    """Verify a controller source snapshot and reject extra or altered files."""

    snapshot_root = run_root / "source_snapshot"
    manifest_path = snapshot_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SOURCE_SNAPSHOT_SCHEMA:
        raise ValueError("unsupported source snapshot schema")
    files = manifest.get("files")
    if not isinstance(files, list) or not all(isinstance(item, dict) for item in files):
        raise ValueError("source snapshot manifest files must be a list of objects")
    declared_paths = {str(item.get("path")) for item in files}
    actual_paths: set[str] = set()
    for path in snapshot_root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"source snapshot contains symbolic link: {path}")
        if path.is_file() and path != manifest_path:
            actual_paths.add(path.relative_to(snapshot_root).as_posix())
    if declared_paths != actual_paths:
        raise ValueError("source snapshot file set does not match its manifest")
    verified_entries: list[dict[str, Any]] = []
    for item in files:
        relative = _validated_relative_path(str(item.get("path")))
        content = (snapshot_root / relative).read_bytes()
        entry = {
            "path": relative.as_posix(),
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        if entry != item:
            raise ValueError(f"source snapshot digest mismatch: {relative.as_posix()}")
        verified_entries.append(entry)
    digest = hashlib.sha256(
        json.dumps(verified_entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if digest != manifest.get("digest") or (expected_digest is not None and digest != expected_digest):
        raise ValueError("source snapshot bundle digest mismatch")
    return manifest


def record_source_snapshot(run_root: Path, snapshot: dict[str, Any]) -> None:
    """Bind a verified source snapshot to immutable run state."""

    state_path = run_root / "run_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if "source_snapshot" in state:
        raise RuntimeError("run state already contains a source snapshot")
    verify_source_snapshot(run_root, expected_digest=str(snapshot["digest"]))
    state["source_snapshot"] = snapshot
    atomic_write_text(state_path, json.dumps(state, indent=2, sort_keys=True) + "\n")


def call_artifact_id(provider_model_id: str, effort: str) -> str:
    """Identity for an invocation, not merely the provider/model selection."""

    cleaned = "".join(char if char.isalnum() else "_" for char in effort.strip().lower()).strip("_") or "default"
    return f"{provider_model_id}__effort_{cleaned}"


def require_new_run_root(path: Path, config: dict[str, Any], *, resume: bool = False) -> str:
    """Claim a new root once; unsafe reuse is deliberately unsupported."""

    if resume:
        raise RuntimeError("--resume is unavailable until immutable attempt lineage is implemented; refusing unsafe reuse")
    # `mkdir` is the claim operation.  Checking then creating would permit two
    # controllers to both observe an empty path and interleave an experiment.
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.mkdir()
    except FileExistsError as exc:
        raise RuntimeError(f"Run root already exists: {path}; choose a new root") from exc
    fingerprint = config_fingerprint(config)
    state = {"schema_version": 1, "config": config, "config_fingerprint": fingerprint}
    atomic_write_text(path / "run_state.json", json.dumps(state, indent=2, sort_keys=True) + "\n")
    return fingerprint


def score_temp_path(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(prefix=f".{destination.stem}.", suffix=".tmp.json", dir=destination.parent, delete=False)
    handle.close()
    return Path(handle.name)


def publish_atomic(source: Path, destination: Path) -> None:
    """Publish only a verified temporary file; os.replace is atomic per filesystem."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)


def atomic_write_text(destination: Path, content: str) -> None:
    """Write one UTF-8 evidence file without exposing a partial record."""

    staged = score_temp_path(destination)
    try:
        staged.write_text(content, encoding="utf-8")
        publish_atomic(staged, destination)
    finally:
        staged.unlink(missing_ok=True)
