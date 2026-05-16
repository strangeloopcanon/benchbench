#!/usr/bin/env python3
"""Broad BenchBench creator/solver sweep.

This run intentionally avoids steering creators toward any specific modality or
task family. Creators get benchmark landscape notes and prior pilot outcomes,
then must decide what benchmark to build.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "experiments" / f"002_broad_sweep_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
RUN_DIR = RUN_ROOT / "run"
PYTHON = shutil.which("python") or shutil.which("python3") or "python3"

MODELS = ["gpt-5.2", "gpt-5.4", "gpt-5.5"]
CREATOR_EFFORT = "low"
SOLVER_EFFORT = "low"
CREATOR_TIMEOUT_SECONDS = 2400
SOLVER_TIMEOUT_SECONDS = 1500
SAMPLE_COUNT = 30
GENERATION_SEED = 20260516


def safe_name(model: str) -> str:
    return model.replace(".", "_").replace("-", "_")


def read_text(path: Path, limit: int | None = None) -> str:
    text = path.read_text(encoding="utf-8")
    return text[:limit] if limit else text


LANDSCAPE_PACK = ROOT / "benchmark_landscape" / "creator_prompt_landscape_pack.md"
BENCHMARK_LANDSCAPE = read_text(
    LANDSCAPE_PACK if LANDSCAPE_PACK.exists() else ROOT / "benchbench_research_notes.md",
    limit=90000,
)
PILOT_SUMMARY = read_text(ROOT / "experiments" / "001_three_model_grid_pilot" / "README.md", limit=12000)


CREATOR_PROMPT = """
You are {model}+Codex acting as a BenchBench creator.

You are already in an empty artifact directory. Build one benchmark package
here. You may use local computation and internet research if useful. Do not
browse or research forever: the output must be a working package.

Your task, in the broadest terms:

Create the best possible new benchmark you can: valid, deterministic or
reliably graded, human-auditable, hard for strong Codex-enabled models, and
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
You are {model}+Codex repairing your BenchBench candidate in place.

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
You are {model}+Codex acting as a blind BenchBench solver.

You are in an isolated solver bundle. You may use any local computation, shell
scripts, installed packages, OCR, image processing, code, and internet access if
useful. Try your best to solve the benchmark.

The only forbidden action is inspecting parent directories or files outside this
isolated solver bundle. Do not look for gold files, generators, scorers, private
traces, or answer keys outside this directory.

Read every visible file in this bundle and solve every item.

