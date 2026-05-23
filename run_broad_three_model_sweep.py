#!/usr/bin/env python3
"""Broad BenchBench creator/solver sweep.

This run intentionally avoids steering creators toward any specific modality or
task family. Creators get benchmark landscape notes and prior pilot outcomes,
then must decide what benchmark to build.
"""

from __future__ import annotations

import datetime as dt
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from benchbench_model_backends import ModelSpec, parse_model_spec, run_cmd, run_model, safe_name
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

DEFAULT_MODELS = ["gpt-5.2", "gpt-5.4", "gpt-5.5"]
MODELS = DEFAULT_MODELS[:]
MODEL_SPECS = [parse_model_spec(model) for model in MODELS]
CREATOR_EFFORT = "low"
SOLVER_EFFORT = "low"
CREATOR_TIMEOUT_SECONDS = 2400
SOLVER_TIMEOUT_SECONDS = 1500
SAMPLE_COUNT = 30
GENERATION_SEED = 20260516


def read_text(path: Path, limit: int | None = None) -> str:
    text = path.read_text(encoding="utf-8")
    return text[:limit] if limit else text


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
BENCHMARK_LANDSCAPE = read_text(
    LANDSCAPE_PACK if LANDSCAPE_PACK.exists() else ROOT / "benchbench_research_notes.md",
    limit=90000,
)
PILOT_SUMMARY = read_text(ROOT / "experiments" / "001_three_model_grid_pilot" / "README.md", limit=12000)
CREATOR_FEEDBACK_CONTEXT = ""
CREATOR_FEEDBACK_CONTEXT_PATH: Path | None = None


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
- solver_bundle/items_private_sample.jsonl must include all item ids and any
  solver-visible asset references relative to solver_bundle.
- The solver bundle must not contain gold answers, generator/verifier/scorer
  code, validation reports, private audit traces, hidden seeds, private solution
  labels, or answer keys.

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
validation commands before finishing.
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


