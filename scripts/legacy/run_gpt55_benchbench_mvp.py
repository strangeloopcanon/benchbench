#!/usr/bin/env python3
"""Small Codex/GPT-5.5 BenchBench MVP runner.

This intentionally uses Codex CLI calls instead of direct API calls, because the
experiment is about whether the local Codex -> GPT-5.5 path can generate and
then stress-test benchmark packages.
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NOTE_PATH = ROOT / "benchbench_research_notes.md"
RUN_ROOT = ROOT / "runs" / f"gpt55_benchbench_mvp_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
MODEL = "gpt-5.5"


VARIANTS = [
    {
        "id": "baseline_valid_hard",
        "search": False,
        "instruction": """
        Design the strongest valid benchmark you can for BenchBench.
        Optimize for: human-solvable, frontier-resistant, objectively gradable,
        and plausibly useful. Do not optimize for decorrelation directly.
        """,
    },
    {
        "id": "residual_axis",
        "search": False,
        "instruction": """
        Design a benchmark whose scores would have low predictability from the
        standard eval basket (MMLU/MMLU-Pro, GPQA, AIME, SWE-bench, LiveBench,
        Arena, BFCL, OSWorld), while still measuring a real named capability.
        Optimize for validated residual signal rather than pure hardness.
        """,
    },
    {
        "id": "anticorrelation_guarded",
        "search": False,
        "instruction": """
        Try to create a benchmark that could be anticorrelated with major evals,
        but only if the anticorrelation is legitimate. Explicitly avoid failure
        modes: reversed labels, obscure trivia, prompt-format traps, ungradeable
        rubrics, or rewarding weak models by accident.
        """,
    },
    {
        "id": "web_augmented_residual",
        "search": True,
        "instruction": """
        You may use web search if it helps. Design a benchmark that targets a
        real-world residual capability missing from common evals. It should be
        cheap to pilot, objectively gradable, and hard for GPT-5.5-like models.
        """,
    },
]


GENERATOR_TEMPLATE = """
You are GPT-5.5 running inside Codex. We are testing whether GPT-5.5 can design
new benchmarks for BenchBench.

Goal: propose ONE compact benchmark package that could be piloted immediately.

Background research note:
<research_note>
{research_note}
</research_note>

Specific prompt variant:
<variant_instruction>
{variant_instruction}
</variant_instruction>

Output requirements:
- Do not modify files.
- If web search is available, use it only if genuinely useful.
- Return exactly the tagged plain text sections below.
- The solver packet must not reveal gold answers.
- Provide 5 sample items. They should be hard but answerable by a qualified
  human under the stated rules.
- The gold packet must include the expected answer and grading rule for each
  item.

<proposal_summary>
title:
capability_axis:
why_existing_evals_miss_it:
expected_correlation_pattern:
human_baseline_protocol:
frontier_failure_hypothesis:
objective_grading_plan:
contamination_plan:
main_risks:
</proposal_summary>

<solver_packet>
Include the benchmark instructions and exactly 5 numbered sample items. Do not
include gold answers or hints that reveal the answer.
</solver_packet>

<gold_packet>
For each of the 5 items, give: id, expected answer, grading rule, why a qualified
human can solve it, and why GPT-5.5 may fail.
</gold_packet>

<self_critique>
Give a blunt verdict: pass/fail/uncertain against BenchBench acceptance gates,
and the top two changes needed before a real run.
</self_critique>
"""


SOLVER_TEMPLATE = """
You are GPT-5.5 running inside Codex. You are the target solver in a first-pass
BenchBench stress test.

You will receive solver-visible packets from several candidate benchmarks. Do
not assume they are fair or valid. Answer each item as best you can under the
given instructions. Also flag ambiguity, missing information, or likely invalid
benchmark design.

Important:
- You do NOT have the gold answers.
- Do not browse.
- Do not modify files.
- For every item, provide a final answer and confidence from 0.0 to 1.0.
- After each benchmark packet, say whether the benchmark seems likely to expose
  a residual capability distinct from common evals.

<candidate_solver_packets>
{solver_packets}
</candidate_solver_packets>
"""


GRADER_TEMPLATE = """
You are GPT-5.5 running inside Codex. You are grading a BenchBench MVP run.

Inputs:
1. The generated benchmark proposals, including their gold packets.
2. GPT-5.5's blind solver answers.

Tasks:
- Grade the solver answers against the gold packets.
- Decide which prompt variant produced the best BenchBench candidate.
- Judge whether each candidate likely measures validated residual signal,
  mere hardness, or invalid/brittle weirdness.
