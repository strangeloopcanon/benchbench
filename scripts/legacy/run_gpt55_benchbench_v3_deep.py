#!/usr/bin/env python3
"""BenchBench v3 deep GPT-5.5 run.

This run gives GPT-5.5 a stronger research-informed creator prompt and asks for
one best-shot benchmark package designed to beat a tool-enabled GPT-5.5 solver.
It enforces a solver bundle so the blind solver sees only the intended files.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ROOT / "runs" / f"gpt55_benchbench_v3_deep_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
MODEL = "gpt-5.5"
CANDIDATE_ID = "deep_residual_bestshot"

REQUIRED_ROOT_FILES = [
    "README.md",
    "benchmark_spec.json",
    "generator.py",
    "verifier.py",
    "scorer.py",
    "items_dev.jsonl",
    "items_private_pool.jsonl",
    "items_private_sample.jsonl",
    "gold_private_pool.jsonl",
    "gold_private_sample.jsonl",
    "validation_report.md",
    "adversarial_selection_report.md",
    "failure_modes.md",
]

REQUIRED_BUNDLE_FILES = [
    "SOLVER_MANIFEST.json",
    "solver_packet.md",
    "items_private_sample.jsonl",
]


RESEARCH_DIGEST = """
Research digest for BenchBench creator:

Existing benchmark families and what they cover:
- MMLU/MMLU-Pro: broad static academic/professional knowledge; saturates and is contamination-prone.
- GPQA/HLE/FrontierMath: expert-written hard closed-answer knowledge/math; strong human baselines and originality matter.
- AIME/MATH/math contests: symbolic/contest reasoning; now heavily optimized and increasingly saturated at the frontier.
- SWE-bench/LiveCodeBench: executable coding and repair; strong because scoring is functional, but strongly correlated with code ability.
- LiveBench: contamination-resistant live refresh across math, coding, instruction following, data analysis, language, and reasoning.
- BFCL/TAU Bench/tool evals: function calling, multi-turn tool use, and workflow execution.
- OSWorld/WebArena/WebVoyager/ScreenSpot: computer/browser/GUI operation with environment state and brittle real-world workflows.
- Chatbot Arena/Arena-Hard/MT-Bench: preference and open-ended instruction following; useful but judge/human preference can confound style.
- MLE-bench/RE-Bench: long-horizon ML/research engineering under budgeted scaffolds; high construct validity but expensive.

Benchmark quality lessons:
- A benchmark is not just hard prompts. It needs a construct claim, item sourcing, scoring, human baseline, contamination plan, statistics, and update process.
- Broken golds or ambiguous tasks score zero no matter how many models fail.
- Reversals are useful only if they reveal an interpretable skill, not bad graders or noise.
- Benchmark^2-style quality metrics include cross-benchmark ranking consistency, discriminability, and capability-alignment deviations.
- Correlation analyses show many benchmarks positively correlate, especially within math/code/science families; a useful new benchmark should add residual information after controlling for the usual basket.
- The recent "LLM rankings are not a ladder" graph/thread suggests benchmark-specific weak-over-strong reversals are common; BenchBench should treat them as hypotheses requiring validity checks, not automatic wins.

Previous BenchBench findings:
- V1: GPT-5.5 produced interesting benchmark ideas but hand-written golds were unreliable.
- V2: forcing generator/verifier/scorer packages fixed much of the validity problem.
- V2 failure: three verified deterministic text/JSON benchmarks were solved almost perfectly by GPT-5.5+Codex: 30/30, 30/30, and 29/30.
- Main lesson: a tool-enabled GPT-5.5 solver can write scripts, parse JSON, brute-force small search spaces, and recompute visible deterministic rules. Do not rely on arithmetic burden, large tables, or visible finite-state transformations.

Target for this run:
- Build the one best benchmark package you can.
- Think deeply before choosing the construct. Consider genuinely under-covered axes: tacit ambiguity detection, evidence provenance under conflicting authority, process-control judgment, adversarial benchmark-quality auditing, hidden assumption repair, causal/process invariants under distribution shift, real-world operational judgment with abstention, or another better axis you discover.
- You may use search, but the final benchmark items should be self-contained/private and mechanically gradable.
- Purpose: beat GPT-5.5+Codex if possible, while staying valid and human-solvable.
"""


CREATOR_PROMPT = """
You are GPT-5.5 running inside Codex as a BenchBench creator in v3 deep mode.

Assigned artifact directory:
{candidate_dir}

You have one job: construct the best possible new benchmark package that a
tool-enabled GPT-5.5+Codex solver will struggle to beat, while the package
remains valid, human-solvable, objectively gradable, and reproducible.

