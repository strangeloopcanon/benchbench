#!/usr/bin/env python3
"""BenchBench v2 constructor experiment.

This run asks GPT-5.5-in-Codex to construct benchmark packages with runnable
generators, verifiers, and scorers. It then validates, solves, scores, and
judges the candidates.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "runs" / f"gpt55_benchbench_v2_constructor_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
MODEL = "gpt-5.5"
REQUIRED_FILES = [
    "README.md",
    "benchmark_spec.json",
    "generator.py",
    "verifier.py",
    "scorer.py",
    "items_dev.jsonl",
    "items_private_sample.jsonl",
    "solver_packet.md",
    "gold_private_sample.jsonl",
    "validation_report.md",
    "failure_modes.md",
]


CREATOR_VARIANTS = [
    {
        "id": "constraint_delta_hard",
        "search": False,
        "instruction": """
        Build the best possible verified version of the v1 winner:
        Constraint Delta Repair. It should test minimal downstream edits after a
        local change to an operational spec/config/policy. Make it harder than
        v1 by requiring 2-4 dependent edits, decoys that mention changed
        concepts but must not be edited, and exact required/forbidden edit sets.
        """,
    },
    {
        "id": "state_machine_residual",
        "search": False,
        "instruction": """
        Build a different mechanically verifiable residual benchmark based on
        small state machines, ledgers, rule systems, schedules, or access
        matrices. Avoid hand-written golds. The verifier must prove uniqueness
        or exhaustively reject non-unique items.
        """,
    },
    {
        "id": "web_grounded_residual",
        "search": True,
        "instruction": """
        Use web search only if helpful. Build a benchmark around a real-world
        work capability that common evals miss, but keep all items synthetic and
        mechanically gradable. Prioritize a robust generator/verifier/scorer over
        novelty theater.
        """,
    },
]


CREATOR_PROMPT = """
You are GPT-5.5 running inside Codex as a BenchBench creator in constructor mode.

This is not a prose-only benchmark-writing task. You must create a runnable
benchmark package in the assigned artifact directory.

Assigned artifact directory:
{candidate_dir}

Variant instruction:
{variant_instruction}

Context from the previous v1 pilot:
- GPT-5.5 generated promising benchmark concepts but often broke gold keys.
- The best v1 concept was Constraint Delta Repair: given an old operational spec
  and a local change request, return the minimal downstream edits while
  preserving unaffected constraints.
- GPT-5.5 solved the v1 sample set 5/5, so v2 needs verified harder items.
- Broken gold answers, ambiguity, or alternate valid answers must score zero.

Goal:
Construct a benchmark that reveals validated residual signal not well predicted
by standard evals, while remaining human-solvable, objectively gradable,
contamination-resistant, and hard for GPT-5.5-class solvers.

Standard benchmark basket to consider:
MMLU/MMLU-Pro, GPQA, AIME/math contest evals, SWE-bench/code repair, LiveBench,
LiveCodeBench, Chatbot Arena/Arena-Hard, BFCL/tool calling, OSWorld.

Required files in the artifact directory:
- README.md
- benchmark_spec.json
- generator.py
- verifier.py
- scorer.py
- items_dev.jsonl
- items_private_sample.jsonl
- solver_packet.md
- gold_private_sample.jsonl
- validation_report.md
- failure_modes.md

