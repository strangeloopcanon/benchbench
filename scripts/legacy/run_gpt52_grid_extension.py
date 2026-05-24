#!/usr/bin/env python3
"""Extend the existing BenchBench sweep with GPT-5.2.

This script adds GPT-5.2 as a creator and solver to the existing
`two_model_sweep_20260515_181811` run, producing the missing cells for a 3x3
creator-by-solver grid at low solver effort.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ROOT / "runs" / "two_model_sweep_20260515_181811"
PYTHON = shutil.which("python") or shutil.which("python3") or "python3"
GENERATION_SEED = 20260516
SAMPLE_COUNT = 30

CREATOR_MODEL = "gpt-5.2"
SOLVER_MODELS = ["gpt-5.2", "gpt-5.4", "gpt-5.5"]
ALL_CREATORS = ["gpt-5.2", "gpt-5.4", "gpt-5.5"]
SOLVER_EFFORT = "low"
CREATOR_EFFORT = "low"
CREATOR_TIMEOUT_SECONDS = 1800
SOLVER_TIMEOUT_SECONDS = 900

CREATOR_TO_CANDIDATE = {
    "gpt-5.2": RUN_ROOT / "candidate_created_by_gpt_5_2",
    "gpt-5.4": RUN_ROOT / "candidate_created_by_gpt_5_4",
    "gpt-5.5": RUN_ROOT / "candidate_created_by_gpt_5_5",
}


CREATOR_PROMPT = """
You are GPT-5.2+Codex creating one BenchBench candidate.

You are already in the empty artifact directory. Build the package here now.
Do not browse. Write files, generate the sample, validate, then respond with a
short summary.

Goal: create a 30-item benchmark that is valid, deterministic, exactly scored,
human-auditable, and difficult for GPT-5.2/GPT-5.4/GPT-5.5 Codex solvers.

Prior evidence to use:
- Text/JSON rule benchmarks were solved 29/30 to 30/30.
- Rich document/OCR packet benchmarks were solved 30/30.
- Visual Trace Cords broke GPT-5.5+Codex at 0/30 because the obvious
  computational shortcut was anticorrelated with the true visual topology.
- In the latest sweep, GPT-5.4 made Occluded Tile Provenance, which stayed hard:
  GPT-5.4 low 4/30, GPT-5.5 low 5/30, GPT-5.5 xhigh 10/30.
- GPT-5.5 made Shadow Weave Topology, which was valid but too easy:
  GPT-5.4 low 24/30, GPT-5.5 low 26/30.

Make a distinct benchmark. Do not clone either prior visual benchmark. Good
directions: raster-only perceptual grouping, occlusion/layer topology,
folded-strip order, tile-overlap provenance, shadow/contact topology, or another
residual skill where a cheap extraction shortcut is wrong.

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


SOLVER_PROMPT = """
You are {model}+Codex acting as a blind BenchBench solver.

You are in an isolated solver bundle. You may use local computation inside this
directory. You must not inspect parent directories or files outside this bundle.
Do not browse the internet.

Read every relevant visible file in this directory, including manifest, item
JSONL, README or solver packet, and referenced local assets. Solve every item.
Use local scripts or image processing if helpful, but prioritize returning a
complete best-effort answer set in this run.

Return only JSONL, one object per item, with exactly:
{{"id":"...","answer":"..."}}
"""


def safe_name(model: str) -> str:
    return model.replace(".", "_").replace("-", "_")


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


def score_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return {key: data.get(key) for key in ["total", "correct", "accuracy"] if key in data}


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


