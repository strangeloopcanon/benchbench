#!/usr/bin/env python3
"""BenchBench v4 creative run.

This run uses the v2/v3 failures as evidence and asks GPT-5.5 to construct a
more creative benchmark, optionally using messy documents or visual assets, while
preserving exact scoring and solver-bundle isolation.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ROOT / "runs" / f"gpt55_benchbench_v4_creative_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
MODEL = "gpt-5.5"
CANDIDATE_ID = "creative_bestshot"

REQUIRED_ROOT_FILES = [
    "README.md",
    "benchmark_spec.json",
    "generator.py",
    "verifier.py",
    "scorer.py",
    "gold_private_sample.jsonl",
    "validation_report.md",
    "failure_modes.md",
]

REQUIRED_BUNDLE_FILES = [
    "SOLVER_MANIFEST.json",
    "solver_packet.md",
    "items_private_sample.jsonl",
]


CREATOR_PROMPT = """
You are GPT-5.5 running inside Codex as a BenchBench v4 creator.

Artifact directory:
{candidate_dir}

Mission:
Build the most creative valid benchmark package you can that a blind
GPT-5.5+Codex solver may fail, while a qualified human could solve.

You are allowed to use nontrivial solver-bundle files: raster images, SVGs,
PDF-like text dumps, CSVs, forms, receipts, email fragments, screenshots,
tables, noisy OCR-style snippets, or mixed-format document sets. You may create
assets with Python. The final benchmark must still be objectively and
deterministically scoreable.

Prior BenchBench evidence you must use:
- v2 produced valid deterministic text/JSON tasks, but GPT-5.5+Codex solved them
  30/30, 30/30, and 29/30 by converting visible rules into computation.
- v3 produced a much better benchmark-quality-auditing task. It was valid and
  beat a naive baseline 6/30, but GPT-5.5+Codex still scored 30/30 after writing
  a parser/reasoner from the visible rules.
- Therefore, do not make a single clean grammar, a compact rule list, or a task
  where all difficulty is regular extraction plus precedence rules.

Existing benchmark map:
- MMLU/MMLU-Pro: broad static knowledge.
- GPQA/HLE/FrontierMath/AIME: hard expert/math closed-answer reasoning.
- SWE-bench/LiveCodeBench: executable code repair/generation.
- LiveBench: contamination-resistant live updates across standard skills.
- BFCL/tool evals: function-calling and tool workflows.
- OSWorld/WebArena/WebVoyager/ScreenSpot: GUI/browser/visual agent tasks.
- Arena-Hard/Chatbot Arena: preference and open-ended user prompts.
- MLE-bench/RE-Bench: long-horizon ML/R&D engineering.

Benchmark-quality principles:
- Broken golds, ambiguity, or impossible items score zero.
- A reversal is useful only if it measures an interpretable residual skill.
- The benchmark should be human-auditable, exact-scoreable, reproducible, and
  not merely an environment/tool-access exploit.
- If you use visual or document assets, state the track caveat clearly: this run
  tests GPT-5.5+Codex with local computation, not necessarily a fully multimodal
  model with direct image perception.

Required root files:
- README.md
- benchmark_spec.json
- generator.py
- verifier.py
- scorer.py
- gold_private_sample.jsonl
- validation_report.md
- failure_modes.md
- optional: items_private_sample.jsonl, assets/, baseline_solver.py, adversarial_selection_report.md

Required isolated solver bundle:
- solver_bundle/SOLVER_MANIFEST.json
- solver_bundle/solver_packet.md
- solver_bundle/items_private_sample.jsonl
- optional: solver_bundle/assets/ and other solver-visible supporting files