Strict CLI contract:
- `python3 generator.py --count 30 --seed 12345 --items items_private_sample.jsonl --gold gold_private_sample.jsonl --solver solver_packet.md`
- `python3 verifier.py --items items_private_sample.jsonl --gold gold_private_sample.jsonl`
- `python3 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

Strict data contract:
- `items_private_sample.jsonl`: one JSON object per item, including at least `id` and solver-visible fields.
- `gold_private_sample.jsonl`: one JSON object per item, including at least `id` and `answer`.
- `predictions.jsonl`: one JSON object per item, including exactly `id` and `answer`.
- `solver_packet.md`: must instruct blind solvers to return only JSONL with `id` and `answer`.

Hard requirements:
1. No hand-written private items unless generated/verified by your scripts.
2. Every private item must have one unique valid gold answer under the stated rules.
3. `verifier.py` must reject ambiguous, impossible, duplicate, and alternate-minimal-solution items.
4. `scorer.py` must be deterministic and must score exact correctness per item.
5. The solver packet must not leak gold answers.
6. Add decoys only when the verifier can prove they do not introduce alternate answers.
7. Run the generator, verifier, and scorer yourself before finishing.
8. Include the commands and results in `validation_report.md`.

Suggested artifact quality bar:
- At least 30 private sample items.
- At least 5 dev items.
- Items should be compact enough for a blind solver call but harder than v1.
- The expected failure mode should be a real capability miss: missed dependency,
  over-editing, stale derived value, wrong invariant, invalid minimality, etc.

If you cannot satisfy the required artifact contract, create `FAILED_CANDIDATE.md`
in the artifact directory explaining why.

Do the work now. You may write files and run commands. Final response should be
brief: artifact path, commands run, pass/fail, and what you believe the benchmark
measures.
"""


VALIDATOR_PROMPT = """
You are GPT-5.5 acting as the BenchBench package validator.

Candidate directory:
{candidate_dir}

Local structural check report:
{local_report}

Inspect the artifact directory. You may run commands. Do not solve private items
as a benchmark solver. Validate the package structure, generator, verifier,
scorer, gold format, and leakage risk.

Required commands to try:
- python3 generator.py --count 30 --seed 12345 --items items_private_sample.jsonl --gold gold_private_sample.jsonl --solver solver_packet.md
- python3 verifier.py --items items_private_sample.jsonl --gold gold_private_sample.jsonl
- python3 scorer.py --gold gold_private_sample.jsonl --predictions predictions_gold.jsonl --out score_gold.json
- python3 scorer.py --gold gold_private_sample.jsonl --predictions predictions_wrong.jsonl --out score_wrong.json

Return:
- PASS / FAIL / CONDITIONAL
- command outputs or summarized results
- structural issues
- validity risks
- whether it is ready for a blind GPT-5.5 solver run
"""


SOLVER_PROMPT = """
You are GPT-5.5 acting as a blind BenchBench solver.

Candidate id: {candidate_id}

You receive only the solver-visible packet below. Do not inspect files, golds,
generator code, verifier code, scorer code, or validation reports. Do not browse.

Return only JSONL, one object per item, with exactly:
{{"id": "...", "answer": ...}}

The `answer` value must follow the solver packet's requested answer format.

<solver_packet>
{solver_packet}
</solver_packet>
"""


JUDGE_PROMPT = """
You are GPT-5.5 acting as the final BenchBench judge.

Use the evidence below to decide what worked. Be strict:
- broken golds score zero
- invalid ambiguity scores zero
- a clean benchmark solved by GPT-5.5 is useful but not frontier-resistant
- a benchmark only counts as working against GPT-5.5 if the scorer shows a real
  failure rate on verified items

Evidence:
{evidence}

Return:
1. compact score table
2. best candidate and why
3. whether any candidate is frontier-resistant in this pilot
4. exact prompt/setup lessons
5. recommended next run
"""


def run_cmd(args: list[str], cwd: Path, stdin_text: str | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def run_codex(prompt: str, out_path: Path, *, search: bool = False, effort: str = "high", cwd: Path | None = None) -> dict[str, object]:
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
    if search:
        cmd.insert(1, "--search")
    completed = run_cmd(cmd, cwd, stdin_text=prompt, timeout=None)
    stdout_path = out_path.with_suffix(".stdout.txt")
    stderr_path = out_path.with_suffix(".stderr.txt")
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return {
        "returncode": completed.returncode,
        "tokens_used": parse_tokens(completed.stdout + "\n" + completed.stderr),
        "out_path": str(out_path),
        "prompt_path": str(prompt_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }


def parse_tokens(text: str) -> int:
    matches = re.findall(r"tokens used\s+(\d[\d,]*)", text)
    if not matches:
        return 0
    return int(matches[-1].replace(",", ""))


def load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def local_validate_candidate(candidate_dir: Path) -> str:
    lines: list[str] = []
    missing = [name for name in REQUIRED_FILES if not (candidate_dir / name).exists()]
    lines.append(f"missing_files: {missing if missing else 'none'}")

    generator_command = [
        "python3",
        "generator.py",
        "--count",
        "30",
        "--seed",
        "12345",
        "--items",
        "items_private_sample.jsonl",
        "--gold",
        "gold_private_sample.jsonl",
        "--solver",
        "solver_packet.md",
    ]
    if (candidate_dir / "generator.py").exists():
        try:
            completed = run_cmd(generator_command, candidate_dir, timeout=60)
            lines.append(f"command: {' '.join(generator_command)}")
            lines.append(f"returncode: {completed.returncode}")
            if completed.stdout.strip():
                lines.append("stdout:")
                lines.append(completed.stdout.strip()[-4000:])
            if completed.stderr.strip():
                lines.append("stderr:")
                lines.append(completed.stderr.strip()[-4000:])
        except Exception as exc:  # noqa: BLE001
            lines.append(f"command_error: {' '.join(generator_command)} -> {exc}")
    else:
        lines.append("command_skipped: generator.py missing")

    gold_path = candidate_dir / "gold_private_sample.jsonl"
    if gold_path.exists():
        try:
            gold_rows = load_jsonl(gold_path)
            lines.append(f"gold_rows: {len(gold_rows)}")
            gold_predictions = [
                {"id": row.get("id"), "answer": row.get("answer")}
                for row in gold_rows
                if "id" in row and "answer" in row
            ]
            wrong_predictions = [
                {"id": row.get("id"), "answer": "__BENCHBENCH_WRONG__"}
                for row in gold_rows
                if "id" in row
            ]
            write_jsonl(candidate_dir / "predictions_gold.jsonl", gold_predictions)
            write_jsonl(candidate_dir / "predictions_wrong.jsonl", wrong_predictions)
            lines.append(f"prediction_fixtures: wrote {len(gold_predictions)} gold and {len(wrong_predictions)} wrong")
        except Exception as exc:  # noqa: BLE001
            lines.append(f"gold_parse_error: {exc}")

    commands = [
        ["python3", "verifier.py", "--items", "items_private_sample.jsonl", "--gold", "gold_private_sample.jsonl"],
        ["python3", "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_gold.jsonl", "--out", "score_gold.json"],
        ["python3", "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_wrong.jsonl", "--out", "score_wrong.json"],
    ]
    for cmd in commands:
        if not (candidate_dir / cmd[1]).exists():
            lines.append(f"command_skipped: {' '.join(cmd)} missing {cmd[1]}")
            continue
        try:
            completed = run_cmd(cmd, candidate_dir, timeout=60)
            lines.append(f"command: {' '.join(cmd)}")
            lines.append(f"returncode: {completed.returncode}")
            if completed.stdout.strip():
                lines.append("stdout:")
                lines.append(completed.stdout.strip()[-4000:])
            if completed.stderr.strip():
                lines.append("stderr:")
                lines.append(completed.stderr.strip()[-4000:])
        except Exception as exc:  # noqa: BLE001
            lines.append(f"command_error: {' '.join(cmd)} -> {exc}")

    for score_name in ["score_gold.json", "score_wrong.json"]:
        score_path = candidate_dir / score_name
        if score_path.exists():
            try:
                lines.append(f"{score_name}: {json.dumps(json.loads(score_path.read_text(encoding='utf-8')), ensure_ascii=True)[:2000]}")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"{score_name}_parse_error: {exc}")

    return "\n".join(lines) + "\n"


def score_solver_output(candidate_dir: Path, solver_output_path: Path) -> str:
    raw = solver_output_path.read_text(encoding="utf-8")
    predictions_path = candidate_dir / "predictions_solver.jsonl"
    predictions_path.write_text(extract_jsonl(raw), encoding="utf-8")
    completed = run_cmd(
        [
            "python3",
            "scorer.py",
            "--gold",
            "gold_private_sample.jsonl",
            "--predictions",
            "predictions_solver.jsonl",
            "--out",
            "score_solver.json",
        ],
        candidate_dir,
        timeout=60,
    )
    report = [
        f"candidate_dir: {candidate_dir}",
        f"solver_output: {solver_output_path}",
        f"score_returncode: {completed.returncode}",
    ]
    if completed.stdout.strip():
        report.extend(["stdout:", completed.stdout.strip()])
    if completed.stderr.strip():
        report.extend(["stderr:", completed.stderr.strip()])
    score_path = candidate_dir / "score_solver.json"
    if score_path.exists():
        report.extend(["score_solver.json:", score_path.read_text(encoding="utf-8")[:4000]])
    report.extend(["extracted_predictions:", predictions_path.read_text(encoding="utf-8")[:4000]])
    return "\n".join(report) + "\n"


def extract_jsonl(text: str) -> str:
    lines: list[str] = []
    in_fence = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not line:
            continue
        if line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            lines.append(json.dumps(obj, ensure_ascii=True))
    return "\n".join(lines) + ("\n" if lines else "")


def main() -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    evidence_chunks: list[str] = []
    validated_candidates: list[tuple[str, Path]] = []

    # Creator phase.
    for variant in CREATOR_VARIANTS:
        variant_id = str(variant["id"])
        candidate_dir = RUN_ROOT / f"candidate_{variant_id}"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        prompt = CREATOR_PROMPT.format(
            candidate_dir=candidate_dir,
            variant_instruction=str(variant["instruction"]).strip(),
        )
        out_path = RUN_ROOT / f"creator_{variant_id}.md"
        result = run_codex(prompt, out_path, search=bool(variant["search"]), effort="high", cwd=ROOT)
        result.update({"phase": "creator", "candidate": variant_id})
        manifest.append(result)

        local_report = local_validate_candidate(candidate_dir)
        local_report_path = RUN_ROOT / f"local_validate_{variant_id}.txt"
        local_report_path.write_text(local_report, encoding="utf-8")

        validator_prompt = VALIDATOR_PROMPT.format(candidate_dir=candidate_dir, local_report=local_report)
        validator_path = RUN_ROOT / f"validator_{variant_id}.md"
        validator_result = run_codex(validator_prompt, validator_path, search=False, effort="medium", cwd=ROOT)
        validator_result.update({"phase": "validator", "candidate": variant_id})
        manifest.append(validator_result)

        validator_text = validator_path.read_text(encoding="utf-8") if validator_path.exists() else ""
        evidence_chunks.append(f"\n\n## Candidate {variant_id}\n\n### Creator final\n\n{out_path.read_text(encoding='utf-8') if out_path.exists() else ''}\n\n### Local validation\n\n{local_report}\n\n### GPT validation\n\n{validator_text}")
        if "FAIL" not in validator_text[:500].upper() and (candidate_dir / "solver_packet.md").exists() and (candidate_dir / "scorer.py").exists():
            validated_candidates.append((variant_id, candidate_dir))

    # Solver phase.
    for variant_id, candidate_dir in validated_candidates:
        solver_packet = (candidate_dir / "solver_packet.md").read_text(encoding="utf-8")
        solver_prompt = SOLVER_PROMPT.format(candidate_id=variant_id, solver_packet=solver_packet)
        solver_path = RUN_ROOT / f"solver_{variant_id}.jsonl"
        solver_result = run_codex(solver_prompt, solver_path, search=False, effort="high", cwd=ROOT)
        solver_result.update({"phase": "solver", "candidate": variant_id})
        manifest.append(solver_result)
        score_report = score_solver_output(candidate_dir, solver_path)
        score_report_path = RUN_ROOT / f"solver_score_{variant_id}.txt"
        score_report_path.write_text(score_report, encoding="utf-8")
        evidence_chunks.append(f"\n\n## Solver {variant_id}\n\n### Solver output\n\n{solver_path.read_text(encoding='utf-8') if solver_path.exists() else ''}\n\n### Solver scoring\n\n{score_report}")

    if not validated_candidates:
        evidence_chunks.append("\n\n## Solver phase\n\nNo candidates passed validation gating well enough for a blind solver run.")

    # Final judge.
    evidence = "\n".join(evidence_chunks)
    evidence_path = RUN_ROOT / "judge_evidence.md"
    evidence_path.write_text(evidence, encoding="utf-8")
    judge_prompt = JUDGE_PROMPT.format(evidence=evidence[:120000])
    judge_path = RUN_ROOT / "final_judge.md"
    judge_result = run_codex(judge_prompt, judge_path, search=False, effort="high", cwd=ROOT)
    judge_result.update({"phase": "judge", "candidate": "all"})
    manifest.append(judge_result)

    total_tokens = sum(int(item.get("tokens_used", 0)) for item in manifest)
    manifest_lines = ["# GPT-5.5 BenchBench v2 constructor manifest", ""]
    for item in manifest:
        manifest_lines.append(
            "- {phase} `{candidate}`: returncode={returncode}, tokens_used={tokens_used}, output={out_path}".format(**item)
        )
    manifest_lines.append("")
    manifest_lines.append(f"Total GPT-5.5 Codex calls: {len(manifest)}")
    manifest_lines.append(f"Total reported tokens used: {total_tokens}")
    manifest_lines.append(f"Validated candidates sent to solver: {', '.join(v for v, _ in validated_candidates) if validated_candidates else 'none'}")
    (RUN_ROOT / "manifest.md").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(RUN_ROOT)


if __name__ == "__main__":
    main()