Return only JSONL, one object per item, with exactly:
{{"id":"...","answer":"..."}}
"""


def run_cmd(args: list[str], cwd: Path, stdin_text: str | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, input=stdin_text, text=True, capture_output=True, check=False, timeout=timeout)


def parse_tokens(text: str) -> int:
    matches = re.findall(r"tokens used\s+(\d[\d,]*)", text)
    return int(matches[-1].replace(",", "")) if matches else 0


def run_codex(model: str, prompt: str, out_path: Path, cwd: Path, effort: str, timeout: int) -> dict[str, Any]:
    prompt_path = out_path.with_suffix(".prompt.txt")
    prompt_path.write_text(prompt, encoding="utf-8")
    cmd = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "-m",
        model,
        "-c",
        f'model_reasoning_effort="{effort}"',
        "--output-last-message",
        str(out_path),
        "-",
    ]
    try:
        completed = run_cmd(cmd, cwd, stdin_text=prompt, timeout=timeout)
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr += f"\nTIMEOUT after {timeout} seconds\n"
        returncode = -124
    stdout_path = out_path.with_suffix(".stdout.txt")
    stderr_path = out_path.with_suffix(".stderr.txt")
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    return {
        "model": model,
        "returncode": returncode,
        "tokens_used": parse_tokens(stdout + "\n" + stderr),
        "out_path": str(out_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "prompt_path": str(prompt_path),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")


def score_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    total = data.get("total", data.get("n_items"))
    correct = data.get("correct", data.get("n_correct"))
    accuracy = data.get("accuracy")
    if total is None or correct is None or accuracy is None:
        return None
    return {"total": total, "correct": correct, "accuracy": accuracy}


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
    gold_path = candidate_dir / "gold_private_sample.jsonl"
    if gold_path.exists():
        try:
            gold_rows = read_jsonl(gold_path)
            write_jsonl(candidate_dir / "predictions_gold_controller.jsonl", [{"id": row["id"], "answer": row["answer"]} for row in gold_rows])
            write_jsonl(candidate_dir / "predictions_wrong_shifted_controller.jsonl", make_shifted_wrong_predictions(gold_rows))
            report.append(f"gold_rows: {len(gold_rows)}")
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
    if bundle_dir.exists():
        bundle_files = sorted(str(path.relative_to(bundle_dir)) for path in bundle_dir.rglob("*") if path.is_file())
        report.append(f"solver_bundle_file_count: {len(bundle_files)}")
        items_path = bundle_dir / "items_private_sample.jsonl"
        if items_path.exists():
            try:
                report.append(f"solver_bundle_item_rows: {len(read_jsonl(items_path))}")
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


def extract_predictions(raw: str, item_ids: list[str]) -> list[dict[str, Any]]:
    by_id: dict[str, Any] = {}
    for line in raw.splitlines():
        s = line.strip().strip(",")
        if not (s.startswith("{") and s.endswith("}")):
            continue
        try:
            obj = json.loads(s)
        except Exception:
            continue
        if isinstance(obj, dict) and set(obj) == {"id", "answer"} and obj.get("id") in item_ids:
            by_id[str(obj["id"])] = obj["answer"]
    return [{"id": row_id, "answer": by_id[row_id]} for row_id in item_ids if row_id in by_id]


def run_solver(creator_model: str, solver_model: str, candidate_dir: Path) -> dict[str, Any]:
    slug = f"{safe_name(creator_model)}__solved_by__{safe_name(solver_model)}"
    solver_dir = RUN_DIR / f"isolated_solver_{slug}"
    if solver_dir.exists():
        shutil.rmtree(solver_dir)
    shutil.copytree(candidate_dir / "solver_bundle", solver_dir)
    item_ids = [str(row["id"]) for row in read_jsonl(solver_dir / "items_private_sample.jsonl")]

    out_path = RUN_DIR / f"solver_{slug}.jsonl"
    result = run_codex(solver_model, SOLVER_PROMPT.format(model=solver_model), out_path, solver_dir, SOLVER_EFFORT, SOLVER_TIMEOUT_SECONDS)
    raw = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    predictions = extract_predictions(raw, item_ids)
    predictions_path = candidate_dir / f"predictions_solver_{safe_name(solver_model)}.jsonl"
    write_jsonl(predictions_path, predictions)
    score_path = candidate_dir / f"score_solver_{safe_name(solver_model)}.json"
    completed = run_cmd(
        [PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", str(predictions_path), "--out", str(score_path)],
        candidate_dir,
        timeout=420,
    )
    result.update(
        {
            "phase": "solver",
            "creator_model": creator_model,
            "solver_model": solver_model,
            "prediction_rows": len(predictions),
            "predictions_path": str(predictions_path),
            "score_path": str(score_path),
            "score_returncode": completed.returncode,
            "score_stdout": completed.stdout[-4000:],
            "score_stderr": completed.stderr[-4000:],
            "score_summary": score_summary(score_path),
        }
    )
    return result


def candidate_title(candidate_dir: Path) -> str:
    spec = candidate_dir / "benchmark_spec.json"
    if spec.exists():
        try:
            data = json.loads(spec.read_text(encoding="utf-8"))
            for key in ["benchmark_name", "name", "title", "benchmark_id"]:
                if data.get(key):
                    return str(data[key])
        except Exception:
            pass
    readme = candidate_dir / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                return line.lstrip("#").strip()
    return candidate_dir.name


def write_summary(manifest: list[dict[str, Any]], validations: dict[str, dict[str, Any]], candidate_dirs: dict[str, Path]) -> None:
    lines: list[str] = []
    lines.append("# Broad BenchBench Sweep")
    lines.append("")
    lines.append("This run used the broad creator prompt: creators saw benchmark landscape notes and prior pilot outcomes, but were not directed toward any specific domain or modality.")
    lines.append("")
    lines.append(f"Run root: `{RUN_ROOT}`")
    lines.append(f"Creator models: `{', '.join(MODELS)}`")
    lines.append(f"Solver models: `{', '.join(MODELS)}`")
    lines.append(f"Creator effort: `{CREATOR_EFFORT}`")
    lines.append(f"Solver effort: `{SOLVER_EFFORT}`")
    lines.append("")
    lines.append("## Candidates")
    lines.append("")
    for model in MODELS:
        cdir = candidate_dirs[model]
        val = validations.get(model, {})
        lines.append(f"### {model}: {candidate_title(cdir)}")
        lines.append("")
        lines.append(f"- Candidate: `{cdir}`")
        lines.append(f"- Validated: `{val.get('valid')}`")
        lines.append(f"- Bundle files: `{val.get('bundle_file_count')}`")
        if val.get("gold_summary"):
            lines.append(f"- Gold control: `{json.dumps(val['gold_summary'], sort_keys=True)}`")
        if val.get("wrong_summary"):
            lines.append(f"- Shifted-wrong control: `{json.dumps(val['wrong_summary'], sort_keys=True)}`")
        lines.append(f"- Leak scan matches: `{len(val.get('leak_matches') or [])}`")
        lines.append("")

    lines.append("## Solver Grid")
    lines.append("")
    lines.append("| creator | benchmark | solver GPT-5.2 | solver GPT-5.4 | solver GPT-5.5 | max score | status |")
    lines.append("|---|---|---:|---:|---:|---:|---|")
    for creator_model in MODELS:
        cdir = candidate_dirs[creator_model]
        cells = []
        max_correct: int | None = None
        max_total: int | None = None
        for solver_model in MODELS:
            score = score_summary(cdir / f"score_solver_{safe_name(solver_model)}.json")
            if score:
                cells.append(f"{score['correct']}/{score['total']}")
                if max_correct is None or score["correct"] > max_correct:
                    max_correct = int(score["correct"])
                    max_total = int(score["total"])
            else:
                cells.append("NA")
        status = "accept" if max_correct is not None and max_total and max_correct < (0.5 * max_total) else "reject"
        lines.append(f"| {creator_model} | {candidate_title(cdir)} | " + " | ".join(cells) + f" | {max_correct}/{max_total} | {status} |")

    lines.append("")
    lines.append("## Calls")
    lines.append("")
    lines.append("| phase | creator | solver/model | rows | score | tokens | returncode |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for item in manifest:
        score = item.get("score_summary") or {}
        score_text = "NA"
        if score:
            score_text = f"{score.get('correct')}/{score.get('total')}"
        lines.append(
            "| {phase} | {creator} | {model} | {rows} | {score} | {tokens} | {rc} |".format(
                phase=item.get("phase"),
                creator=item.get("creator_model", ""),
                model=item.get("solver_model", item.get("model", "")),
                rows=item.get("prediction_rows", ""),
                score=score_text,
                tokens=item.get("tokens_used", 0),
                rc=item.get("returncode"),
            )
        )
    lines.append("")
    lines.append(f"Total reported tokens: `{sum(int(item.get('tokens_used') or 0) for item in manifest)}`")
    lines.append("")
    (RUN_ROOT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RUN_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    validations: dict[str, dict[str, Any]] = {}
    candidate_dirs: dict[str, Path] = {}

    for model in MODELS:
        slug = safe_name(model)
        candidate_dir = RUN_DIR / f"candidate_created_by_{slug}"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        candidate_dirs[model] = candidate_dir
        print(f"[creator:start] {model}", flush=True)
        creator = run_codex(
            model,
            CREATOR_PROMPT.format(
                model=model,
                benchmark_landscape=BENCHMARK_LANDSCAPE,
                pilot_summary=PILOT_SUMMARY,
                python=PYTHON,
                seed=GENERATION_SEED,
            ),
            RUN_DIR / f"creator_{slug}.md",
            candidate_dir,
            CREATOR_EFFORT,
            CREATOR_TIMEOUT_SECONDS,
        )
        creator.update({"phase": "creator", "creator_model": model})
        manifest.append(creator)
        print(f"[creator:done] {model} rc={creator['returncode']} tokens={creator['tokens_used']}", flush=True)

        validation = local_validate(candidate_dir)
        validations[model] = validation
        print(f"[validate] {model} valid={validation['valid']}", flush=True)

        if not validation["valid"]:
            print(f"[repair:start] {model}", flush=True)
            repair = run_codex(
                model,
                REPAIR_PROMPT.format(model=model, local_report=validation["report"][:60000]),
                RUN_DIR / f"repair_{slug}.md",
                candidate_dir,
                CREATOR_EFFORT,
                CREATOR_TIMEOUT_SECONDS,
            )
            repair.update({"phase": "repair", "creator_model": model})
            manifest.append(repair)
            print(f"[repair:done] {model} rc={repair['returncode']} tokens={repair['tokens_used']}", flush=True)
            validation = local_validate(candidate_dir)
            validations[model] = validation
            print(f"[validate:after_repair] {model} valid={validation['valid']}", flush=True)

    for creator_model in MODELS:
        candidate_dir = candidate_dirs[creator_model]
        if not validations.get(creator_model, {}).get("valid"):
            continue
        for solver_model in MODELS:
            print(f"[solver:start] creator={creator_model} solver={solver_model}", flush=True)
            result = run_solver(creator_model, solver_model, candidate_dir)
            manifest.append(result)
            print(
                f"[solver:done] creator={creator_model} solver={solver_model} "
                f"rows={result['prediction_rows']} score={result.get('score_summary')} "
                f"tokens={result['tokens_used']} rc={result['returncode']}",
                flush=True,
            )

    write_summary(manifest, validations, candidate_dirs)
    print(RUN_ROOT / "summary.md", flush=True)


if __name__ == "__main__":
    main()