def local_validate(candidate_dir: Path) -> dict[str, Any]:
    report: list[str] = []
    commands: list[dict[str, Any]] = []
    required_root = [
        "README.md",
        "benchmark_spec.json",
        "generator.py",
        "verifier.py",
        "scorer.py",
        "gold_private_sample.jsonl",
        "validation_report.md",
        "failure_modes.md",
    ]
    missing_root = [name for name in required_root if not (candidate_dir / name).exists()]
    missing_bundle = [
        name
        for name in ["SOLVER_MANIFEST.json", "items_private_sample.jsonl"]
        if not (candidate_dir / "solver_bundle" / name).exists()
    ]
    if not any((candidate_dir / "solver_bundle" / name).exists() for name in ["README.md", "solver_packet.md"]):
        missing_bundle.append("README.md or solver_packet.md")
    report.append(f"missing_root_files: {missing_root if missing_root else 'none'}")
    report.append(f"missing_solver_bundle_files: {missing_bundle if missing_bundle else 'none'}")

    solvability_terms = ["solvab", "identifi", "external solver", "human", "specialist"]
    solvability_sources = []
    for rel in ["validation_report.md", "README.md", "benchmark_spec.json"]:
        path = candidate_dir / rel
        if not path.exists() or path.stat().st_size > 1_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if any(term in text for term in solvability_terms):
            solvability_sources.append(rel)
    report.append(
        "external_solvability_evidence: "
        + ("present in " + ", ".join(solvability_sources) if solvability_sources else "not found")
    )

    def run_validation_command(args: list[str], timeout: int = 420) -> subprocess.CompletedProcess[str] | None:
        if not (candidate_dir / args[1]).exists():
            commands.append({"args": args, "skipped": True, "reason": f"{args[1]} missing"})
            return None
        try:
            completed = run_cmd(args, candidate_dir, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            commands.append({"args": args, "error": str(exc)})
            return None
        commands.append(
            {
                "args": args,
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-4000:],
                "stderr_tail": completed.stderr[-4000:],
            }
        )
        return completed

    generator = run_validation_command(
        [PYTHON, "generator.py", "--sample-count", str(SAMPLE_COUNT), "--seed", str(GENERATION_SEED), "--out-dir", "."],
        timeout=600,
    )

    gold_rows: list[dict[str, Any]] = []
    gold_contract_valid = False
    gold_path = candidate_dir / "gold_private_sample.jsonl"
    if gold_path.exists():
        try:
            gold_rows = read_jsonl(gold_path)
            write_jsonl(candidate_dir / "predictions_gold_controller.jsonl", [{"id": row["id"], "answer": row["answer"]} for row in gold_rows])
            write_jsonl(candidate_dir / "predictions_wrong_shifted_controller.jsonl", make_shifted_wrong_predictions(gold_rows))
            report.append(f"gold_rows: {len(gold_rows)}")
            gold_keys_ok = all(isinstance(row, dict) and set(row) == {"id", "answer"} for row in gold_rows)
            gold_ids = [str(row["id"]) for row in gold_rows if isinstance(row, dict) and "id" in row]
            gold_ids_unique = len(gold_ids) == len(set(gold_ids))
            gold_contract_valid = gold_keys_ok and gold_ids_unique and len(gold_rows) == SAMPLE_COUNT
            report.append(f"gold_contract_valid: {gold_contract_valid}")
        except Exception as exc:  # noqa: BLE001
            report.append(f"gold_parse_error: {exc}")

    verifier = run_validation_command(
        [PYTHON, "verifier.py", "--items", "solver_bundle/items_private_sample.jsonl", "--gold", "gold_private_sample.jsonl"],
        timeout=420,
    )
    gold_score = run_validation_command(
        [PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_gold_controller.jsonl", "--out", "score_gold_controller.json"],
        timeout=420,
    )
    wrong_score = run_validation_command(
        [
            PYTHON,
            "scorer.py",
            "--gold",
            "gold_private_sample.jsonl",
            "--predictions",
            "predictions_wrong_shifted_controller.jsonl",
            "--out",
            "score_wrong_shifted_controller.json",
        ],
        timeout=420,
    )

    bundle_dir = candidate_dir / "solver_bundle"
    bundle_files: list[str] = []
    item_contract_valid = False
    if bundle_dir.exists():
        bundle_files = sorted(str(path.relative_to(bundle_dir)) for path in bundle_dir.rglob("*") if path.is_file())
        report.append(f"solver_bundle_file_count: {len(bundle_files)}")
        items_path = bundle_dir / "items_private_sample.jsonl"
        if items_path.exists():
            try:
                item_rows = read_jsonl(items_path)
                report.append(f"solver_bundle_item_rows: {len(item_rows)}")
                item_ids = [str(row["id"]) for row in item_rows if isinstance(row, dict) and "id" in row]
                item_ids_unique = len(item_ids) == len(set(item_ids))
                item_ids_match_gold = bool(gold_rows) and set(item_ids) == {str(row["id"]) for row in gold_rows}
                item_contract_valid = (
                    len(item_rows) == SAMPLE_COUNT
                    and len(item_ids) == SAMPLE_COUNT
                    and item_ids_unique
                    and item_ids_match_gold
                )
                report.append(f"solver_bundle_item_contract_valid: {item_contract_valid}")
            except Exception as exc:  # noqa: BLE001
                report.append(f"solver_bundle_item_parse_error: {exc}")

    leak_terms = [
        "gold_private",
        "private_audit",
        "generator.py",
        "verifier.py",
        "scorer.py",
        "correct_answer",
        "solution",
        "answer_key",
        "target_",
        "seed",
    ]
    leaks: list[str] = []
    if bundle_dir.exists():
        for path in bundle_dir.rglob("*"):
            if not path.is_file() or path.stat().st_size > 2_000_000:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            low = text.lower()
            for term in leak_terms:
                if term.lower() in low:
                    leaks.append(f"{path.relative_to(bundle_dir)}:{term}")
    report.append("leak_scan_matches: " + ("none" if not leaks else ", ".join(leaks[:80])))

    gold_summary = score_summary(candidate_dir / "score_gold_controller.json")
    wrong_summary = score_summary(candidate_dir / "score_wrong_shifted_controller.json")
    if gold_summary:
        report.append(f"score_gold_controller: {json.dumps(gold_summary, sort_keys=True)}")
    if wrong_summary:
        report.append(f"score_wrong_shifted_controller: {json.dumps(wrong_summary, sort_keys=True)}")

    valid = (
        not missing_root
        and not missing_bundle
        and generator is not None
        and generator.returncode == 0
        and verifier is not None
        and verifier.returncode == 0
        and gold_score is not None
        and gold_score.returncode == 0
        and gold_summary is not None
        and gold_summary.get("total") == SAMPLE_COUNT
        and gold_summary.get("correct") == SAMPLE_COUNT
        and gold_contract_valid
        and item_contract_valid
    )

    text_report = "\n".join(report) + "\n\ncommands:\n" + json.dumps(commands, indent=2) + "\n"
    (candidate_dir / "controller_validation_report.txt").write_text(text_report, encoding="utf-8")
    return {
        "valid": valid,
        "bundle_file_count": len(bundle_files),
        "gold_summary": gold_summary,
        "wrong_summary": wrong_summary,
        "leak_matches": leaks,
        "report": text_report,
    }


def run_solver(creator_model: str, solver_spec: ModelSpec, candidate_dir: Path) -> dict[str, Any]:
    slug = f"{safe_name(creator_model)}__solved_by__{safe_name(solver_spec.name)}"
    solver_dir = RUN_DIR / f"isolated_solver_{slug}"
    antigravity_temp_dir: Path | None = None
    if solver_spec.provider in {"antigravity", "claude"}:
        antigravity_temp_dir = Path(tempfile.mkdtemp(prefix=f"benchbench_{slug}_"))
        solver_dir = antigravity_temp_dir
        shutil.copytree(candidate_dir / "solver_bundle", solver_dir, dirs_exist_ok=True)
    else:
        if solver_dir.exists():
            shutil.rmtree(solver_dir)
        shutil.copytree(candidate_dir / "solver_bundle", solver_dir)
    item_ids = [str(row["id"]) for row in read_jsonl(solver_dir / "items_private_sample.jsonl")]

    out_path = RUN_DIR / f"solver_{slug}.jsonl"
    result = run_model(
        solver_spec,
        SOLVER_PROMPT.format(agent_label=solver_spec.agent_label, solver_bundle_path=solver_dir),
        out_path,
        solver_dir,
        SOLVER_EFFORT,
        SOLVER_TIMEOUT_SECONDS,
    )
    predictions, prediction_source = (
        ([], str(out_path))
        if result.get("model_mismatch")
        else extract_solver_predictions(out_path, solver_dir, item_ids)
    )
    predictions_path = candidate_dir / f"predictions_solver_{safe_name(solver_spec.name)}.jsonl"
    write_jsonl(predictions_path, predictions)
    score_path = candidate_dir / f"score_solver_{safe_name(solver_spec.name)}.json"
    if result.get("model_mismatch"):
        completed = subprocess.CompletedProcess(
            [], 86, "", "skipped scoring because Antigravity selected-model check failed"
        )
    else:
        completed = run_cmd(
            [
                PYTHON,
                "scorer.py",
                "--gold",
                "gold_private_sample.jsonl",
                "--predictions",
                str(predictions_path),
                "--out",
                str(score_path),
            ],
            candidate_dir,
            timeout=420,
        )
    if antigravity_temp_dir is not None:
        shutil.rmtree(antigravity_temp_dir, ignore_errors=True)
    result.update(
        {
            "phase": "solver",
            "creator_model": creator_model,
            "solver_model": solver_spec.name,
            "solver_display_model": solver_spec.display_name,
            "prediction_rows": len(predictions),
            "prediction_source": prediction_source,
            "predictions_path": str(predictions_path),
            "score_path": str(score_path),
            "score_returncode": completed.returncode,
            "score_stdout": completed.stdout[-4000:],
            "score_stderr": completed.stderr[-4000:],
            "score_summary": score_summary(score_path),
        }
    )
    return result


def candidate_status(scores: list[dict[str, Any] | None]) -> str:
    parsed_scores = [score for score in scores if score]
    if not parsed_scores:
        return "no_scores"
    totals = [int(score["total"]) for score in parsed_scores if score.get("total") is not None]
    corrects = [int(score["correct"]) for score in parsed_scores if score.get("correct") is not None]
    if not totals or not corrects:
        return "no_scores"
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
    for solver_spec in MODEL_SPECS:
        score = score_summary(candidate_dir / f"score_solver_{safe_name(solver_spec.name)}.json")
        scores.append(score)
        if score:
            cells.append(f"{score['correct']}/{score['total']}")
            if max_correct is None or score["correct"] > max_correct:
                max_correct = int(score["correct"])
                max_total = int(score["total"])
        else:
            cells.append("NA")
    max_score = f"{max_correct}/{max_total}" if max_correct is not None and max_total is not None else "NA"
    return cells, scores, max_score, candidate_status(scores)


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
    for creator_spec in MODEL_SPECS:
        cdir = candidate_dirs[creator_spec.name]
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
    for spec in MODEL_SPECS:
        lines.extend(candidate_card_lines(spec, candidate_dirs[spec.name], validations.get(spec.name, {})))
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
    (RUN_ROOT / "feedback_for_next_sweep.md").write_text("\n".join(lines), encoding="utf-8")


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
    lines.append(f"Creator models: `{', '.join(spec.name for spec in MODEL_SPECS)}`")
    lines.append(f"Solver models: `{', '.join(spec.name for spec in MODEL_SPECS)}`")
    lines.append(f"Creator effort: `{CREATOR_EFFORT}`")
    lines.append(f"Solver effort: `{SOLVER_EFFORT}`")
    if CREATOR_FEEDBACK_CONTEXT_PATH is not None:
        lines.append(f"Creator feedback context: `{CREATOR_FEEDBACK_CONTEXT_PATH}`")
    if any(spec.provider == "antigravity" for spec in MODEL_SPECS):
        lines.append("")
        lines.append("Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.")
    lines.append("")
    lines.append("## Benchmark Cards")
    lines.append("")
    for spec in MODEL_SPECS:
        lines.extend(candidate_card_lines(spec, candidate_dirs[spec.name], validations.get(spec.name, {})))

    lines.append("## Solver Grid")
    lines.append("")
    lines.extend(solver_grid_lines(candidate_dirs))

    lines.append("")
    lines.append("## Calls")
    lines.append("")
    lines.append("| phase | creator | solver/model | rows | score | tokens | Claude cost | Claude cache read | returncode |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for item in manifest:
        score = item.get("score_summary") or {}
        score_text = "NA"
        if score:
            score_text = f"{score.get('correct')}/{score.get('total')}"
        lines.append(
            "| {phase} | {creator} | {model} | {rows} | {score} | {tokens} | {cost} | {cache_read} | {rc} |".format(
                phase=item.get("phase"),
                creator=item.get("creator_model", ""),
                model=item.get("solver_display_model", item.get("display_model", item.get("solver_model", item.get("model", "")))),
                rows=item.get("prediction_rows", ""),
                score=score_text,
                tokens=item.get("tokens_used", 0),
                cost=item.get("claude_total_cost_usd", ""),
                cache_read=item.get("claude_cache_read_input_tokens", ""),
                rc=item.get("returncode"),
            )
        )
    lines.append("")
    lines.append(f"Total reported tokens: `{sum(int(item.get('tokens_used') or 0) for item in manifest)}`")
    claude_cost = sum(float(item.get("claude_total_cost_usd") or 0) for item in manifest)
    if claude_cost:
        lines.append(f"Total reported Claude cost: `${claude_cost:.4f}`")
    lines.append("")
    (RUN_ROOT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RUN_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_feedback_for_next_sweep(validations, candidate_dirs)


def write_manifest(manifest: list[dict[str, Any]]) -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    (RUN_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a broad BenchBench creator/solver sweep.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help=(
            "Creator and solver model specs. Unprefixed specs use Codex. "
            "Use agy:gemini-3.5-flash-high, agy:gemini-3.1-pro, or agy:current for Antigravity. "
            "Use claude:sonnet or claude:opus for Claude Code."
        ),
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
    return parser.parse_args()


def main() -> None:
    global CREATOR_EFFORT, SOLVER_EFFORT, CREATOR_TIMEOUT_SECONDS, SOLVER_TIMEOUT_SECONDS, MODELS, MODEL_SPECS, RUN_ROOT, RUN_DIR, CREATOR_FEEDBACK_CONTEXT, CREATOR_FEEDBACK_CONTEXT_PATH

    args = parse_args()
    MODELS = args.models
    MODEL_SPECS = [parse_model_spec(model) for model in MODELS]
    CREATOR_EFFORT = args.creator_effort
    SOLVER_EFFORT = args.solver_effort
    CREATOR_TIMEOUT_SECONDS = args.creator_timeout_seconds
    SOLVER_TIMEOUT_SECONDS = args.solver_timeout_seconds
    if args.feedback_context is not None:
        CREATOR_FEEDBACK_CONTEXT_PATH = args.feedback_context if args.feedback_context.is_absolute() else ROOT / args.feedback_context
        CREATOR_FEEDBACK_CONTEXT = read_text(CREATOR_FEEDBACK_CONTEXT_PATH, limit=60000)
    if args.run_root is not None:
        RUN_ROOT = args.run_root if args.run_root.is_absolute() else ROOT / args.run_root
        RUN_DIR = RUN_ROOT / "run"

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    validations: dict[str, dict[str, Any]] = {}
    candidate_dirs: dict[str, Path] = {}

    for spec in MODEL_SPECS:
        slug = safe_name(spec.name)
        candidate_dir = RUN_DIR / f"candidate_created_by_{slug}"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        candidate_dirs[spec.name] = candidate_dir
        print(f"[creator:start] {spec.name}", flush=True)
        creator = run_model(
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
                python=PYTHON,
                seed=GENERATION_SEED,
            ),
            RUN_DIR / f"creator_{slug}.md",
            candidate_dir,
            CREATOR_EFFORT,
            CREATOR_TIMEOUT_SECONDS,
        )
        creator.update({"phase": "creator", "creator_model": spec.name, "creator_display_model": spec.display_name})
        manifest.append(creator)
        write_manifest(manifest)
        print(f"[creator:done] {spec.name} rc={creator['returncode']} tokens={creator['tokens_used']}", flush=True)

        validation = mismatch_validation(creator) if creator.get("model_mismatch") else local_validate(candidate_dir)
        validations[spec.name] = validation
        print(f"[validate] {spec.name} valid={validation['valid']}", flush=True)

        if not validation["valid"] and not creator.get("model_mismatch"):
            print(f"[repair:start] {spec.name}", flush=True)
            repair = run_model(
                spec,
                REPAIR_PROMPT.format(
                    agent_label=spec.agent_label,
                    artifact_dir=candidate_dir,
                    local_report=validation["report"][:60000],
                ),
                RUN_DIR / f"repair_{slug}.md",
                candidate_dir,
                CREATOR_EFFORT,
                CREATOR_TIMEOUT_SECONDS,
            )
            repair.update({"phase": "repair", "creator_model": spec.name, "creator_display_model": spec.display_name})
            manifest.append(repair)
            write_manifest(manifest)
            print(f"[repair:done] {spec.name} rc={repair['returncode']} tokens={repair['tokens_used']}", flush=True)
            validation = mismatch_validation(repair) if repair.get("model_mismatch") else local_validate(candidate_dir)
            validations[spec.name] = validation
            print(f"[validate:after_repair] {spec.name} valid={validation['valid']}", flush=True)

    for creator_spec in MODEL_SPECS:
        candidate_dir = candidate_dirs[creator_spec.name]
        if not validations.get(creator_spec.name, {}).get("valid"):
            continue
        for solver_spec in MODEL_SPECS:
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