def run_solver(creator_model: str, solver_model: str) -> dict[str, Any]:
    candidate_dir = CREATOR_TO_CANDIDATE[creator_model]
    slug = f"{safe_name(creator_model)}__solved_by__{safe_name(solver_model)}"
    solver_dir = RUN_ROOT / f"isolated_solver_grid_{slug}"
    if solver_dir.exists():
        shutil.rmtree(solver_dir)
    shutil.copytree(candidate_dir / "solver_bundle", solver_dir)

    item_ids = [str(row["id"]) for row in read_jsonl(solver_dir / "items_private_sample.jsonl")]
    out_path = RUN_ROOT / f"solver_grid_{slug}.jsonl"
    result = run_codex(solver_model, SOLVER_PROMPT.format(model=solver_model), out_path, solver_dir, SOLVER_EFFORT, SOLVER_TIMEOUT_SECONDS)
    raw = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    predictions = extract_predictions(raw, item_ids)
    predictions_path = candidate_dir / f"predictions_solver_grid_{safe_name(solver_model)}.jsonl"
    write_jsonl(predictions_path, predictions)
    score_path = candidate_dir / f"score_solver_grid_{safe_name(solver_model)}.json"
    completed = run_cmd(
        [PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", str(predictions_path), "--out", str(score_path)],
        candidate_dir,
        timeout=300,
    )
    result.update(
        {
            "phase": "solver_grid",
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


def existing_score(creator_model: str, solver_model: str) -> dict[str, Any] | None:
    candidate_dir = CREATOR_TO_CANDIDATE[creator_model]
    old = candidate_dir / f"score_solver_high_{safe_name(solver_model)}.json"
    if old.exists():
        return score_summary(old)
    new = candidate_dir / f"score_solver_grid_{safe_name(solver_model)}.json"
    if new.exists():
        return score_summary(new)
    return None


def write_summary(manifest: list[dict[str, Any]], validation: dict[str, Any]) -> None:
    candidate_dir = CREATOR_TO_CANDIDATE[CREATOR_MODEL]
    lines: list[str] = []
    lines.append("# GPT-5.2 Grid Extension")
    lines.append("")
    lines.append(f"Run root: `{RUN_ROOT}`")
    lines.append("")
    lines.append("## GPT-5.2 Creator")
    lines.append("")
    lines.append(f"- Candidate: `{candidate_dir}`")
    lines.append(f"- Validated: `{validation.get('valid')}`")
    lines.append(f"- Bundle files: `{validation.get('bundle_file_count')}`")
    if validation.get("gold_summary"):
        lines.append(f"- Gold control: `{json.dumps(validation['gold_summary'], sort_keys=True)}`")
    if validation.get("wrong_summary"):
        lines.append(f"- Shifted-wrong control: `{json.dumps(validation['wrong_summary'], sort_keys=True)}`")
    lines.append(f"- Leak scan matches: `{len(validation.get('leak_matches') or [])}`")
    lines.append("")
    lines.append("## 3x3 Solver Grid")
    lines.append("")
    lines.append("| creator | solver gpt-5.2 | solver gpt-5.4 | solver gpt-5.5 |")
    lines.append("|---|---:|---:|---:|")
    for creator_model in ALL_CREATORS:
        cells: list[str] = []
        for solver_model in SOLVER_MODELS:
            score = existing_score(creator_model, solver_model)
            if score:
                cells.append(f"{score.get('correct')}/{score.get('total')}")
            else:
                cells.append("NA")
        lines.append(f"| {creator_model} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## New Solver Calls")
    lines.append("")
    lines.append("| creator | solver | rows | correct | total | accuracy | tokens | returncode |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for item in manifest:
        if item.get("phase") != "solver_grid":
            continue
        score = item.get("score_summary") or {}
        lines.append(
            "| {creator} | {solver} | {rows} | {correct} | {total} | {accuracy} | {tokens} | {rc} |".format(
                creator=item["creator_model"],
                solver=item["solver_model"],
                rows=item["prediction_rows"],
                correct=score.get("correct", "NA"),
                total=score.get("total", "NA"),
                accuracy=score.get("accuracy", "NA"),
                tokens=item["tokens_used"],
                rc=item["returncode"],
            )
        )
    lines.append("")
    lines.append(f"Solver effort for added cells: `{SOLVER_EFFORT}`")
    lines.append(f"Total new solver tokens: `{sum(int(item.get('tokens_used') or 0) for item in manifest if item.get('phase') == 'solver_grid')}`")
    lines.append("")
    (RUN_ROOT / "gpt52_grid_extension_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RUN_ROOT / "gpt52_grid_extension_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    manifest: list[dict[str, Any]] = []
    candidate_dir = CREATOR_TO_CANDIDATE[CREATOR_MODEL]
    candidate_dir.mkdir(parents=True, exist_ok=True)
    if not (candidate_dir / "controller_validation_report.txt").exists():
        print(f"[creator:start] {CREATOR_MODEL} -> {candidate_dir}", flush=True)
        result = run_codex(
            CREATOR_MODEL,
            CREATOR_PROMPT.format(python=PYTHON, seed=GENERATION_SEED),
            RUN_ROOT / "creator_gpt_5_2.md",
            candidate_dir,
            CREATOR_EFFORT,
            CREATOR_TIMEOUT_SECONDS,
        )
        result.update({"phase": "creator", "creator_model": CREATOR_MODEL})
        manifest.append(result)
        print(f"[creator:done] {CREATOR_MODEL} rc={result['returncode']} tokens={result['tokens_used']}", flush=True)
    validation = local_validate(candidate_dir)
    print(f"[validate] {CREATOR_MODEL} valid={validation['valid']}", flush=True)

    missing_cells = [
        ("gpt-5.4", "gpt-5.2"),
        ("gpt-5.5", "gpt-5.2"),
        ("gpt-5.2", "gpt-5.2"),
        ("gpt-5.2", "gpt-5.4"),
        ("gpt-5.2", "gpt-5.5"),
    ]
    if not validation["valid"]:
        print("[skip] GPT-5.2 candidate invalid; only running GPT-5.2 solver on existing candidates.", flush=True)
        missing_cells = [cell for cell in missing_cells if cell[0] != "gpt-5.2"]

    for creator_model, solver_model in missing_cells:
        if existing_score(creator_model, solver_model):
            print(f"[skip] creator={creator_model} solver={solver_model} already scored", flush=True)
            continue
        print(f"[solver:start] creator={creator_model} solver={solver_model}", flush=True)
        result = run_solver(creator_model, solver_model)
        manifest.append(result)
        print(
            f"[solver:done] creator={creator_model} solver={solver_model} "
            f"rows={result['prediction_rows']} score={result.get('score_summary')} "
            f"tokens={result['tokens_used']} rc={result['returncode']}",
            flush=True,
        )

    write_summary(manifest, validation)
    print(RUN_ROOT / "gpt52_grid_extension_summary.md", flush=True)


if __name__ == "__main__":
    main()

