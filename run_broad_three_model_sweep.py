#!/usr/bin/env python3
"""Broad BenchBench creator/solver sweep.

This run intentionally avoids steering creators toward any specific modality or
task family. Creators get benchmark landscape notes and prior pilot outcomes,
then must decide what benchmark to build.
"""

from __future__ import annotations

import datetime as dt
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from benchbench_model_backends import ModelSpec, effective_effort, parse_model_spec, preflight_model, provider_binary, run_model, safe_name
from benchbench_run_state import (
    atomic_write_text,
    call_artifact_id,
    create_source_snapshot,
    publish_atomic,
    record_source_snapshot,
    require_new_run_root,
    score_temp_path,
    source_snapshot_digest,
)
from benchbench_sandbox import SandboxUnavailable, isolated_provider_path, run_generated_command
from benchbench_schema import benchmark_package_digest, bundle_leaks, generated_payload_digest, validate_answer_rows, validate_artifact_tree, validate_item_rows
from benchbench_results import (
    candidate_title,
    extract_solver_predictions,
    read_jsonl,
    score_summary,
    write_jsonl,
)


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "experiments" / f"002_broad_sweep_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
RUN_DIR = RUN_ROOT / "run"
PYTHON = shutil.which("python") or shutil.which("python3") or "python3"
# Use the controller's environment so generated benchmarks have the locked
# dependencies they declare.  The Seatbelt profile grants only this Python
# runtime, never the surrounding home directory.
SANDBOX_PYTHON = str(Path(PYTHON).resolve())

DEFAULT_MODELS = [
    "gpt-5.6-sol@high",
    "gpt-5.6-terra@xhigh",
    "agy:gemini-3.6-flash-high@high",
    "cursor:claude-opus-5@high",
]
FRONTIER_FOUR_POLICY = "benchbench.frontier-four/2026-08-01"
MODELS = DEFAULT_MODELS[:]
CREATOR_MODELS = DEFAULT_MODELS[:]
MODEL_SPECS = [parse_model_spec(model) for model in MODELS]
CREATOR_SPECS = [parse_model_spec(model) for model in CREATOR_MODELS]
CREATOR_EFFORT = "high"
SOLVER_EFFORT = "high"
CREATOR_TIMEOUT_SECONDS = 2400
SOLVER_TIMEOUT_SECONDS = 1500
SAMPLE_COUNT = 30
GENERATION_SEED = 20260516

SOURCE_SNAPSHOT_FILES = (
    "benchbench_model_backends.py",
    "benchbench_results.py",
    "benchbench_run_state.py",
    "benchbench_sandbox.py",
    "benchbench_schema.py",
    "pyproject.toml",
    "requirements.txt",
    "run_broad_three_model_sweep.py",
    "uv.lock",
)


def read_text(path: Path, limit: int | None = None) -> str:
    text = path.read_text(encoding="utf-8")
    return text[:limit] if limit else text


def read_prompt_input(path: Path, limit: int) -> tuple[str, str]:
    """Read prompt text once and hash exactly the bytes injected into calls."""

    text = path.read_text(encoding="utf-8")[:limit]
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def harness_digest() -> str:
    return source_snapshot_digest(ROOT, SOURCE_SNAPSHOT_FILES)


def reported_tokens(manifest: list[dict[str, Any]]) -> int:
    return sum(int(item.get("tokens_used") or 0) for item in manifest)


def charged_tokens(
    manifest: list[dict[str, Any]],
    zero_telemetry_reservation: int = 5_000_000,
) -> int:
    """Return conservative dispatch accounting without inventing usage telemetry."""

    return sum(
        int(item.get("tokens_used") or 0) or zero_telemetry_reservation
        for item in manifest
    )


def budget_allows_call(
    manifest: list[dict[str, Any]],
    max_total_tokens: int,
    zero_telemetry_reservation: int = 5_000_000,
) -> bool:
    return charged_tokens(manifest, zero_telemetry_reservation) < max_total_tokens