Strict CLI contract from the candidate directory:
- `python3 generator.py --sample-count 30 --seed 20260515 --out-dir .`
- `python3 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`
- `python3 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

Data contract:
- `gold_private_sample.jsonl` rows include exactly `id` and `answer`.
- solver predictions include exactly `id` and `answer`.
- `solver_bundle/items_private_sample.jsonl` must contain item ids and references
  to any solver-visible assets using relative paths inside `solver_bundle/`.
- The solver bundle must not contain golds, verifier/generator/scorer logic,
  validation reports, prior predictions, or hidden labels.

Before finishing:
1. Generate 30 private sample items.
2. Verify every item.
3. Run gold scorer.
4. Run wrong or naive baseline scorer.
5. Inspect the solver bundle for leakage.
6. Write a validation report.

Think hard and be bold. The goal is to finally produce a benchmark that this
Codex-enabled GPT-5.5 solver cannot solve. But do not sacrifice validity.
"""


VALIDATOR_PROMPT = """
You are GPT-5.5 acting as BenchBench v4 validator.

Candidate directory:
{candidate_dir}

Local validation report:
{local_report}

Validate only package quality and solver-bundle isolation. Do not solve the
items. Check whether it should be sent to a blind GPT-5.5+Codex solver.

Return PASS / FAIL / CONDITIONAL and concise reasons.
"""


SOLVER_PROMPT = """
You are GPT-5.5+Codex acting as a blind BenchBench solver.

You are in an isolated solver bundle. You may use local computation inside this
directory. You must not inspect parent directories or files outside this bundle.
Do not browse.

Read SOLVER_MANIFEST.json, solver_packet.md, items_private_sample.jsonl, and any
referenced local assets. Solve every item.

Return only JSONL, one object per item, with exactly:
{"id": "...", "answer": ...}
"""


JUDGE_PROMPT = """
You are GPT-5.5 acting as corrected final BenchBench v4 judge.

Evidence:
{evidence}

Judge strictly:
1. Is the package valid?
2. Was the blind solver run properly isolated?
3. What benchmark was built?
4. What did GPT-5.5+Codex score?
5. Is it frontier-resistant in this pilot?
6. What lesson should feed into the next run?
"""


def run_cmd(args: list[str], cwd: Path, stdin_text: str | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, input=stdin_text, text=True, capture_output=True, check=False, timeout=timeout)


def parse_tokens(text: str) -> int:
    matches = re.findall(r"tokens used\s+(\d[\d,]*)", text)
    return int(matches[-1].replace(",", "")) if matches else 0


def run_codex(prompt: str, out_path: Path, *, effort: str = "high", cwd: Path | None = None) -> dict[str, Any]:
    cwd = cwd or ROOT
    prompt_path = out_path.with_suffix(".prompt.txt")
    prompt_path.write_text(prompt, encoding="utf-8")
    cmd = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "-m",
        MODEL,
        "-c",
        f'model_reasoning_effort="{effort}"',
        "--output-last-message",
        str(out_path),
        "-",
    ]
    completed = run_cmd(cmd, cwd, stdin_text=prompt, timeout=None)
    stdout_path = out_path.with_suffix(".stdout.txt")
    stderr_path = out_path.with_suffix(".stderr.txt")
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return {
        "returncode": completed.returncode,
        "tokens_used": parse_tokens(completed.stdout + "\n" + completed.stderr),
        "out_path": str(out_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "prompt_path": str(prompt_path),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
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


def local_validate(candidate_dir: Path) -> str:
    lines: list[str] = []
    missing_root = [name for name in REQUIRED_ROOT_FILES if not (candidate_dir / name).exists()]
    missing_bundle = [name for name in REQUIRED_BUNDLE_FILES if not (candidate_dir / "solver_bundle" / name).exists()]
    lines.append(f"missing_root_files: {missing_root if missing_root else 'none'}")
    lines.append(f"missing_solver_bundle_files: {missing_bundle if missing_bundle else 'none'}")

    generator_cmd = ["python3", "generator.py", "--sample-count", "30", "--seed", "20260515", "--out-dir", "."]
    if (candidate_dir / "generator.py").exists():
        try:
            completed = run_cmd(generator_cmd, candidate_dir, timeout=180)
            lines.extend([f"command: {' '.join(generator_cmd)}", f"returncode: {completed.returncode}"])
            if completed.stdout.strip():
                lines.extend(["stdout:", completed.stdout.strip()[-4000:]])
            if completed.stderr.strip():
                lines.extend(["stderr:", completed.stderr.strip()[-4000:]])
        except Exception as exc:  # noqa: BLE001
            lines.append(f"generator_error: {exc}")

    commands = [
        ["python3", "verifier.py", "--items", "solver_bundle/items_private_sample.jsonl", "--gold", "gold_private_sample.jsonl"],
    ]
    gold_path = candidate_dir / "gold_private_sample.jsonl"
    if gold_path.exists():
        try:
            gold_rows = load_jsonl(gold_path)
            lines.append(f"gold_rows: {len(gold_rows)}")
            write_jsonl(candidate_dir / "predictions_gold.jsonl", [{"id": row["id"], "answer": row["answer"]} for row in gold_rows])
            # Prefer creator-provided wrong/baseline predictions if present.
            if not (candidate_dir / "predictions_wrong.jsonl").exists():
                wrong_rows = []
                for row in gold_rows:
                    ans = row["answer"]
                    wrong = "__BENCHBENCH_WRONG__" if ans != "__BENCHBENCH_WRONG__" else "__BENCHBENCH_OTHER_WRONG__"
                    wrong_rows.append({"id": row["id"], "answer": wrong})
                write_jsonl(candidate_dir / "predictions_wrong.jsonl", wrong_rows)
            commands.extend(
                [
                    ["python3", "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_gold.jsonl", "--out", "score_gold.json"],
                    ["python3", "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_wrong.jsonl", "--out", "score_wrong.json"],
                ]
            )
        except Exception as exc:  # noqa: BLE001
            lines.append(f"gold_fixture_error: {exc}")

    for command in commands:
        if not (candidate_dir / command[1]).exists():
            lines.append(f"command_skipped: {' '.join(command)}")
            continue
        try:
            completed = run_cmd(command, candidate_dir, timeout=180)
            lines.extend([f"command: {' '.join(command)}", f"returncode: {completed.returncode}"])
            if completed.stdout.strip():
                lines.extend(["stdout:", completed.stdout.strip()[-4000:]])
            if completed.stderr.strip():
                lines.extend(["stderr:", completed.stderr.strip()[-4000:]])
        except Exception as exc:  # noqa: BLE001
            lines.append(f"command_error: {' '.join(command)} -> {exc}")

    bundle_dir = candidate_dir / "solver_bundle"
    if bundle_dir.exists():
        bundle_files = sorted(str(path.relative_to(bundle_dir)) for path in bundle_dir.rglob("*") if path.is_file())
        lines.append(f"solver_bundle_file_count: {len(bundle_files)}")
        lines.append("solver_bundle_files_preview:")
        lines.extend(bundle_files[:200])
        items_path = bundle_dir / "items_private_sample.jsonl"
        if items_path.exists():
            try:
                lines.append(f"solver_bundle_item_rows: {len(load_jsonl(items_path))}")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"solver_bundle_item_parse_error: {exc}")

    for score_name in ["score_gold.json", "score_wrong.json"]:
        score_path = candidate_dir / score_name
        if score_path.exists():
            try:
                summary = json.loads(score_path.read_text(encoding="utf-8"))
                lines.append(f"{score_name}: {json.dumps({k: v for k, v in summary.items() if k != 'item_results'}, ensure_ascii=True)}")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"{score_name}_parse_error: {exc}")
    return "\n".join(lines) + "\n"


def extract_jsonl(raw: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        s = line.strip()
        if not (s.startswith("{") and s.endswith("}")):
            continue
        try:
            obj = json.loads(s)
        except Exception:
            continue
        if isinstance(obj, dict) and "id" in obj and "answer" in obj and obj["id"] not in seen:
            seen.add(str(obj["id"]))
            rows.append({"id": obj["id"], "answer": obj["answer"]})
    return rows


def score_solver(candidate_dir: Path, solver_output: Path) -> str:
    rows = extract_jsonl(solver_output.read_text(encoding="utf-8"))
    predictions = candidate_dir / "predictions_solver.jsonl"
    write_jsonl(predictions, rows)
    completed = run_cmd(
        ["python3", "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_solver.jsonl", "--out", "score_solver.json"],
        candidate_dir,
        timeout=180,
    )
    report = [
        f"prediction_rows_extracted: {len(rows)}",
        f"score_returncode: {completed.returncode}",
    ]
    if completed.stdout.strip():
        report.extend(["stdout:", completed.stdout.strip()])
    if completed.stderr.strip():
        report.extend(["stderr:", completed.stderr.strip()])
    score_path = candidate_dir / "score_solver.json"
    if score_path.exists():
        report.extend(["score_solver.json:", score_path.read_text(encoding="utf-8")[:12000]])
    return "\n".join(report) + "\n"


def main() -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    candidate_dir = RUN_ROOT / f"candidate_{CANDIDATE_ID}"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []

    creator_path = RUN_ROOT / "creator_creative_bestshot.md"
    creator_result = run_codex(CREATOR_PROMPT.format(candidate_dir=candidate_dir), creator_path, effort="xhigh", cwd=ROOT)
    creator_result.update({"phase": "creator", "candidate": CANDIDATE_ID})
    manifest.append(creator_result)

    local_report = local_validate(candidate_dir)
    (RUN_ROOT / "local_validate_creative_bestshot.txt").write_text(local_report, encoding="utf-8")

    validator_path = RUN_ROOT / "validator_creative_bestshot.md"
    validator_prompt = VALIDATOR_PROMPT.format(candidate_dir=candidate_dir, local_report=local_report)
    validator_result = run_codex(validator_prompt, validator_path, effort="high", cwd=ROOT)
    validator_result.update({"phase": "validator", "candidate": CANDIDATE_ID})
    manifest.append(validator_result)
    validator_text = validator_path.read_text(encoding="utf-8") if validator_path.exists() else ""

    should_solve = (
        "FAIL" not in validator_text[:800].upper()
        and (candidate_dir / "solver_bundle" / "SOLVER_MANIFEST.json").exists()
        and (candidate_dir / "solver_bundle" / "solver_packet.md").exists()
        and (candidate_dir / "solver_bundle" / "items_private_sample.jsonl").exists()
        and (candidate_dir / "scorer.py").exists()
    )

    solver_evidence = "Solver skipped because validator failed or bundle was incomplete.\n"
    if should_solve:
        solver_dir = RUN_ROOT / "isolated_solver_bundle"
        if solver_dir.exists():
            shutil.rmtree(solver_dir)
        shutil.copytree(candidate_dir / "solver_bundle", solver_dir)
        solver_path = RUN_ROOT / "solver_creative_bestshot.jsonl"
        solver_result = run_codex(SOLVER_PROMPT, solver_path, effort="xhigh", cwd=solver_dir)
        solver_result.update({"phase": "solver", "candidate": CANDIDATE_ID})
        manifest.append(solver_result)
        solver_evidence = score_solver(candidate_dir, solver_path)
        (RUN_ROOT / "solver_score_creative_bestshot.txt").write_text(solver_evidence, encoding="utf-8")

    evidence = f"""
# BenchBench v4 Creative Evidence

## Creator

{creator_path.read_text(encoding='utf-8') if creator_path.exists() else ''}

## Local Validation

{local_report}

## Validator

{validator_text}

## Solver Evidence

{solver_evidence}
"""
    (RUN_ROOT / "judge_evidence.md").write_text(evidence, encoding="utf-8")

    judge_path = RUN_ROOT / "final_judge.md"
    judge_result = run_codex(JUDGE_PROMPT.format(evidence=evidence[:160000]), judge_path, effort="high", cwd=ROOT)
    judge_result.update({"phase": "judge", "candidate": "all"})
    manifest.append(judge_result)

    total_tokens = sum(int(item.get("tokens_used", 0)) for item in manifest)
    manifest_lines = ["# GPT-5.5 BenchBench v4 creative manifest", ""]
    for item in manifest:
        manifest_lines.append("- {phase} `{candidate}`: returncode={returncode}, tokens_used={tokens_used}, output={out_path}".format(**item))
    manifest_lines.extend(["", f"Total GPT-5.5 Codex calls: {len(manifest)}", f"Total reported tokens used: {total_tokens}", f"Solver attempted: {'yes' if should_solve else 'no'}"])
    (RUN_ROOT / "manifest.md").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(RUN_ROOT)


if __name__ == "__main__":
    main()
