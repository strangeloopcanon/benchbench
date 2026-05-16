#!/usr/bin/env python3
"""Run a two-model BenchBench creator/solver sweep.

The sweep asks GPT-5.4+Codex and GPT-5.5+Codex to each create one benchmark
candidate, validates the packages locally, then asks both GPT-5.4+Codex and
GPT-5.5+Codex to solve both accepted candidates from isolated solver bundles.
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
RUN_ROOT = ROOT / "runs" / f"two_model_sweep_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
PYTHON = shutil.which("python") or shutil.which("python3") or "python3"

CREATOR_MODELS = ["gpt-5.4", "gpt-5.5"]
SOLVER_MODELS = ["gpt-5.4", "gpt-5.5"]
CREATOR_EFFORT = "low"
SOLVER_EFFORT = "xhigh"
CREATOR_TIMEOUT_SECONDS = 1800
REPAIR_TIMEOUT_SECONDS = 1200
SOLVER_TIMEOUT_SECONDS = 3600
GENERATION_SEED = 20260516
SAMPLE_COUNT = 30


CREATOR_PROMPT = """
You are {model}+Codex creating one BenchBench candidate.

You are already in the empty artifact directory. Build the package here now.
Do not browse. Do not spend a long planning pass. Write files, generate the
sample, validate, then respond with a short summary.

Goal: create a 30-item benchmark that is valid, deterministic, exactly scored,
human-auditable, and difficult for GPT-5.4/GPT-5.5 Codex solvers.

Prior evidence to use:
- Text/JSON rule benchmarks were solved 29/30 to 30/30.
- Rich document/OCR packet benchmarks were solved 30/30.
- Visual Trace Cords broke GPT-5.5+Codex at 0/30 because the obvious
  computational shortcut was anticorrelated with the true visual topology.

Make a distinct benchmark. Do not clone Visual Trace Cords. Good directions:
raster-only perceptual grouping, occlusion/layer topology, folded-strip order,
tile-overlap provenance, shadow/contact topology, or another residual skill
where a cheap extraction shortcut is wrong.

Required files in this directory:
- README.md
- benchmark_spec.json
- generator.py
- verifier.py
- scorer.py
- gold_private_sample.jsonl
- validation_report.md
- failure_modes.md
- solver_bundle/SOLVER_MANIFEST.json
- solver_bundle/items_private_sample.jsonl
- solver_bundle/README.md or solver_bundle/solver_packet.md

