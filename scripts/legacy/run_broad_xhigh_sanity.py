#!/usr/bin/env python3
"""Run GPT-5.5 xhigh sanity checks on broad-sweep contenders."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchbench_model_backends import parse_tokens, run_cmd, safe_name
from benchbench_results import candidate_title, extract_predictions, read_jsonl, score_summary, write_jsonl


RUN_ROOT = ROOT / "experiments" / "002_broad_sweep_20260515_220653"
RUN_DIR = RUN_ROOT / "run"
PYTHON = shutil.which("python") or shutil.which("python3") or "python3"
SOLVER_MODEL = "gpt-5.5"
SOLVER_EFFORT = "xhigh"
SOLVER_TIMEOUT_SECONDS = 3600
CONTENDERS = ["gpt-5.2", "gpt-5.5"]


SOLVER_PROMPT = """
You are GPT-5.5+Codex acting as a blind BenchBench solver.

You are in an isolated solver bundle. You may use any local computation, shell
scripts, installed packages, OCR, image processing, code, and internet access if
useful. Try your best to solve the benchmark.

The only forbidden action is inspecting parent directories or files outside this
isolated solver bundle. Do not look for gold files, generators, scorers, private
traces, or answer keys outside this directory.

Read every visible file in this bundle and solve every item.

Return only JSONL, one object per item, with exactly:
{"id":"...","answer":"..."}
"""


def run_codex(out_path: Path, cwd: Path) -> dict[str, Any]:
    prompt_path = out_path.with_suffix(".prompt.txt")
    prompt_path.write_text(SOLVER_PROMPT, encoding="utf-8")
    cmd = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "-m",
        SOLVER_MODEL,
        "-c",
        f'model_reasoning_effort="{SOLVER_EFFORT}"',
        "--output-last-message",
        str(out_path),
        "-",
    ]
    try:
        completed = run_cmd(cmd, cwd, stdin_text=SOLVER_PROMPT, timeout=SOLVER_TIMEOUT_SECONDS)
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
        stderr += f"\nTIMEOUT after {SOLVER_TIMEOUT_SECONDS} seconds\n"
        returncode = -124
    stdout_path = out_path.with_suffix(".stdout.txt")
    stderr_path = out_path.with_suffix(".stderr.txt")
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    return {
        "returncode": returncode,
        "tokens_used": parse_tokens(stdout + "\n" + stderr),
        "out_path": str(out_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "prompt_path": str(prompt_path),
    }


def run_one(creator_model: str) -> dict[str, Any]:
    candidate_dir = RUN_DIR / f"candidate_created_by_{safe_name(creator_model)}"
    slug = f"{safe_name(creator_model)}__solved_by__{safe_name(SOLVER_MODEL)}__xhigh"
    solver_dir = RUN_DIR / f"isolated_solver_{slug}"
    if solver_dir.exists():
        shutil.rmtree(solver_dir)
    shutil.copytree(candidate_dir / "solver_bundle", solver_dir)
    item_ids = [str(row["id"]) for row in read_jsonl(solver_dir / "items_private_sample.jsonl")]
    out_path = RUN_DIR / f"solver_{slug}.jsonl"
    result = run_codex(out_path, solver_dir)
    raw = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    predictions = extract_predictions(raw, item_ids)
    pred_path = candidate_dir / "predictions_solver_gpt_5_5_xhigh.jsonl"
    write_jsonl(pred_path, predictions)
    score_path = candidate_dir / "score_solver_gpt_5_5_xhigh.json"
    completed = run_cmd(
        [PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", str(pred_path), "--out", str(score_path)],
        candidate_dir,
        timeout=420,
    )
    result.update(
        {
            "creator_model": creator_model,
            "benchmark": candidate_title(candidate_dir),
            "prediction_rows": len(predictions),
            "predictions_path": str(pred_path),
            "score_path": str(score_path),
            "score_returncode": completed.returncode,
            "score_stdout": completed.stdout[-4000:],
            "score_stderr": completed.stderr[-4000:],
            "score_summary": score_summary(score_path),
        }
    )
    return result


def main() -> None:
    manifest: list[dict[str, Any]] = []
    for creator_model in CONTENDERS:
        print(f"[xhigh:start] creator={creator_model} solver={SOLVER_MODEL}", flush=True)
        result = run_one(creator_model)
        manifest.append(result)
        print(
            f"[xhigh:done] creator={creator_model} rows={result['prediction_rows']} "
            f"score={result.get('score_summary')} tokens={result['tokens_used']} rc={result['returncode']}",
            flush=True,
        )
    lines = ["# Broad Sweep GPT-5.5 XHigh Sanity Checks", ""]
    lines.append("| creator | benchmark | rows | score | accuracy | tokens | returncode |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for item in manifest:
        score = item.get("score_summary") or {}
        lines.append(
            "| {creator} | {bench} | {rows} | {correct}/{total} | {acc} | {tokens} | {rc} |".format(
                creator=item["creator_model"],
                bench=item["benchmark"],
                rows=item["prediction_rows"],
                correct=score.get("correct", "NA"),
                total=score.get("total", "NA"),
                acc=score.get("accuracy", "NA"),
                tokens=item["tokens_used"],
                rc=item["returncode"],
            )
        )
    lines.append("")
    lines.append(f"Solver model: `{SOLVER_MODEL}`")
    lines.append(f"Solver effort: `{SOLVER_EFFORT}`")
    (RUN_ROOT / "xhigh_sanity_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RUN_ROOT / "xhigh_sanity_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