def compact_text(value: Any, limit: int = 260) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    elif isinstance(value, list):
        text = "; ".join(compact_text(item, limit=limit) for item in value)
    elif isinstance(value, dict):
        preferred = [
            value.get("name"),
            value.get("description"),
            value.get("reason"),
            value.get("why_not_duplicate"),
            value.get("type"),
        ]
        text = " - ".join(str(part) for part in preferred if part)
        if not text:
            text = json.dumps(value, sort_keys=True)
    else:
        text = str(value)
    text = " ".join(text.replace("|", "\\|").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def read_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def first_markdown_paragraph(path: Path, limit: int = 260) -> str:
    if not path.exists():
        return ""
    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if line.startswith(("#", "-", "`", "|")):
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return compact_text(paragraphs[0], limit=limit) if paragraphs else ""


LANDSCAPE_PACK = ROOT / "benchmark_landscape" / "creator_prompt_landscape_pack.md"
LANDSCAPE_CONTEXT_PATH = (
    LANDSCAPE_PACK if LANDSCAPE_PACK.exists() else ROOT / "benchbench_research_notes.md"
)
BENCHMARK_LANDSCAPE, BENCHMARK_LANDSCAPE_DIGEST = read_prompt_input(
    LANDSCAPE_CONTEXT_PATH,
    90000,
)
PILOT_SUMMARY_PATH = ROOT / "experiments" / "001_three_model_grid_pilot" / "README.md"
PILOT_SUMMARY, PILOT_SUMMARY_DIGEST = read_prompt_input(PILOT_SUMMARY_PATH, 12000)
CREATOR_FEEDBACK_CONTEXT = ""
CREATOR_FEEDBACK_CONTEXT_PATH: Path | None = None
CREATOR_FEEDBACK_CONTEXT_DIGEST: str | None = None


CREATOR_PROMPT = """
You are {agent_label} acting as a BenchBench creator.

Your task, in the broadest terms:

Create the best possible new benchmark you can: valid, deterministic or
reliably graded, human-auditable, hard for strong tool-enabled models, and
interesting rather than a near-duplicate of existing evals. You may choose any
domain, modality, artifact type, environment, or scoring method that you can
package and validate in this directory.

External-solvability requirement:

The benchmark must be solvable in principle by a qualified external solver,
including another model or human specialist, using only the public solver
bundle and the stated rules. Do not make a benchmark whose difficulty comes
from being impossible, under-specified, private-keyed, dependent on hidden
generator details, or equivalent to "solve an open research problem." Hard is
good; unknowable is a benchmark-design failure. In `validation_report.md`,
include a short solvability/identifiability argument and describe what evidence
an external solver could use to determine the answers.

You are not being asked to make a visual benchmark. You are not being asked to
choose any particular domain. Use the landscape report and prior pilot only as
evidence about what has been tried and what makes benchmarks good or bad.

Benchmark landscape report:

<<<BENCHMARK_LANDSCAPE
{benchmark_landscape}
BENCHMARK_LANDSCAPE>>>

Prior BenchBench pilot result:

<<<PRIOR_PILOT
{pilot_summary}
PRIOR_PILOT>>>

{feedback_context_block}

Required root files:
- README.md
- benchmark_spec.json
- generator.py
- verifier.py
- scorer.py
- gold_private_sample.jsonl
- validation_report.md
- failure_modes.md

Required isolated solver bundle:
- solver_bundle/SOLVER_MANIFEST.json
- solver_bundle/items_private_sample.jsonl
- solver_bundle/README.md or solver_bundle/solver_packet.md
- any solver-visible assets needed for the task

Execution target:

Your empty artifact directory is:

{artifact_dir}

Use that exact directory as the working directory for every shell command and
file read/write. Some agent CLIs may open a global scratch directory by
default; ignore that scratch directory and build the benchmark package only in
the artifact directory above.

You may use local computation and internet research if useful. Do not browse or
research forever: the output must be a working package.

Strict CLI contract from this directory:
- `{python} generator.py --sample-count 30 --seed {seed} --out-dir .`
- `{python} verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`
- `{python} scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

Data contract:
- gold_private_sample.jsonl rows include exactly `id` and `answer`.
- solver predictions include exactly `id` and `answer`.
- score_report.json must be a JSON object containing `schema_version: 2`,
  integer `total` and `correct` fields, and numeric `accuracy` equal to
  `correct / total`. `correct` is the number of exact item-level matches;
  additional diagnostic fields are allowed.
- solver_bundle/items_private_sample.jsonl must include all item ids and any
  solver-visible asset references relative to solver_bundle.
- The solver bundle must not contain gold answers, generator/verifier/scorer
  code, validation reports, private audit traces, hidden seeds, private solution
  labels, or answer keys.
- `generator.py` must recreate `gold_private_sample.jsonl` and the complete
  `solver_bundle/` from scratch when both are absent; it may not depend on
  stale generated files already being present.

Before finishing:
1. Generate 30 private sample items.
2. Verify the package.
3. Run a gold self-score.
4. Run at least one weak baseline or obvious-shortcut baseline.
5. Check external solvability: explain why the public bundle contains enough
   information for a qualified external solver to solve the items in principle.
6. Inspect the solver bundle for leakage.
7. Write validation_report.md.
8. In README.md or benchmark_spec.json, briefly state what existing benchmarks
   this is closest to and why this package is not merely a duplicate.

BenchBench evaluates you as a benchmark inventor. The solver models will be
allowed to use all available tools and try hard, except they may not inspect
private files outside the isolated solver bundle.
"""


REPAIR_PROMPT = """
You are {agent_label} repairing your BenchBench candidate in place.

The candidate artifact directory is:

{artifact_dir}

Use that exact directory as the working directory for every shell command and
file read/write. Some agent CLIs may open a global scratch directory by
default; ignore that scratch directory and repair the benchmark package only in
the artifact directory above.

The controller validation found problems:

<<<LOCAL_REPORT
{local_report}
LOCAL_REPORT>>>

Fix package validity only: deterministic generation, verifier/scorer CLI,
solver-bundle isolation, JSONL contracts, and validation report. Preserve the
benchmark's intended idea if possible. Regenerate the 30-item sample and rerun
validation commands before finishing. The scorer's output JSON must contain
`schema_version: 2`, integer `total` and `correct`, and numeric `accuracy`
equal to `correct / total`; custom score names do not replace those fields.
"""


SOLVER_PROMPT = """
You are {agent_label} acting as a blind BenchBench solver.

You are in an isolated solver bundle at:

{solver_bundle_path}

Use that exact directory as the working directory for every shell command and
file read/write. Some agent CLIs may open a global scratch directory by
default; ignore that scratch directory and work only in the solver bundle
above.

You may use any local computation, shell scripts, installed packages, OCR,
image processing, code, and internet access if useful. Try your best to solve
the benchmark.

The only forbidden action is inspecting parent directories or files outside this
isolated solver bundle. Do not look for gold files, generators, scorers, private
traces, or answer keys outside this directory.

Read every visible file in this bundle and solve every item.

Return only JSONL, one object per item, with exactly:
{{"id":"...","answer":"..."}}
"""


def make_shifted_wrong_predictions(gold_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    answers: list[Any] = []
    for row in gold_rows:
        answer = row.get("answer")
        if answer not in answers:
            answers.append(answer)
    wrong_rows = []
    for row in gold_rows:
        answer = row.get("answer")
        if len(answers) > 1:
            wrong = answers[(answers.index(answer) + 1) % len(answers)]
        else:
            wrong = "__BENCHBENCH_WRONG__"
        wrong_rows.append({"id": row["id"], "answer": wrong})
    return wrong_rows


def _controller_scratch(candidate_dir: Path) -> tempfile.TemporaryDirectory[str]:
    """Copy a candidate outside the checkout before invoking its code."""

    scratch = tempfile.TemporaryDirectory(prefix="benchbench-controller-")
    target = Path(scratch.name) / "candidate"
    shutil.copytree(candidate_dir, target, ignore=shutil.ignore_patterns("__pycache__", "controller_validation_report.txt"))
    return scratch


def _command_record(args: list[str], completed: subprocess.CompletedProcess[str] | None, error: Exception | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {"args": args}
    if completed is not None:
        # Generated validators and scorers can read private gold.  Their raw
        # output is therefore secret-bearing, even when the command succeeds.
        # Preserve enough evidence to diagnose execution without publishing
        # model-controlled bytes into controller reports.
        stdout = completed.stdout.encode("utf-8", errors="replace")
        stderr = completed.stderr.encode("utf-8", errors="replace")
        record.update(
            {
                "returncode": completed.returncode,
                "stdout_bytes": len(stdout),
                "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                "stderr_bytes": len(stderr),
                "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
            }
        )
    if error is not None:
        record["error"] = str(error)
    return record


def _run_generated(args: list[str], scratch: Path, commands: list[dict[str, Any]], timeout: int) -> subprocess.CompletedProcess[str] | None:
    try:
        completed = run_generated_command(args, scratch, timeout=timeout)
    except (SandboxUnavailable, subprocess.TimeoutExpired, OSError) as exc:
        commands.append(_command_record(args, None, exc))
        return None
    commands.append(_command_record(args, completed))
    return completed


def _solvability_evidence(candidate_dir: Path) -> list[str]:
    terms = ("solv", "identifi", "external solver", "qualified", "evidence", "determin")
    sources: list[str] = []
    for rel in ("validation_report.md", "README.md", "benchmark_spec.json"):
        path = candidate_dir / rel
        if not path.exists() or path.stat().st_size > 1_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if len(text) >= 180 and sum(term in text for term in terms) >= 2:
            sources.append(rel)
    return sources


def local_validate(candidate_dir: Path) -> dict[str, Any]:
    """Validate twice in clean sandboxes; never execute the canonical package."""

    report: list[str] = []
    commands: list[dict[str, Any]] = []
    try:
        validate_artifact_tree(candidate_dir)
    except ValueError as exc:
        report.append(f"artifact_tree: invalid: {exc}")
        return {
            "valid": False,
            "bundle_file_count": 0,
            "gold_summary": None,
            "wrong_summary": None,
            "leak_matches": [],
            "candidate_digest": None,
            "deterministic": False,
            "frozen_package_match": False,
            "report": "\n".join(report) + "\n",
        }
    required_root = [
        "README.md",
        "benchmark_spec.json",
        "generator.py",
        "verifier.py",
        "scorer.py",
        "validation_report.md",
        "failure_modes.md",
    ]
    missing_root = [name for name in required_root if not (candidate_dir / name).exists()]
    required_frozen = [
        "gold_private_sample.jsonl",
        "solver_bundle/SOLVER_MANIFEST.json",
        "solver_bundle/items_private_sample.jsonl",
    ]
    missing_bundle = [name for name in required_frozen if not (candidate_dir / name).exists()]
    if not any((candidate_dir / "solver_bundle" / name).exists() for name in ("README.md", "solver_packet.md")):
        missing_bundle.append("solver_bundle/README.md or solver_packet.md")
    report.append(f"missing_root_files: {missing_root if missing_root else 'none'}")
    report.append(f"missing_solver_bundle_files: {missing_bundle if missing_bundle else 'none'}")

    solvability_sources = _solvability_evidence(candidate_dir)
    report.append(
        "external_solvability_evidence: "
        + ("present in " + ", ".join(solvability_sources) if solvability_sources else "not found")
    )

    # The generator owns only the gold sample and complete solver bundle. Its
    # source code and authored research assets remain readable inputs, while
    # every generated output starts absent on each deterministic replay.
    frozen_digest = generated_payload_digest(candidate_dir)
    candidate_digest = benchmark_package_digest(candidate_dir)
    run_digests: list[str] = []
    gold_summary: dict[str, Any] | None = None
    wrong_summary: dict[str, Any] | None = None
    gold_contract_valid = item_contract_valid = verifier_ok = controls_ok = False
    leaks: list[str] = []
    bundle_files: list[str] = []
    for attempt in range(2):
        with _controller_scratch(candidate_dir) as scratch_name:
            scratch = Path(scratch_name) / "candidate"
            # A no-op or partial generator cannot inherit any prior payload.
            shutil.rmtree(scratch / "solver_bundle", ignore_errors=True)
            for rel in ("gold_private_sample.jsonl", "predictions_gold_controller.jsonl", "predictions_wrong_shifted_controller.jsonl", "score_gold_controller.json", "score_wrong_shifted_controller.json"):
                (scratch / rel).unlink(missing_ok=True)
            generator = _run_generated([SANDBOX_PYTHON, "generator.py", "--sample-count", str(SAMPLE_COUNT), "--seed", str(GENERATION_SEED), "--out-dir", "."], scratch, commands, 600)
            if generator is None or generator.returncode != 0:
                report.append(f"generation_attempt_{attempt + 1}: failed")
                continue
            try:
                validate_artifact_tree(scratch)
                required_generated = ("SOLVER_MANIFEST.json", "items_private_sample.jsonl")
                absent = [name for name in required_generated if not (scratch / "solver_bundle" / name).exists()]
                if not any((scratch / "solver_bundle" / name).exists() for name in ("README.md", "solver_packet.md")):
                    absent.append("README.md or solver_packet.md")
                if absent:
                    raise ValueError("missing generated solver bundle files: " + ", ".join(absent))
                gold_rows = validate_answer_rows(scratch / "gold_private_sample.jsonl", count=SAMPLE_COUNT)
                gold_ids = {row["id"] for row in gold_rows}
                validate_item_rows(scratch / "solver_bundle" / "items_private_sample.jsonl", count=SAMPLE_COUNT, expected_ids=gold_ids)
                gold_contract_valid = item_contract_valid = True
                leaks = bundle_leaks(scratch / "solver_bundle", gold_rows)
                bundle_files = sorted(str(path.relative_to(scratch / "solver_bundle")) for path in (scratch / "solver_bundle").rglob("*") if path.is_file())
                # Bind validation to the generator-owned payload later handed
                # to solvers. Controller controls are added after this digest.
                run_digests.append(generated_payload_digest(scratch))
                write_jsonl(scratch / "predictions_gold_controller.jsonl", gold_rows)
                write_jsonl(scratch / "predictions_wrong_shifted_controller.jsonl", make_shifted_wrong_predictions(gold_rows))
            except Exception as exc:  # noqa: BLE001
                report.append(f"generation_contract_attempt_{attempt + 1}: {exc}")
                continue
            verifier = _run_generated([SANDBOX_PYTHON, "verifier.py", "--items", "solver_bundle/items_private_sample.jsonl", "--gold", "gold_private_sample.jsonl"], scratch, commands, 420)
            gold_score = _run_generated([SANDBOX_PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_gold_controller.jsonl", "--out", "score_gold_controller.json"], scratch, commands, 420)
            wrong_score = _run_generated([SANDBOX_PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_wrong_shifted_controller.jsonl", "--out", "score_wrong_shifted_controller.json"], scratch, commands, 420)
            verifier_ok = verifier is not None and verifier.returncode == 0
            try:
                gold_summary = score_summary(scratch / "score_gold_controller.json", allow_legacy=False) if gold_score and gold_score.returncode == 0 else None
                wrong_summary = score_summary(scratch / "score_wrong_shifted_controller.json", allow_legacy=False) if wrong_score and wrong_score.returncode == 0 else None
            except ValueError as exc:
                report.append(f"score_parse_attempt_{attempt + 1}: {exc}")
            controls_ok = bool(gold_summary and wrong_summary and gold_summary.get("total") == SAMPLE_COUNT and gold_summary.get("correct") == SAMPLE_COUNT and wrong_summary.get("total") == SAMPLE_COUNT and wrong_summary.get("correct") == 0)

    deterministic = len(run_digests) == 2 and run_digests[0] == run_digests[1]
    frozen_package_match = deterministic and run_digests[0] == frozen_digest
    report.append(f"deterministic_generated_payload_digest: {deterministic}; digests={run_digests}")
    report.append(f"frozen_generated_payload_digest_match: {frozen_package_match}; frozen_digest={frozen_digest}")
    report.append(f"solver_bundle_file_count: {len(bundle_files)}")
    report.append("leak_scan_matches: " + ("none" if not leaks else ", ".join(leaks[:80])))
    if gold_summary:
        report.append(f"score_gold_controller: {json.dumps(gold_summary, sort_keys=True)}")
    else:
        report.append("score_gold_controller: missing or not normalizable; require total, correct, and accuracy")
    if wrong_summary:
        report.append(f"score_wrong_shifted_controller: {json.dumps(wrong_summary, sort_keys=True)}")
    else:
        report.append("score_wrong_shifted_controller: missing or not normalizable; require total, correct, and accuracy")

    valid = (
        not missing_root
        and not missing_bundle
        and gold_contract_valid
        and item_contract_valid
        and verifier_ok
        and controls_ok
        and deterministic
        and frozen_package_match
        and bool(solvability_sources)
        and not leaks
    )

    text_report = "\n".join(report) + "\n\ncommands:\n" + json.dumps(commands, indent=2) + "\n"
    return {
        "valid": valid,
        "bundle_file_count": len(bundle_files),
        "gold_summary": gold_summary,
        "wrong_summary": wrong_summary,
        "leak_matches": leaks,
        "candidate_digest": candidate_digest,
        "generated_payload_digest": frozen_digest,
        "deterministic": deterministic,
        "frozen_package_match": frozen_package_match,
        "report": text_report,
    }


def write_validation_evidence(candidate_dir: Path, validation: dict[str, Any]) -> Path:
    """Store controller evidence beside, never inside, an immutable artifact."""

    report_path = candidate_dir.parent / "controller_validation_report.txt"
    atomic_write_text(report_path, str(validation.get("report") or ""))
    record = {
        "schema_version": "benchbench.validation/v1",
        "valid": validation.get("valid") is True,
        "candidate_digest": validation.get("candidate_digest"),
        "deterministic": validation.get("deterministic") is True,
        "frozen_package_match": validation.get("frozen_package_match") is True,
        "bundle_file_count": int(validation.get("bundle_file_count") or 0),
        "gold_summary": validation.get("gold_summary"),
        "wrong_summary": validation.get("wrong_summary"),
        "leak_match_count": len(validation.get("leak_matches") or []),
        "report_sha256": _file_digest(report_path),
    }
    record_path = candidate_dir.parent / "controller_validation.v1.json"
    atomic_write_text(record_path, json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record_path


def freeze_call_evidence(result: dict[str, Any], evidence_dir: Path) -> None:
    """Copy provider sidecars out of disposable workspaces and rewrite paths."""

    evidence_dir.mkdir(parents=True, exist_ok=True)
    for key, value in list(result.items()):
        if key == "out_path" or not key.endswith("_path") or not isinstance(value, str):
            continue
        source = Path(value)
        if not source.is_file():
            continue
        suffix = "".join(source.suffixes) or ".txt"
        destination = evidence_dir / f"{key.removesuffix('_path')}{suffix}"
        shutil.copy2(source, destination)
        result[key] = str(destination)


def run_creator_attempt(spec: ModelSpec, prompt: str, raw_destination: Path, evidence_artifact: Path, effort: str, timeout: int, seed_artifact: Path | None = None) -> dict[str, Any]:
    """Run a creator outside the checkout, then freeze its complete attempt."""

    with tempfile.TemporaryDirectory(prefix=f"benchbench-creator-{spec.artifact_id}-") as temporary:
        temporary_root = Path(temporary)
        artifact = temporary_root / "artifact"
        if seed_artifact is None:
            artifact.mkdir()
        else:
            shutil.copytree(seed_artifact, artifact)
        raw_temp = temporary_root / "model_output.txt"
        prompt = prompt.replace(str(evidence_artifact), str(artifact))
        try:
            with isolated_provider_path(provider_binary(spec), temporary_root):
                result = run_model(spec, prompt, raw_temp, artifact, effort, timeout)
        except Exception as exc:  # fail closed and preserve the attempted snapshot
            result = {
                "model": spec.name,
                "display_model": spec.display_name,
                "provider": spec.provider,
                "artifact_id": spec.artifact_id,
                "returncode": -124 if isinstance(exc, subprocess.TimeoutExpired) else 70,
                "tokens_used": 0,
                "call_state": "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "sandbox_error",
                "call_error": str(exc),
                "out_path": str(raw_temp),
                "effort": effort,
            }
        freeze_call_evidence(result, raw_destination.parent / "call_evidence" / raw_destination.stem)
        evidence_artifact.parent.mkdir(parents=True, exist_ok=True)
        try:
            tree_limits = validate_artifact_tree(artifact)
            shutil.copytree(artifact, evidence_artifact)
            result["artifact_tree"] = tree_limits
        except ValueError as exc:
            provider_returncode = result.get("returncode")
            evidence_artifact.mkdir()
            rejection_path = evidence_artifact.parent / "artifact_rejection.json"
            rejection_path.write_text(
                json.dumps({"state": "unsafe_artifact", "error": str(exc)}, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result.update(
                {
                    "provider_returncode": provider_returncode,
                    "returncode": 74,
                    "call_state": "unsafe_artifact",
                    "call_error": str(exc),
                    "artifact_rejection_path": str(rejection_path),
                }
            )
        if raw_temp.exists():
            shutil.copy2(raw_temp, raw_destination)
        result["out_path"] = str(raw_destination)
        result["artifact_snapshot"] = str(evidence_artifact)
        return result


def set_active_attempt(candidate_root: Path, artifact: Path) -> None:
    active = candidate_root / "active"
    active.unlink(missing_ok=True)
    active.symlink_to(artifact.relative_to(candidate_root), target_is_directory=True)


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_score_record(
    summary: dict[str, Any],
    candidate_dir: Path,
    prediction_path: Path,
    invocation_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "total": int(summary["total"]),
        "correct": int(summary["correct"]),
        "accuracy": float(summary["accuracy"]),
        "invocation_id": invocation_id,
        "candidate_digest": benchmark_package_digest(candidate_dir),
        "gold_digest": _file_digest(candidate_dir / "gold_private_sample.jsonl"),
        "prediction_digest": _file_digest(prediction_path),
    }


def solver_result_dir(candidate_dir: Path) -> Path:
    """Return controller-owned result storage outside the creator artifact."""

    if candidate_dir.name == "artifact":
        if candidate_dir.parent.name.startswith("attempt_"):
            return candidate_dir.parent.parent / "solver_results"
        return candidate_dir.parent / "solver_results"
    # Even legacy/fixture layouts must never place controller evidence inside
    # the creator-authored benchmark package.
    return candidate_dir.parent / "solver_results"


def verified_normalized_score(
    score_path: Path,
    candidate_dir: Path,
    prediction_path: Path,
    invocation_id: str,
) -> dict[str, Any] | None:
    if not score_path.is_file() or not prediction_path.is_file():
        return None
    try:
        raw = json.loads(score_path.read_text(encoding="utf-8"))
        summary = score_summary(score_path, allow_legacy=False)
        if (
            summary is None
            or raw.get("invocation_id") != invocation_id
            or raw.get("candidate_digest") != benchmark_package_digest(candidate_dir)
            or raw.get("gold_digest") != _file_digest(candidate_dir / "gold_private_sample.jsonl")
            or raw.get("prediction_digest") != _file_digest(prediction_path)
        ):
            return None
        return summary
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def run_solver(creator_model: str, solver_spec: ModelSpec, candidate_dir: Path) -> dict[str, Any]:
    """Run a blind solver in a disposable bundle and publish only valid cells."""

    solver_effort = effective_effort(solver_spec, SOLVER_EFFORT)
    solver_call_id = call_artifact_id(solver_spec.artifact_id, solver_effort)
    slug = f"{safe_name(creator_model)}__solved_by__{solver_call_id}"
    raw_destination = RUN_DIR / f"solver_{slug}.txt"
    result_dir = solver_result_dir(candidate_dir)
    predictions_path = result_dir / f"predictions_solver_{solver_call_id}.jsonl"
    score_path = result_dir / f"score_solver_{solver_call_id}.json"
    base: dict[str, Any] = {
        "phase": "solver", "creator_model": creator_model, "solver_model": solver_spec.name,
        "solver_display_model": solver_spec.display_name, "solver_artifact_id": solver_call_id,
        "prediction_rows": None, "predictions_path": str(predictions_path), "score_path": str(score_path),
        "score_summary": None, "score_returncode": None,
        "tokens_used": 0, "returncode": None,
    }
    if predictions_path.exists() or score_path.exists() or score_path.with_suffix(".raw.txt").exists():
        return {
            **base,
            "cell_state": "existing_attempt",
            "cell_error": "Refusing to overwrite controller-owned solver evidence",
        }
    with tempfile.TemporaryDirectory(prefix=f"benchbench-solver-{slug}-") as temp:
        temp_root = Path(temp)
        solver_dir = temp_root / "solver_bundle"
        shutil.copytree(candidate_dir / "solver_bundle", solver_dir)
        try:
            item_rows = validate_item_rows(solver_dir / "items_private_sample.jsonl", count=SAMPLE_COUNT)
        except Exception as exc:  # noqa: BLE001
            return {**base, "cell_state": "invalid_bundle", "cell_error": str(exc), "returncode": None}
        item_ids = [row["id"] for row in item_rows]
        raw_temp = temp_root / "model_output.txt"
        try:
            with isolated_provider_path(provider_binary(solver_spec), temp_root):
                result = run_model(solver_spec, SOLVER_PROMPT.format(agent_label=solver_spec.agent_label, solver_bundle_path=solver_dir), raw_temp, solver_dir, solver_effort, SOLVER_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            return {**base, "cell_state": "timeout", "cell_error": str(exc), "returncode": -124}
        except Exception as exc:  # noqa: BLE001
            return {**base, "cell_state": "backend_error", "cell_error": str(exc), "returncode": None}
        if raw_temp.exists():
            raw_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(raw_temp, raw_destination)
        freeze_call_evidence(result, RUN_DIR / "call_evidence" / raw_destination.stem)
        result = {**base, **result}
        result["out_path"] = str(raw_destination)
        if result.get("returncode") != 0:
            result["cell_state"] = "timeout" if result.get("returncode") == -124 else "backend_error"
            return result
        if result.get("model_mismatch"):
            result["cell_state"] = "model_mismatch"
            return result
        try:
            predictions, prediction_source = extract_solver_predictions(raw_temp, solver_dir, item_ids)
            # Extraction must not turn a malformed/partial answer into a 0 score.
            temp_predictions = temp_root / "predictions.jsonl"
            write_jsonl(temp_predictions, predictions)
            validate_answer_rows(temp_predictions, expected_ids=set(item_ids), count=SAMPLE_COUNT)
        except Exception as exc:  # noqa: BLE001
            result.update({"cell_state": "invalid_output", "cell_error": str(exc), "prediction_rows": None})
            return result
        result.update(
            {
                "prediction_rows": len(predictions),
                "prediction_source": str(predictions_path),
                "prediction_extraction_source": (
                    "solver_bundle_file" if Path(prediction_source) != raw_temp else "provider_output"
                ),
            }
        )
        with _controller_scratch(candidate_dir) as scoring_name:
            scoring_dir = Path(scoring_name) / "candidate"
            scoring_predictions = scoring_dir / "predictions.jsonl"
            shutil.copy2(temp_predictions, scoring_predictions)
            score_temp = scoring_dir / "score.tmp.json"
            completed = _run_generated([SANDBOX_PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions.jsonl", "--out", "score.tmp.json"], scoring_dir, [], 420)
            if completed is None or completed.returncode != 0 or not score_temp.exists():
                result.update({"cell_state": "scorer_error", "score_returncode": None if completed is None else completed.returncode})
                return result
            try:
                summary = score_summary(score_temp, allow_legacy=False)
                if not summary or summary.get("total") != SAMPLE_COUNT or not isinstance(summary.get("correct"), int) or not 0 <= summary["correct"] <= SAMPLE_COUNT:
                    raise ValueError("scorer did not emit a complete bounded score")
            except Exception as exc:  # noqa: BLE001
                result.update({"cell_state": "invalid_score", "cell_error": str(exc), "score_returncode": completed.returncode})
                return result
            publish_predictions = score_temp_path(predictions_path)
            try:
                shutil.copy2(temp_predictions, publish_predictions)
                publish_atomic(publish_predictions, predictions_path)
                publish_score = score_temp_path(score_path)
                normalized = normalized_score_record(
                    summary,
                    candidate_dir,
                    temp_predictions,
                    solver_call_id,
                )
                publish_score.write_text(
                    json.dumps(normalized, sort_keys=True)
                    + "\n",
                    encoding="utf-8",
                )
                publish_atomic(publish_score, score_path)
            finally:
                for path in (
                    locals().get("publish_predictions"),
                    locals().get("publish_score"),
                ):
                    if isinstance(path, Path):
                        path.unlink(missing_ok=True)
            result.update(
                {
                    "cell_state": "success",
                    "score_returncode": completed.returncode,
                    "score_summary": summary,
                    "candidate_digest": normalized["candidate_digest"],
                    "gold_digest": normalized["gold_digest"],
                    "prediction_digest": normalized["prediction_digest"],
                }
            )
            return result


def candidate_status(scores: list[dict[str, Any] | None]) -> str:
    typed = any(score is not None and "cell_state" in score for score in scores)
    if any(score is None for score in scores):
        return "incomplete_panel"
    if typed and (len(scores) != len(MODEL_SPECS) or any(not score or score.get("cell_state") != "success" for score in scores)):
        return "incomplete_panel"
    parsed_scores = [score for score in scores if score]
    totals = [int(score["total"]) for score in parsed_scores if score.get("total") is not None]
    corrects = [int(score["correct"]) for score in parsed_scores if score.get("correct") is not None]
    if not totals or not corrects:
        return "no_scores"
    if len(set(totals)) != 1 or totals[0] != SAMPLE_COUNT:
        return "incomplete_panel"
    max_total = max(totals)
    max_correct = max(corrects)
    if max_correct == 0:
        return "solvability_audit"
    if max_total and max_correct >= (0.5 * max_total):
        return "reject"
    return "accept"


def solver_score_cells(candidate_dir: Path) -> tuple[list[str], list[dict[str, Any] | None], str, str]:
    cells: list[str] = []
    scores: list[dict[str, Any] | None] = []
    max_correct: int | None = None
    max_total: int | None = None
    used_legacy_evidence = False
    for solver_spec in MODEL_SPECS:
        invocation_id = call_artifact_id(solver_spec.artifact_id, effective_effort(solver_spec, SOLVER_EFFORT))
        result_dir = solver_result_dir(candidate_dir)
        score_path = result_dir / f"score_solver_{invocation_id}.json"
        prediction_path = result_dir / f"predictions_solver_{invocation_id}.jsonl"
        # Historical runs are immutable and used unqualified names.  They are
        # display-only and never confer a new-run acceptance decision.
        if not score_path.exists():
            score_path = candidate_dir / f"score_solver_{safe_name(solver_spec.name)}.json"
            used_legacy_evidence = score_path.exists() or used_legacy_evidence
            score = score_summary(score_path, allow_legacy=True)
        else:
            score = verified_normalized_score(score_path, candidate_dir, prediction_path, invocation_id)
        scores.append(score)
        if score:
            cells.append(f"{score['correct']}/{score['total']}")
            if max_correct is None or score["correct"] > max_correct:
                max_correct = int(score["correct"])
                max_total = int(score["total"])
        else:
            cells.append("NA")
    max_score = f"{max_correct}/{max_total}" if max_correct is not None and max_total is not None else "NA"
    status = "historical_noncanonical" if used_legacy_evidence else candidate_status(scores)
    return cells, scores, max_score, status


def candidate_card_lines(spec: ModelSpec, candidate_dir: Path, validation: dict[str, Any]) -> list[str]:
    spec_data = read_json_dict(candidate_dir / "benchmark_spec.json")
    title = candidate_title(candidate_dir)
    description = compact_text(
        spec_data.get("description")
        or spec_data.get("task")
        or spec_data.get("task_description")
        or first_markdown_paragraph(candidate_dir / "README.md")
    )
    capability = compact_text(
        spec_data.get("capability_claim")
        or spec_data.get("capabilities_measured")
        or spec_data.get("capability")
        or spec_data.get("modality")
    )
    answer = compact_text(
        spec_data.get("grading_method")
        or spec_data.get("grading")
        or spec_data.get("answer_format")
        or spec_data.get("output_format")
    )
    closest = compact_text(spec_data.get("closest_existing_benchmarks"), limit=360)
    failure_hint = compact_text(first_markdown_paragraph(candidate_dir / "failure_modes.md"), limit=300)
    cells, scores, max_score, status = solver_score_cells(candidate_dir)
    score_text = ", ".join(f"{solver.display_name}: {cell}" for solver, cell in zip(MODEL_SPECS, cells))

    lines = [f"### {spec.display_name}: {title}", ""]
    if description:
        lines.append(f"- What it asks: {description}")
    if capability:
        lines.append(f"- Intended capability: {capability}")
    if answer:
        lines.append(f"- Answer/scoring: {answer}")
    if closest:
        lines.append(f"- Closest existing benchmarks: {closest}")
    if failure_hint:
        lines.append(f"- Creator-anticipated failure modes: {failure_hint}")
    lines.append(f"- Validation: `{validation.get('valid')}`; bundle files: `{validation.get('bundle_file_count')}`; leak scan matches: `{len(validation.get('leak_matches') or [])}`")
    if validation.get("gold_summary"):
        lines.append(f"- Gold control: `{json.dumps(validation['gold_summary'], sort_keys=True)}`")
    if validation.get("wrong_summary"):
        lines.append(f"- Shifted-wrong control: `{json.dumps(validation['wrong_summary'], sort_keys=True)}`")
    if any(scores):
        lines.append(f"- Solver results: {score_text}")
        lines.append(f"- Current read: `{status}`; max score `{max_score}`")
    lines.append("")
    return lines


def mismatch_validation(result: dict[str, Any]) -> dict[str, Any]:
    expected = result.get("antigravity_expected_label")
    actual = result.get("antigravity_actual_label")
    report = f"model_mismatch: expected {expected!r}, saw {actual!r}\n"
    return {
        "valid": False,
        "bundle_file_count": 0,
        "gold_summary": None,
        "wrong_summary": None,
        "leak_matches": [],
        "report": report,
    }


def solver_grid_lines(candidate_dirs: dict[str, Path]) -> list[str]:
    lines: list[str] = []
    solver_headers = [f"solver {spec.display_name}" for spec in MODEL_SPECS]
    lines.append("| creator | benchmark | " + " | ".join(solver_headers) + " | max score | status |")
    lines.append("|---|---|" + "|".join("---:" for _ in MODEL_SPECS) + "|---:|---|")
    for creator_spec in CREATOR_SPECS:
        cdir = candidate_dirs.get(creator_spec.artifact_id)
        if cdir is None:
            continue
        cells, _scores, max_score, status = solver_score_cells(cdir)
        lines.append(
            f"| {creator_spec.display_name} | {candidate_title(cdir)} | "
            + " | ".join(cells)
            + f" | {max_score} | {status} |"
        )
    return lines


def write_feedback_for_next_sweep(validations: dict[str, dict[str, Any]], candidate_dirs: dict[str, Path]) -> None:
    lines: list[str] = [
        "# Feedback For Next BenchBench Sweep",
        "",
        "This file is generated from the current creator/solver sweep state. After the final solver finishes, give it to the next creator models with `--feedback-context`.",
        "",
        "BenchBench is evaluating benchmark invention. The goal is a complete benchmark package that is valid, reproducible, externally solvable in principle, and still hard after strong tool-enabled solvers attack the public solver bundle.",
        "",
        "## Result Grid",
        "",
    ]
    lines.extend(solver_grid_lines(candidate_dirs))
    lines.extend(
        [
            "",
            "## Benchmark Cards",
            "",
            "These cards summarize what each prior benchmark actually asked, not just its name and score.",
            "",
        ]
    )
    for spec in CREATOR_SPECS:
        if spec.artifact_id in candidate_dirs:
            lines.extend(candidate_card_lines(spec, candidate_dirs[spec.artifact_id], validations.get(spec.artifact_id, {})))
    lines.extend(
        [
            "## Lessons For The Next Creator",
            "",
            "- Do not make a clean puzzle where the public packet exposes one obvious parser, simulator, BFS, or brute-force strategy.",
            "- Do not rely on type strictness, hidden labels, private vocabulary, malformed output expectations, or missing public evidence to create low scores.",
            "- Treat all-zero rows as audit warnings, not as automatic benchmark wins.",
            "- Prefer complete but messy public evidence, closed answer contracts, adversarial edge cases, cross-document consistency, and partial recoverability.",
            "- A candidate should be rejected if any strong solver gets 30/30, or if all strong solvers get 0/30 and the public bundle cannot prove external solvability.",
            "",
        ]
    )
    atomic_write_text(RUN_ROOT / "feedback_for_next_sweep.md", "\n".join(lines))


def write_summary(manifest: list[dict[str, Any]], validations: dict[str, dict[str, Any]], candidate_dirs: dict[str, Path]) -> None:
    lines: list[str] = []
    lines.append("# Broad BenchBench Sweep")
    lines.append("")
    if CREATOR_FEEDBACK_CONTEXT_PATH is None:
        lines.append("This run used the broad creator prompt: creators saw benchmark landscape notes and prior pilot outcomes, but were not directed toward any specific domain or modality.")
    else:
        lines.append("This run used the broad creator prompt plus a prior-run failure report: creators saw benchmark landscape notes, prior pilot outcomes, and feedback on how the previous candidates broke.")
    lines.append("")
    lines.append(f"Run root: `{RUN_ROOT}`")
    lines.append(f"Creator models: `{', '.join(spec.name for spec in CREATOR_SPECS)}`")
    lines.append(f"Solver models: `{', '.join(spec.name for spec in MODEL_SPECS)}`")
    lines.append(f"Creator effort: `{CREATOR_EFFORT}`")
    lines.append(f"Solver effort: `{SOLVER_EFFORT}`")
    if CREATOR_FEEDBACK_CONTEXT_PATH is not None:
        lines.append(f"Creator feedback context: `{CREATOR_FEEDBACK_CONTEXT_PATH}`")
    if any(spec.provider == "antigravity" for spec in [*CREATOR_SPECS, *MODEL_SPECS]):
        lines.append("")
        lines.append("Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.")
    lines.append("")
    lines.append("## Benchmark Cards")
    lines.append("")
    for spec in CREATOR_SPECS:
        if spec.artifact_id in candidate_dirs:
            lines.extend(candidate_card_lines(spec, candidate_dirs[spec.artifact_id], validations.get(spec.artifact_id, {})))

    lines.append("## Solver Grid")
    lines.append("")
    lines.extend(solver_grid_lines(candidate_dirs))

    lines.append("")
    lines.append("## Calls")
    lines.append("")
    lines.append("| phase | creator | solver/model | rows | score | tokens | cost | cache read | cache write | returncode |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for item in manifest:
        score = item.get("score_summary") or {}
        score_text = "NA"
        if score:
            score_text = f"{score.get('correct')}/{score.get('total')}"
        lines.append(
            "| {phase} | {creator} | {model} | {rows} | {score} | {tokens} | {cost} | {cache_read} | {cache_write} | {rc} |".format(
                phase=item.get("phase"),
                creator=item.get("creator_model", ""),
                model=item.get("solver_display_model", item.get("display_model", item.get("solver_model", item.get("model", "")))),
                rows=item.get("prediction_rows", ""),
                score=score_text,
                tokens=item.get("tokens_used", 0),
                cost=item.get("claude_total_cost_usd", ""),
                cache_read=item.get("claude_cache_read_input_tokens", item.get("cursor_cache_read_tokens", "")),
                cache_write=item.get("claude_cache_creation_input_tokens", item.get("cursor_cache_write_tokens", "")),
                rc=item.get("returncode"),
            )
        )
    lines.append("")
    lines.append(f"Total reported tokens: `{sum(int(item.get('tokens_used') or 0) for item in manifest)}`")
    claude_cost = sum(float(item.get("claude_total_cost_usd") or 0) for item in manifest)
    if claude_cost:
        lines.append(f"Total reported Claude cost: `${claude_cost:.4f}`")
    lines.append("")
    atomic_write_text(RUN_ROOT / "summary.md", "\n".join(lines) + "\n")
    atomic_write_text(RUN_ROOT / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_feedback_for_next_sweep(validations, candidate_dirs)


def write_manifest(manifest: list[dict[str, Any]]) -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    atomic_write_text(RUN_ROOT / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def resolve_model_lists(
    models: list[str] | None,
    creator_models: list[str] | None,
    solver_models: list[str] | None,
) -> tuple[list[str], list[str]]:
    base_models = models or DEFAULT_MODELS
    return creator_models or base_models, solver_models or base_models


def resolve_panel_policy(
    run_root: Path,
    creator_call_ids: list[str],
    solver_call_ids: list[str],
    default_creator_call_ids: list[str],
    default_solver_call_ids: list[str],
) -> str:
    exact_frontier_four = (
        creator_call_ids == default_creator_call_ids
        and solver_call_ids == default_solver_call_ids
    )
    if run_root.name.startswith("010_") and not exact_frontier_four:
        raise ValueError(
            "Experiment 010 requires the exact benchbench.frontier-four/2026-08-01 creator and solver panels"
        )
    return FRONTIER_FOUR_POLICY if exact_frontier_four else "custom"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a broad BenchBench creator/solver sweep.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help=(
            "Creator and solver model specs when separate panels are not supplied. Unprefixed specs use Codex. "
            "Append @effort for a per-model override. Use agy:gemini-3.6-flash-high or agy:current for Antigravity. "
            "Use claude:sonnet or claude:opus for Claude Code. "
            "Use cursor:claude-opus-5 for Claude Opus 5 through Cursor Agent."
        ),
    )
    parser.add_argument(
        "--creator-models",
        nargs="+",
        default=None,
        help="Creator model specs when the creator and solver panels differ.",
    )
    parser.add_argument(
        "--solver-models",
        nargs="+",
        default=None,
        help="Solver model specs. Defaults to --models, or the default model panel when --models is omitted.",
    )
    parser.add_argument("--run-root", type=Path, default=None, help="Optional output experiment directory.")
    parser.add_argument("--creator-effort", default=CREATOR_EFFORT)
    parser.add_argument("--solver-effort", default=SOLVER_EFFORT)
    parser.add_argument("--creator-timeout-seconds", type=int, default=CREATOR_TIMEOUT_SECONDS)
    parser.add_argument("--solver-timeout-seconds", type=int, default=SOLVER_TIMEOUT_SECONDS)
    parser.add_argument(
        "--feedback-context",
        type=Path,
        default=None,
        help="Optional Markdown/text file appended to creator prompts as feedback from prior runs.",
    )
    parser.add_argument("--preflight-only", action="store_true", help="Check all requested provider CLIs without making model calls.")
    parser.add_argument("--resume", action="store_true", help="Rejected: immutable resume lineage is not implemented yet.")
    parser.add_argument(
        "--max-total-tokens",
        type=int,
        default=int(os.getenv("BENCHBENCH_MAX_TOTAL_TOKENS", "0")),
        help="Required live-run ceiling on reported provider tokens; no new call starts after the ceiling is reached.",
    )
    parser.add_argument(
        "--allow-unmetered-cost",
        action="store_true",
        help="Acknowledge providers without dollar telemetry or a provider-enforced monetary cap.",
    )
    parser.add_argument(
        "--allow-dispatch-ceiling-overshoot",
        action="store_true",
        help="Acknowledge that one in-flight provider call can overshoot the reported-token dispatch ceiling.",
    )
    parser.add_argument(
        "--zero-telemetry-reservation",
        type=int,
        default=5_000_000,
        help="Conservative token charge for a completed call that reports zero telemetry.",
    )
    return parser.parse_args()


def main() -> None:
    global CREATOR_EFFORT, SOLVER_EFFORT, CREATOR_TIMEOUT_SECONDS, SOLVER_TIMEOUT_SECONDS, MODELS, CREATOR_MODELS, MODEL_SPECS, CREATOR_SPECS, RUN_ROOT, RUN_DIR, CREATOR_FEEDBACK_CONTEXT, CREATOR_FEEDBACK_CONTEXT_PATH, CREATOR_FEEDBACK_CONTEXT_DIGEST

    args = parse_args()
    CREATOR_MODELS, MODELS = resolve_model_lists(args.models, args.creator_models, args.solver_models)
    CREATOR_SPECS = [parse_model_spec(model) for model in CREATOR_MODELS]
    MODEL_SPECS = [parse_model_spec(model) for model in MODELS]
    CREATOR_EFFORT = args.creator_effort
    SOLVER_EFFORT = args.solver_effort
    CREATOR_TIMEOUT_SECONDS = args.creator_timeout_seconds
    SOLVER_TIMEOUT_SECONDS = args.solver_timeout_seconds
    if args.feedback_context is not None:
        CREATOR_FEEDBACK_CONTEXT_PATH = args.feedback_context if args.feedback_context.is_absolute() else ROOT / args.feedback_context
        CREATOR_FEEDBACK_CONTEXT, CREATOR_FEEDBACK_CONTEXT_DIGEST = read_prompt_input(
            CREATOR_FEEDBACK_CONTEXT_PATH,
            60000,
        )
    if args.run_root is not None:
        RUN_ROOT = args.run_root if args.run_root.is_absolute() else ROOT / args.run_root
        RUN_DIR = RUN_ROOT / "run"

    # Availability is a provider/model property; effort is validated by the
    # provider catalog and remains part of each eventual call identity.
    unique_specs = {spec.artifact_id: spec for spec in [*CREATOR_SPECS, *MODEL_SPECS]}
    preflight = [preflight_model(spec, ROOT) for spec in unique_specs.values()]
    print(json.dumps({"preflight": preflight}, indent=2, sort_keys=True), flush=True)
    failures = [
        item
        for item in preflight
        if item.get("state") != "binary_ready" or item.get("model_available") is False
    ]
    if args.preflight_only:
        if failures:
            raise SystemExit("Provider preflight failed")
        return
    audited_live_providers = {"codex", "antigravity"}
    unsupported_live = sorted({spec.provider for spec in unique_specs.values() if spec.provider not in audited_live_providers})
    if unsupported_live:
        raise SystemExit(
            "Live execution requires an audited credential boundary; "
            "unsupported providers: " + ", ".join(unsupported_live)
        )
    if failures:
        raise SystemExit("Provider preflight failed; refusing to make creator calls")
    if args.max_total_tokens <= 0:
        raise SystemExit("Live runs require --max-total-tokens (or BENCHBENCH_MAX_TOTAL_TOKENS)")
    if not args.allow_dispatch_ceiling_overshoot:
        raise SystemExit(
            "Provider CLIs cannot enforce one uniform per-call token cap; pass "
            "--allow-dispatch-ceiling-overshoot after approving the worst-case in-flight call"
        )
    if args.zero_telemetry_reservation <= 0:
        raise SystemExit("--zero-telemetry-reservation must be a positive integer")
    unmetered = sorted(
        {spec.provider for spec in unique_specs.values() if spec.provider != "claude"}
    )
    if unmetered and not args.allow_unmetered_cost:
        raise SystemExit(
            "These providers do not expose a harness-enforced dollar cap: "
            + ", ".join(unmetered)
            + "; pass --allow-unmetered-cost after reviewing the token ceiling"
        )
    creator_call_ids = [call_artifact_id(spec.artifact_id, effective_effort(spec, CREATOR_EFFORT)) for spec in CREATOR_SPECS]
    solver_call_ids = [call_artifact_id(spec.artifact_id, effective_effort(spec, SOLVER_EFFORT)) for spec in MODEL_SPECS]
    if len(creator_call_ids) != len(set(creator_call_ids)) or len(solver_call_ids) != len(set(solver_call_ids)):
        raise SystemExit("Duplicate provider/model/effort identity in a declared panel")
    default_specs = [parse_model_spec(value) for value in DEFAULT_MODELS]
    default_creator_call_ids = [
        call_artifact_id(spec.artifact_id, effective_effort(spec, CREATOR_EFFORT))
        for spec in default_specs
    ]
    default_solver_call_ids = [
        call_artifact_id(spec.artifact_id, effective_effort(spec, SOLVER_EFFORT))
        for spec in default_specs
    ]
    try:
        panel_policy = resolve_panel_policy(
            RUN_ROOT,
            creator_call_ids,
            solver_call_ids,
            default_creator_call_ids,
            default_solver_call_ids,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    run_config = {
        "creator_models": creator_call_ids, "solver_models": solver_call_ids,
        "creator_effort": CREATOR_EFFORT, "solver_effort": SOLVER_EFFORT, "generation_seed": GENERATION_SEED,
        "sample_count": SAMPLE_COUNT,
        "creator_timeout_seconds": CREATOR_TIMEOUT_SECONDS,
        "solver_timeout_seconds": SOLVER_TIMEOUT_SECONDS,
        "feedback_digest": CREATOR_FEEDBACK_CONTEXT_DIGEST,
        "landscape_path": str(LANDSCAPE_CONTEXT_PATH.relative_to(ROOT)),
        "landscape_digest": BENCHMARK_LANDSCAPE_DIGEST,
        "pilot_summary_path": str(PILOT_SUMMARY_PATH.relative_to(ROOT)),
        "pilot_summary_digest": PILOT_SUMMARY_DIGEST,
        "harness_digest": harness_digest(),
        "max_total_tokens": args.max_total_tokens,
        "zero_telemetry_reservation": args.zero_telemetry_reservation,
        "dispatch_ceiling_overshoot_acknowledged": args.allow_dispatch_ceiling_overshoot,
        "unmetered_cost_acknowledged": args.allow_unmetered_cost,
        "panel_policy": panel_policy,
        "provider_preflight": preflight,
    }
    try:
        require_new_run_root(RUN_ROOT, run_config, resume=args.resume)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    try:
        source_snapshot = create_source_snapshot(ROOT, RUN_ROOT, SOURCE_SNAPSHOT_FILES)
        if source_snapshot["digest"] != run_config["harness_digest"]:
            raise RuntimeError("controller source changed while the run root was being initialized")
        record_source_snapshot(RUN_ROOT, source_snapshot)
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Failed to freeze controller source snapshot: {exc}") from exc
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    manifest: list[dict[str, Any]] = []
    validations: dict[str, dict[str, Any]] = {}
    candidate_dirs: dict[str, Path] = {}

    for spec in CREATOR_SPECS:
        if not budget_allows_call(manifest, args.max_total_tokens, args.zero_telemetry_reservation):
            print("[budget:stop] charged token ceiling reached before next creator call", flush=True)
            break
        creator_effort = effective_effort(spec, CREATOR_EFFORT)
        slug = call_artifact_id(spec.artifact_id, creator_effort)
        candidate_root = RUN_DIR / f"candidate_created_by_{slug}"
        candidate_dir = candidate_root / "attempt_0001" / "artifact"
        candidate_dirs[spec.artifact_id] = candidate_dir
        print(f"[creator:start] {spec.name}", flush=True)
        creator = run_creator_attempt(
            spec,
            CREATOR_PROMPT.format(
                agent_label=spec.agent_label,
                artifact_dir=candidate_dir,
                benchmark_landscape=BENCHMARK_LANDSCAPE,
                pilot_summary=PILOT_SUMMARY,
                feedback_context_block=(
                    "Feedback from the previous BenchBench run:\n\n"
                    "<<<PRIOR_RUN_FEEDBACK\n"
                    f"{CREATOR_FEEDBACK_CONTEXT}\n"
                    "PRIOR_RUN_FEEDBACK>>>\n"
                    if CREATOR_FEEDBACK_CONTEXT
                    else ""
                ),
                python=SANDBOX_PYTHON,
                seed=GENERATION_SEED,
            ),
            RUN_DIR / f"creator_{slug}.txt",
            candidate_dir,
            creator_effort,
            CREATOR_TIMEOUT_SECONDS,
        )
        creator.update({"phase": "creator", "creator_model": spec.name, "creator_display_model": spec.display_name})
        set_active_attempt(candidate_root, candidate_dir)
        manifest.append(creator)
        write_manifest(manifest)
        print(f"[creator:done] {spec.name} rc={creator['returncode']} tokens={creator['tokens_used']}", flush=True)

        validation = mismatch_validation(creator) if creator.get("model_mismatch") else local_validate(candidate_dir)
        creator["validation_report_path"] = str(write_validation_evidence(candidate_dir, validation))
        validations[spec.artifact_id] = validation
        write_manifest(manifest)
        print(f"[validate] {spec.name} valid={validation['valid']}", flush=True)

        if (
            not validation["valid"]
            and not creator.get("model_mismatch")
            and budget_allows_call(
                manifest,
                args.max_total_tokens,
                args.zero_telemetry_reservation,
            )
        ):
            print(f"[repair:start] {spec.name}", flush=True)
            repair_dir = candidate_root / "attempt_0002" / "artifact"
            repair = run_creator_attempt(
                spec,
                REPAIR_PROMPT.format(
                    agent_label=spec.agent_label,
                    artifact_dir=repair_dir,
                    local_report=validation["report"][:60000],
                ),
                RUN_DIR / f"repair_{slug}.txt",
                repair_dir,
                creator_effort,
                CREATOR_TIMEOUT_SECONDS,
                seed_artifact=candidate_dir,
            )
            repair.update({"phase": "repair", "creator_model": spec.name, "creator_display_model": spec.display_name})
            manifest.append(repair)
            write_manifest(manifest)
            print(f"[repair:done] {spec.name} rc={repair['returncode']} tokens={repair['tokens_used']}", flush=True)
            candidate_dir = repair_dir
            candidate_dirs[spec.artifact_id] = candidate_dir
            set_active_attempt(candidate_root, candidate_dir)
            validation = mismatch_validation(repair) if repair.get("model_mismatch") else local_validate(candidate_dir)
            repair["validation_report_path"] = str(write_validation_evidence(candidate_dir, validation))
            validations[spec.artifact_id] = validation
            write_manifest(manifest)
            print(f"[validate:after_repair] {spec.name} valid={validation['valid']}", flush=True)

    for creator_spec in CREATOR_SPECS:
        candidate_dir = candidate_dirs.get(creator_spec.artifact_id)
        if candidate_dir is None:
            continue
        if not validations.get(creator_spec.artifact_id, {}).get("valid"):
            continue
        for solver_spec in MODEL_SPECS:
            if not budget_allows_call(
                manifest,
                args.max_total_tokens,
                args.zero_telemetry_reservation,
            ):
                print("[budget:stop] charged token ceiling reached before next solver call", flush=True)
                break
            print(f"[solver:start] creator={creator_spec.name} solver={solver_spec.name}", flush=True)
            result = run_solver(creator_spec.name, solver_spec, candidate_dir)
            manifest.append(result)
            write_manifest(manifest)
            write_summary(manifest, validations, candidate_dirs)
            print(
                f"[solver:done] creator={creator_spec.name} solver={solver_spec.name} "
                f"rows={result['prediction_rows']} score={result.get('score_summary')} "
                f"tokens={result['tokens_used']} rc={result['returncode']}",
                flush=True,
            )

    write_summary(manifest, validations, candidate_dirs)
    print(RUN_ROOT / "summary.md", flush=True)


if __name__ == "__main__":
    main()