- Estimate whether GPT-5.5 beat each candidate sample set, using the available
  gold packets. A sample set "works against GPT-5.5" only if GPT-5.5 clearly
  failed at least 3 of 5 items for reasons that are not ambiguity or bad grading.
- Be strict: invalid benchmark design should score worse than a benchmark GPT-5.5
  can solve.

Return:
1. A compact score table.
2. The best candidate and why.
3. What instructions worked best.
4. What failed.
5. Recommended next experiment.

<generated_proposals>
{generated_proposals}
</generated_proposals>

<blind_solver_answers>
{solver_answers}
</blind_solver_answers>
"""


def run_codex(prompt: str, out_path: Path, *, search: bool = False) -> dict[str, str | int]:
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
        'model_reasoning_effort="low"',
        "--output-last-message",
        str(out_path),
    ]
    if search:
        cmd.insert(1, "--search")
    cmd.append("-")
    with prompt_path.open("r", encoding="utf-8") as handle:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            stdin=handle,
            text=True,
            capture_output=True,
            check=False,
        )
    log_path = out_path.with_suffix(".stdout.txt")
    err_path = out_path.with_suffix(".stderr.txt")
    log_path.write_text(completed.stdout, encoding="utf-8")
    err_path.write_text(completed.stderr, encoding="utf-8")
    combined_log = completed.stdout + "\n" + completed.stderr
    return {
        "returncode": completed.returncode,
        "tokens_used": parse_tokens_used(combined_log),
        "out_path": str(out_path),
        "prompt_path": str(prompt_path),
        "stdout_path": str(log_path),
        "stderr_path": str(err_path),
    }


def parse_tokens_used(stdout: str) -> int:
    matches = re.findall(r"tokens used\s+(\d[\d,]*)", stdout)
    if not matches:
        return 0
    return int(matches[-1].replace(",", ""))


def extract_tag(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.S)
    if not match:
        return f"[missing <{tag}> section]\n\n{text[:2000]}"
    return match.group(1).strip()


def main() -> None:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    note = NOTE_PATH.read_text(encoding="utf-8")
    manifest: list[dict[str, str | int]] = []
    generated_blocks: list[str] = []
    solver_blocks: list[str] = []

    for variant in VARIANTS:
        variant_id = str(variant["id"])
        prompt = GENERATOR_TEMPLATE.format(
            research_note=note,
            variant_instruction=textwrap.dedent(str(variant["instruction"])).strip(),
        )
        out_path = RUN_ROOT / f"generator_{variant_id}.md"
        result = run_codex(prompt, out_path, search=bool(variant["search"]))
        result["call_type"] = "generator"
        result["variant"] = variant_id
        manifest.append(result)
        text = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
        generated_blocks.append(f"\n\n## {variant_id}\n\n{text}")
        solver_packet = extract_tag(text, "solver_packet")
        solver_blocks.append(f"\n\n## {variant_id}\n\n{solver_packet}")

    solver_prompt = SOLVER_TEMPLATE.format(solver_packets="\n".join(solver_blocks))
    solver_path = RUN_ROOT / "solver_gpt55_blind.md"
    solver_result = run_codex(solver_prompt, solver_path, search=False)
    solver_result["call_type"] = "solver"
    solver_result["variant"] = "all"
    manifest.append(solver_result)

    solver_answers = solver_path.read_text(encoding="utf-8") if solver_path.exists() else ""
    grader_prompt = GRADER_TEMPLATE.format(
        generated_proposals="\n".join(generated_blocks),
        solver_answers=solver_answers,
    )
    grader_path = RUN_ROOT / "grader_gpt55_final_eval.md"
    grader_result = run_codex(grader_prompt, grader_path, search=False)
    grader_result["call_type"] = "grader"
    grader_result["variant"] = "all"
    manifest.append(grader_result)

    manifest_lines = ["# GPT-5.5 BenchBench MVP manifest", ""]
    total_tokens = 0
    for item in manifest:
        total_tokens += int(item.get("tokens_used", 0))
        manifest_lines.append(
            "- {call_type} `{variant}`: returncode={returncode}, tokens_used={tokens_used}, output={out_path}".format(
                **item
            )
        )
    manifest_lines.append("")
    manifest_lines.append(f"Total GPT-5.5 Codex calls: {len(manifest)}")
    manifest_lines.append(f"Total reported tokens used: {total_tokens}")
    (RUN_ROOT / "manifest.md").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(RUN_ROOT)


if __name__ == "__main__":
    main()