Before building, think deeply about the benchmark landscape and choose a
capability axis that is genuinely new, interesting, and under-covered. Do not
just make a harder MMLU/AIME/SWE-bench variant. Do not make a visible deterministic
toy system that Codex can solve by scripting.

{research_digest}

Required root files:
- README.md
- benchmark_spec.json
- generator.py
- verifier.py
- scorer.py
- items_dev.jsonl
- items_private_pool.jsonl
- items_private_sample.jsonl
- gold_private_pool.jsonl
- gold_private_sample.jsonl
- validation_report.md
- adversarial_selection_report.md
- failure_modes.md

Required isolated solver bundle:
- solver_bundle/SOLVER_MANIFEST.json
- solver_bundle/solver_packet.md
- solver_bundle/items_private_sample.jsonl

The blind solver will receive only `solver_bundle/`.

Strict CLI contract from the candidate directory:
- `python3 generator.py --pool-count 120 --sample-count 30 --seed 20260515 --out-dir .`
- `python3 verifier.py --items items_private_sample.jsonl --gold gold_private_sample.jsonl`
- `python3 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

Strict data contract:
- item rows: JSONL with `id` plus solver-visible fields only.
- gold rows: JSONL with `id` and `answer`.
- predictions: JSONL with exactly `id` and `answer`.
- scorer: deterministic per-item exact correctness, with a summary JSON.
- solver bundle must include all information needed to solve, but no gold,
  oracle, generator logic, verifier logic, score files, prior predictions, or
  validation reports.

Hard requirements:
1. Generate a larger verified private pool, then select the 30-item sample.
2. Verify unique gold answers and reject ambiguous/impossible/duplicate items.
3. Run at least one baseline or heuristic solver over the pool.
4. Select sample items that the baseline fails or finds hard for interpretable reasons.
5. Explicitly explain why the task should remain hard for GPT-5.5+Codex with tools.
6. Keep the benchmark human-solvable: describe the qualified-human protocol.
7. Run generator, verifier, gold scorer, wrong/dummy scorer, and your baseline before finishing.
8. If your best honest result is "this probably still will not beat GPT-5.5+Codex," say that in the reports, but still build the strongest valid package you can.

Use the workspace and search if useful. Final response should be brief:
artifact path, chosen capability, commands run, validation status, expected failure mode.
"""


VALIDATOR_PROMPT = """
You are GPT-5.5 acting as the BenchBench v3 package validator.

Candidate directory:
{candidate_dir}

Local validation report:
{local_report}

Validate the package. You may run commands. Do not solve the benchmark.

Check:
1. Required root files exist.
2. Required solver bundle files exist.
3. Solver bundle contains all private sample items and no gold/oracle/leakage.
4. Generator runs with the strict CLI contract.
5. Verifier runs and checks uniqueness/validity.
6. Scorer runs on gold predictions and wrong predictions.
7. There is a real adversarial selection report, not just a claim.
8. The claimed capability is not just a duplicate of MMLU/GPQA/AIME/SWE-bench/LiveBench/BFCL/OSWorld.
9. Estimate whether a short script can solve the task from the visible solver bundle.

Return:
- PASS / FAIL / CONDITIONAL
- command outputs or summarized results
- leakage/isolation finding
- validity risks
- predicted GPT-5.5+Codex hardness
- whether it should be sent to blind solver
"""


SOLVER_PROMPT = """
You are GPT-5.5+Codex acting as a blind BenchBench solver.

You are in a directory that contains only the solver-visible bundle. You may use
local computation inside this directory, but you must not inspect parent
directories or any files outside the solver bundle. Do not browse.

Solve every item. Return only JSONL, one object per item, with exactly:
{{"id": "...", "answer": ...}}

Follow the output schema in `SOLVER_MANIFEST.json` and `solver_packet.md`.
"""


JUDGE_PROMPT = """
You are GPT-5.5 acting as the final BenchBench v3 judge.

Evidence:
{evidence}

Be strict:
- Broken golds or ambiguity score zero.
- Incomplete solver bundles score zero.
- A clean benchmark solved by GPT-5.5+Codex is useful but not frontier-resistant.
- The only thing that counts as "beat GPT-5.5" is a real scorer-measured failure rate on verified items.

Return:
1. compact score table
2. whether the candidate is accepted as frontier-resistant
3. what benchmark was built and what it measures
4. why GPT-5.5+Codex succeeded or failed
5. exact setup lessons for the next BenchBench run
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


def run_codex(
    prompt: str,
    out_path: Path,
    *,
    search: bool = False,
    effort: str = "high",
    cwd: Path | None = None,
) -> dict[str, object]:
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


def local_validate(candidate_dir: Path) -> str:
    lines: list[str] = []
    missing_root = [name for name in REQUIRED_ROOT_FILES if not (candidate_dir / name).exists()]
    missing_bundle = [name for name in REQUIRED_BUNDLE_FILES if not (candidate_dir / "solver_bundle" / name).exists()]
    lines.append(f"missing_root_files: {missing_root if missing_root else 'none'}")
    lines.append(f"missing_solver_bundle_files: {missing_bundle if missing_bundle else 'none'}")

    generator_cmd = [
        "python3",
        "generator.py",
        "--pool-count",
        "120",
        "--sample-count",
        "30",
        "--seed",
        "20260515",
        "--out-dir",
        ".",
    ]
    if (candidate_dir / "generator.py").exists():
        try:
            completed = run_cmd(generator_cmd, candidate_dir, timeout=120)
            lines.extend([f"command: {' '.join(generator_cmd)}", f"returncode: {completed.returncode}"])
            if completed.stdout.strip():
                lines.extend(["stdout:", completed.stdout.strip()[-4000:]])
            if completed.stderr.strip():
                lines.extend(["stderr:", completed.stderr.strip()[-4000:]])
        except Exception as exc:  # noqa: BLE001
            lines.append(f"generator_error: {exc}")
    else:
        lines.append("generator_skipped: missing")

    gold_path = candidate_dir / "gold_private_sample.jsonl"
    if gold_path.exists():
        try:
            gold_rows = load_jsonl(gold_path)
            lines.append(f"gold_rows: {len(gold_rows)}")
            write_jsonl(
                candidate_dir / "predictions_gold.jsonl",
                [{"id": row.get("id"), "answer": row.get("answer")} for row in gold_rows],
            )
            write_jsonl(
                candidate_dir / "predictions_wrong.jsonl",
                [{"id": row.get("id"), "answer": {"__wrong__": True}} for row in gold_rows],
            )
            lines.append("prediction_fixtures: wrote predictions_gold.jsonl and predictions_wrong.jsonl")
        except Exception as exc:  # noqa: BLE001
            lines.append(f"gold_parse_error: {exc}")

    commands = [
        ["python3", "verifier.py", "--items", "items_private_sample.jsonl", "--gold", "gold_private_sample.jsonl"],
        ["python3", "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_gold.jsonl", "--out", "score_gold.json"],
        ["python3", "scorer.py", "--gold", "gold_private_sample.jsonl", "--predictions", "predictions_wrong.jsonl", "--out", "score_wrong.json"],
    ]
    for command in commands:
        if not (candidate_dir / command[1]).exists():
            lines.append(f"command_skipped: {' '.join(command)}")
            continue
        try:
            completed = run_cmd(command, candidate_dir, timeout=120)
            lines.extend([f"command: {' '.join(command)}", f"returncode: {completed.returncode}"])
            if completed.stdout.strip():
                lines.extend(["stdout:", completed.stdout.strip()[-4000:]])
            if completed.stderr.strip():
                lines.extend(["stderr:", completed.stderr.strip()[-4000:]])
        except Exception as exc:  # noqa: BLE001
            lines.append(f"command_error: {' '.join(command)} -> {exc}")

    for score_name in ["score_gold.json", "score_wrong.json"]:
        score_path = candidate_dir / score_name
        if score_path.exists():
            try:
                lines.append(f"{score_name}: {json.dumps(json.loads(score_path.read_text(encoding='utf-8')), ensure_ascii=True)[:4000]}")
            except Exception as exc:  # noqa: BLE001
                lines.append(f"{score_name}_parse_error: {exc}")

    bundle_items = candidate_dir / "solver_bundle" / "items_private_sample.jsonl"
    if bundle_items.exists():
        try:
            lines.append(f"solver_bundle_item_rows: {len(load_jsonl(bundle_items))}")
        except Exception as exc:  # noqa: BLE001
            lines.append(f"solver_bundle_item_parse_error: {exc}")

    return "\n".join(lines) + "\n"


def extract_jsonl(text: str) -> str:
    rows: list[str] = []
    in_fence = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not line or not line.startswith("{") or not line.endswith("}"):
            continue
        try:
            rows.append(json.dumps(json.loads(line), ensure_ascii=True))
        except Exception:
            continue
    return "\n".join(rows) + ("\n" if rows else "")


def score_solver(candidate_dir: Path, raw_solver_path: Path) -> str:
    predictions_path = candidate_dir / "predictions_solver.jsonl"
    predictions_path.write_text(extract_jsonl(raw_solver_path.read_text(encoding="utf-8")), encoding="utf-8")
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
        timeout=120,
    )
    lines = [
        f"raw_solver_output: {raw_solver_path}",
        f"extracted_predictions: {predictions_path}",
        f"score_returncode: {completed.returncode}",
    ]
    if completed.stdout.strip():
        lines.extend(["stdout:", completed.stdout.strip()])
    if completed.stderr.strip():
        lines.extend(["stderr:", completed.stderr.strip()])
    score_path = candidate_dir / "score_solver.json"
    if score_path.exists():
        lines.extend(["score_solver.json:", score_path.read_text(encoding="utf-8")[:8000]])
    lines.extend(["prediction_preview:", predictions_path.read_text(encoding="utf-8")[:8000]])
    return "\n".join(lines) + "\n"


def make_solver_run_dir(candidate_dir: Path) -> Path:
    solver_run_dir = RUN_ROOT / "isolated_solver_bundle"
    if solver_run_dir.exists():
        shutil.rmtree(solver_run_dir)
    shutil.copytree(candidate_dir / "solver_bundle", solver_run_dir)
    return solver_run_dir


def main() -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    candidate_dir = RUN_ROOT / f"candidate_{CANDIDATE_ID}"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []

    creator_prompt = CREATOR_PROMPT.format(candidate_dir=candidate_dir, research_digest=RESEARCH_DIGEST.strip())
    creator_path = RUN_ROOT / "creator_deep_residual_bestshot.md"
    creator_result = run_codex(creator_prompt, creator_path, search=True, effort="xhigh", cwd=ROOT)
    creator_result.update({"phase": "creator", "candidate": CANDIDATE_ID})
    manifest.append(creator_result)

    local_report = local_validate(candidate_dir)
    (RUN_ROOT / "local_validate_deep_residual_bestshot.txt").write_text(local_report, encoding="utf-8")

    validator_prompt = VALIDATOR_PROMPT.format(candidate_dir=candidate_dir, local_report=local_report)
    validator_path = RUN_ROOT / "validator_deep_residual_bestshot.md"
    validator_result = run_codex(validator_prompt, validator_path, search=False, effort="high", cwd=ROOT)
    validator_result.update({"phase": "validator", "candidate": CANDIDATE_ID})
    manifest.append(validator_result)

    validator_text = validator_path.read_text(encoding="utf-8") if validator_path.exists() else ""
    should_solve = (
        "FAIL" not in validator_text[:700].upper()
        and (candidate_dir / "solver_bundle" / "solver_packet.md").exists()
        and (candidate_dir / "solver_bundle" / "items_private_sample.jsonl").exists()
        and (candidate_dir / "scorer.py").exists()
    )

    solver_evidence = "Solver skipped because validation failed or solver bundle was incomplete.\n"
    if should_solve:
        solver_run_dir = make_solver_run_dir(candidate_dir)
        solver_path = RUN_ROOT / "solver_deep_residual_bestshot.jsonl"
        solver_result = run_codex(SOLVER_PROMPT, solver_path, search=False, effort="xhigh", cwd=solver_run_dir)
        solver_result.update({"phase": "solver", "candidate": CANDIDATE_ID})
        manifest.append(solver_result)
        solver_evidence = score_solver(candidate_dir, solver_path)
        (RUN_ROOT / "solver_score_deep_residual_bestshot.txt").write_text(solver_evidence, encoding="utf-8")

    evidence = f"""
# BenchBench v3 Deep Run Evidence

## Creator output

{creator_path.read_text(encoding='utf-8') if creator_path.exists() else ''}

## Local validation

{local_report}

## GPT validator

{validator_text}

## Solver evidence

{solver_evidence}
"""
    evidence_path = RUN_ROOT / "judge_evidence.md"
    evidence_path.write_text(evidence, encoding="utf-8")

    judge_path = RUN_ROOT / "final_judge.md"
    judge_result = run_codex(JUDGE_PROMPT.format(evidence=evidence[:140000]), judge_path, search=False, effort="high", cwd=ROOT)
    judge_result.update({"phase": "judge", "candidate": "all"})
    manifest.append(judge_result)

    total_tokens = sum(int(row.get("tokens_used", 0)) for row in manifest)
    manifest_lines = ["# GPT-5.5 BenchBench v3 deep manifest", ""]
    for row in manifest:
        manifest_lines.append(
            "- {phase} `{candidate}`: returncode={returncode}, tokens_used={tokens_used}, output={out_path}".format(**row)
        )
    manifest_lines.extend(
        [
            "",
            f"Total GPT-5.5 Codex calls: {len(manifest)}",
            f"Total reported tokens used: {total_tokens}",
            f"Solver attempted: {'yes' if should_solve else 'no'}",
        ]
    )
    (RUN_ROOT / "manifest.md").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(RUN_ROOT)


if __name__ == "__main__":
    main()