Strict CLI contract:
- `{python} generator.py --sample-count 30 --seed {seed} --out-dir .`
- `{python} verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`
- `{python} scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

Contracts:
- gold rows and prediction rows contain exactly `id` and `answer`.
- solver_bundle item paths must be relative to solver_bundle.
- solver_bundle must not contain gold, generator/verifier/scorer, validation
  report, private traces, hidden coordinates, seed, source vectors, or solution
  labels.

Before finishing, generate 30 items, run verifier, run gold scorer, run one weak
baseline, inspect solver_bundle for leakage, and write validation_report.md.
"""


REPAIR_PROMPT = """
You are {model} running inside Codex as a BenchBench repair pass.

Candidate directory:
{candidate_dir}

The local controller found validation problems:

{local_report}

Repair the candidate in place. Preserve the intended benchmark idea if it is
good, but fix package validity, deterministic generation, solver-bundle
isolation, verifier/scorer CLI compatibility, and gold/prediction contracts.
Regenerate the 30-item sample and update validation_report.md.
"""


SOLVER_PROMPT = """
You are {model}+Codex acting as a blind BenchBench solver.

You are in an isolated solver bundle. You may use local computation inside this
directory. You must not inspect parent directories or files outside this bundle.
Do not browse the internet.

Read every relevant visible file in this directory, including
SOLVER_MANIFEST.json, items_private_sample.jsonl, README.md or solver_packet.md,
and any referenced local assets. Solve every item.

Return only JSONL, one object per item, with exactly:
{{"id":"...","answer":"..."}}
"""


def run_cmd(
    args: list[str],
    cwd: Path,
    stdin_text: str | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def parse_tokens(text: str) -> int:
    matches = re.findall(r"tokens used\s+(\d[\d,]*)", text)
    return int(matches[-1].replace(",", "")) if matches else 0


def safe_name(model: str) -> str:
    return model.replace(".", "_").replace("-", "_")


def run_codex(
    *,
    model: str,
    prompt: str,
    out_path: Path,
    cwd: Path,
    effort: str,
    timeout: int | None = None,
) -> dict[str, Any]:
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
    return {key: data.get(key) for key in ["total", "correct", "accuracy"] if key in data}


def make_shifted_wrong_predictions(gold_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    answers = []
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
    has_solver_text = any((candidate_dir / "solver_bundle" / name).exists() for name in ["README.md", "solver_packet.md"])
    if not has_solver_text:
        missing_bundle.append("README.md or solver_packet.md")
    report.append(f"missing_root_files: {missing_root if missing_root else 'none'}")
    report.append(f"missing_solver_bundle_files: {missing_bundle if missing_bundle else 'none'}")

    def run_validation_command(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess[str] | None:
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
        timeout=420,
    )

    gold_rows: list[dict[str, Any]] = []
    gold_path = candidate_dir / "gold_private_sample.jsonl"
    if gold_path.exists():
        try:
            gold_rows = read_jsonl(gold_path)
            write_jsonl(candidate_dir / "predictions_gold.jsonl", [{"id": row["id"], "answer": row["answer"]} for row in gold_rows])
            write_jsonl(candidate_dir / "predictions_wrong_shifted.jsonl", make_shifted_wrong_predictions(gold_rows))
            report.append(f"gold_rows: {len(gold_rows)}")
        except Exception as exc:  # noqa: BLE001
            report.append(f"gold_parse_error: {exc}")

    verifier = run_validation_command(
        [PYTHON, "verifier.py", "--items", "solver_bundle/items_private_sample.jsonl", "--gold", "gold_private_sample.jsonl"],
        timeout=300,
    )
    gold_score = run_validation_command(
        [PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_gold.jsonl", "--out", "score_gold_controller.json"],
        timeout=300,
    )
    wrong_score = run_validation_command(
        [
            PYTHON,
            "scorer.py",
            "--gold",
            "gold_private_sample.jsonl",
            "--predictions",
            "predictions_wrong_shifted.jsonl",
            "--out",
            "score_wrong_shifted_controller.json",
        ],
        timeout=300,
    )

    bundle_dir = candidate_dir / "solver_bundle"
    bundle_files: list[str] = []
    if bundle_dir.exists():
        bundle_files = sorted(str(path.relative_to(bundle_dir)) for path in bundle_dir.rglob("*") if path.is_file())
        report.append(f"solver_bundle_file_count: {len(bundle_files)}")
        report.append("solver_bundle_files_preview:")
        report.extend(bundle_files[:120])
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
    if leaks:
        report.append("leak_scan_matches:")
        report.extend(leaks[:80])
    else:
        report.append("leak_scan_matches: none")

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
        and (bundle_dir / "items_private_sample.jsonl").exists()
    )

    text_report = "\n".join(report) + "\n\ncommands:\n" + json.dumps(commands, indent=2) + "\n"
    (candidate_dir / "controller_validation_report.txt").write_text(text_report, encoding="utf-8")
    return {
        "valid": valid,
        "missing_root": missing_root,
        "missing_bundle": missing_bundle,
        "gold_summary": gold_summary,
        "wrong_summary": wrong_summary,
        "bundle_file_count": len(bundle_files),
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


def run_solver(candidate_dir: Path, creator_model: str, solver_model: str) -> dict[str, Any]:
    solver_slug = f"{safe_name(creator_model)}__solved_by__{safe_name(solver_model)}"
    solver_dir = RUN_ROOT / f"isolated_solver_{solver_slug}"
    if solver_dir.exists():
        shutil.rmtree(solver_dir)
    shutil.copytree(candidate_dir / "solver_bundle", solver_dir)

    item_rows = read_jsonl(solver_dir / "items_private_sample.jsonl")
    item_ids = [str(row["id"]) for row in item_rows if "id" in row]

    out_path = RUN_ROOT / f"solver_{solver_slug}.jsonl"
    result = run_codex(
        model=solver_model,
        prompt=SOLVER_PROMPT.format(model=solver_model),
        out_path=out_path,
        cwd=solver_dir,
        effort=SOLVER_EFFORT,
        timeout=SOLVER_TIMEOUT_SECONDS,
    )

    raw = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    predictions = extract_predictions(raw, item_ids)
    predictions_path = candidate_dir / f"predictions_solver_{safe_name(solver_model)}.jsonl"
    write_jsonl(predictions_path, predictions)
    score_path = candidate_dir / f"score_solver_{safe_name(solver_model)}.json"
    score_completed = run_cmd(
        [PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", str(predictions_path), "--out", str(score_path)],
        candidate_dir,
        timeout=300,
    )
    result.update(
        {
            "phase": "solver",
            "creator_model": creator_model,
            "solver_model": solver_model,
            "prediction_rows": len(predictions),
            "predictions_path": str(predictions_path),
            "score_path": str(score_path),
            "score_returncode": score_completed.returncode,
            "score_stdout": score_completed.stdout[-4000:],
            "score_stderr": score_completed.stderr[-4000:],
            "score_summary": score_summary(score_path),
        }
    )
    return result


def summarize(manifest: list[dict[str, Any]], candidates: dict[str, Path], validations: dict[str, dict[str, Any]]) -> None:
    lines: list[str] = []
    lines.append("# BenchBench Two-Model Creator/Solver Sweep")
    lines.append("")
    lines.append(f"Run root: `{RUN_ROOT}`")
    lines.append(f"Python used for validation/scoring: `{PYTHON}`")
    lines.append("")
    lines.append("## Design")
    lines.append("")
    lines.append("- Creator models: GPT-5.4+Codex and GPT-5.5+Codex.")
    lines.append("- Solver models: GPT-5.4+Codex and GPT-5.5+Codex.")
    lines.append("- Each creator was asked for one 30-item benchmark package.")
    lines.append("- Each valid candidate was solved blind from an isolated copy of its solver bundle.")
    lines.append("")
    lines.append("## Candidates")
    lines.append("")
    for model, path in candidates.items():
        validation = validations.get(model, {})
        lines.append(f"### {model}")
        lines.append("")
        lines.append(f"- Candidate: `{path}`")
        lines.append(f"- Validated: `{validation.get('valid')}`")
        lines.append(f"- Bundle file count: `{validation.get('bundle_file_count')}`")
        if validation.get("gold_summary"):
            lines.append(f"- Gold control: `{json.dumps(validation['gold_summary'], sort_keys=True)}`")
        if validation.get("wrong_summary"):
            lines.append(f"- Shifted wrong control: `{json.dumps(validation['wrong_summary'], sort_keys=True)}`")
        leak_count = len(validation.get("leak_matches") or [])
        lines.append(f"- Controller leak scan matches: `{leak_count}`")
        lines.append("")
    lines.append("## Solver Score Matrix")
    lines.append("")
    lines.append("| creator | solver | predictions | correct | total | accuracy | tokens |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for item in manifest:
        if item.get("phase") != "solver":
            continue
        score = item.get("score_summary") or {}
        lines.append(
            "| {creator} | {solver} | {preds} | {correct} | {total} | {acc} | {tokens} |".format(
                creator=item.get("creator_model"),
                solver=item.get("solver_model"),
                preds=item.get("prediction_rows"),
                correct=score.get("correct", "NA"),
                total=score.get("total", "NA"),
                acc=score.get("accuracy", "NA"),
                tokens=item.get("tokens_used", 0),
            )
        )
    lines.append("")
    lines.append("## Codex Calls")
    lines.append("")
    lines.append("| phase | model | returncode | tokens | output |")
    lines.append("|---|---:|---:|---:|---|")
    for item in manifest:
        lines.append(
            "| {phase} | {model} | {returncode} | {tokens} | `{out}` |".format(
                phase=item.get("phase"),
                model=item.get("model"),
                returncode=item.get("returncode"),
                tokens=item.get("tokens_used", 0),
                out=item.get("out_path"),
            )
        )
    lines.append("")
    total_tokens = sum(int(item.get("tokens_used") or 0) for item in manifest)
    lines.append(f"Total reported Codex tokens: `{total_tokens}`")
    lines.append("")
    (RUN_ROOT / "sweep_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RUN_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    candidates: dict[str, Path] = {}
    validations: dict[str, dict[str, Any]] = {}

    for creator_model in CREATOR_MODELS:
        slug = safe_name(creator_model)
        candidate_dir = RUN_ROOT / f"candidate_created_by_{slug}"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        candidates[creator_model] = candidate_dir

        creator_out = RUN_ROOT / f"creator_{slug}.md"
        print(f"[creator:start] {creator_model} -> {candidate_dir}", flush=True)
        creator_result = run_codex(
            model=creator_model,
            prompt=CREATOR_PROMPT.format(
                model=creator_model,
                candidate_dir=candidate_dir,
                python=PYTHON,
                seed=GENERATION_SEED,
            ),
            out_path=creator_out,
            cwd=candidate_dir,
            effort=CREATOR_EFFORT,
            timeout=CREATOR_TIMEOUT_SECONDS,
        )
        creator_result.update({"phase": "creator", "creator_model": creator_model})
        manifest.append(creator_result)
        print(
            f"[creator:done] {creator_model} returncode={creator_result['returncode']} tokens={creator_result['tokens_used']}",
            flush=True,
        )

        validation = local_validate(candidate_dir)
        validations[creator_model] = validation
        print(f"[validate] {creator_model} valid={validation['valid']}", flush=True)

        if not validation["valid"]:
            repair_out = RUN_ROOT / f"repair_{slug}.md"
            print(f"[repair:start] {creator_model}", flush=True)
            repair_result = run_codex(
                model=creator_model,
                prompt=REPAIR_PROMPT.format(
                    model=creator_model,
                    candidate_dir=candidate_dir,
                    local_report=validation["report"][:60000],
                ),
                out_path=repair_out,
                cwd=candidate_dir,
                effort=CREATOR_EFFORT,
                timeout=REPAIR_TIMEOUT_SECONDS,
            )
            repair_result.update({"phase": "repair", "creator_model": creator_model})
            manifest.append(repair_result)
            print(
                f"[repair:done] {creator_model} returncode={repair_result['returncode']} tokens={repair_result['tokens_used']}",
                flush=True,
            )
            validation = local_validate(candidate_dir)
            validations[creator_model] = validation
            print(f"[validate:after_repair] {creator_model} valid={validation['valid']}", flush=True)

    for creator_model, candidate_dir in candidates.items():
        validation = validations.get(creator_model, {})
        if not validation.get("valid"):
            manifest.append(
                {
                    "phase": "solver_skipped",
                    "creator_model": creator_model,
                    "model": "all",
                    "returncode": None,
                    "tokens_used": 0,
                    "reason": "candidate failed validation",
                }
            )
            continue
        for solver_model in SOLVER_MODELS:
            print(f"[solver:start] creator={creator_model} solver={solver_model}", flush=True)
            solver_result = run_solver(candidate_dir, creator_model, solver_model)
            manifest.append(solver_result)
            print(
                f"[solver:done] creator={creator_model} solver={solver_model} "
                f"rows={solver_result.get('prediction_rows')} score={solver_result.get('score_summary')} "
                f"tokens={solver_result.get('tokens_used')}",
                flush=True,
            )

    summarize(manifest, candidates, validations)
    print(RUN_ROOT)


if __name__ == "__main__":
    main()
