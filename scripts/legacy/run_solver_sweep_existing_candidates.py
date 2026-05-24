#!/usr/bin/env python3
"""Run/resume solver sweep for the existing two-model candidate run."""

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
SOLVER_MODELS = ["gpt-5.4", "gpt-5.5"]
CREATOR_TO_CANDIDATE = {
    "gpt-5.4": RUN_ROOT / "candidate_created_by_gpt_5_4",
    "gpt-5.5": RUN_ROOT / "candidate_created_by_gpt_5_5",
}
SOLVER_EFFORT = "low"
SOLVER_TIMEOUT_SECONDS = 900

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


def run_codex(model: str, prompt: str, out_path: Path, cwd: Path) -> dict[str, Any]:
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
        f'model_reasoning_effort="{SOLVER_EFFORT}"',
        "--output-last-message",
        str(out_path),
        "-",
    ]
    try:
        completed = run_cmd(cmd, cwd, stdin_text=prompt, timeout=SOLVER_TIMEOUT_SECONDS)
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


def score_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return {key: data.get(key) for key in ["total", "correct", "accuracy"] if key in data}


def run_solver(creator_model: str, solver_model: str) -> dict[str, Any]:
    candidate_dir = CREATOR_TO_CANDIDATE[creator_model]
    slug = f"{safe_name(creator_model)}__solved_by__{safe_name(solver_model)}"
    solver_dir = RUN_ROOT / f"isolated_solver_high_{slug}"
    if solver_dir.exists():
        shutil.rmtree(solver_dir)
    shutil.copytree(candidate_dir / "solver_bundle", solver_dir)

    item_ids = [str(row["id"]) for row in read_jsonl(solver_dir / "items_private_sample.jsonl")]
    out_path = RUN_ROOT / f"solver_high_{slug}.jsonl"
    result = run_codex(solver_model, SOLVER_PROMPT.format(model=solver_model), out_path, solver_dir)

    raw = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    predictions = extract_predictions(raw, item_ids)
    predictions_path = candidate_dir / f"predictions_solver_high_{safe_name(solver_model)}.jsonl"
    write_jsonl(predictions_path, predictions)
    score_path = candidate_dir / f"score_solver_high_{safe_name(solver_model)}.json"
    completed = run_cmd(
        [PYTHON, "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", str(predictions_path), "--out", str(score_path)],
        candidate_dir,
        timeout=300,
    )
    result.update(
        {
            "phase": "solver_high",
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


def main() -> None:
    manifest: list[dict[str, Any]] = []
    for creator_model in CREATOR_TO_CANDIDATE:
        for solver_model in SOLVER_MODELS:
            print(f"[solver_high:start] creator={creator_model} solver={solver_model}", flush=True)
            result = run_solver(creator_model, solver_model)
            manifest.append(result)
            print(
                f"[solver_high:done] creator={creator_model} solver={solver_model} "
                f"rows={result['prediction_rows']} score={result.get('score_summary')} "
                f"tokens={result['tokens_used']} rc={result['returncode']}",
                flush=True,
            )

    lines = ["# High-Effort Solver Sweep", ""]
    lines.append("| creator | solver | rows | correct | total | accuracy | tokens | returncode |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for item in manifest:
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
    lines.append(f"Solver effort: `{SOLVER_EFFORT}`")
    lines.append(f"Total solver tokens: `{sum(int(item.get('tokens_used') or 0) for item in manifest)}`")
    (RUN_ROOT / "solver_sweep_high_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RUN_ROOT / "solver_sweep_high_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
