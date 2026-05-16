#!/usr/bin/env python3
"""Build the BenchBench benchmark landscape pack.

The pack has three jobs:
- give benchmark creators a compact picture of what has already been tried;
- preserve machine-readable public score tables where available;
- normalize scores into a long table usable for rank correlations and
  regression-based novelty checks.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup
from huggingface_hub import hf_hub_download


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmark_landscape"
SOURCE_TABLES = OUT / "source_score_tables"
USER_AGENT = "Mozilla/5.0 BenchBench landscape collector"


OPENLLM_REPO = "open-llm-leaderboard/contents"
OPENLLM_PARQUET = "data/train-00000-of-00001.parquet"
OPENLLM_URL = "https://huggingface.co/datasets/open-llm-leaderboard/contents"

LMARENA_ARCHIVE_REPO = "lmarena/chatbot-arena-leaderboard"
LMARENA_ARCHIVE_FILE = "leaderboard_table_20250409.csv"
LMARENA_ARCHIVE_URL = "https://huggingface.co/spaces/lmarena/chatbot-arena-leaderboard"

ARENA_PAGES = [
    {
        "source_id": "lmarena_current_text",
        "benchmark": "arena_text_overall",
        "name": "LMArena Text Arena overall",
        "url": "https://arena.ai/leaderboard/text",
    },
    {
        "source_id": "lmarena_current_code_webdev",
        "benchmark": "arena_code_webdev_overall",
        "name": "LMArena Code Arena WebDev overall",
        "url": "https://arena.ai/leaderboard/code/webdev",
    },
    {
        "source_id": "lmarena_current_code_image_to_webdev",
        "benchmark": "arena_code_image_to_webdev_overall",
        "name": "LMArena Code Arena Image-to-WebDev overall",
        "url": "https://arena.ai/leaderboard/code/image-to-webdev",
    },
    {
        "source_id": "lmarena_current_vision",
        "benchmark": "arena_vision_overall",
        "name": "LMArena Vision Arena overall",
        "url": "https://arena.ai/leaderboard/vision",
    },
    {
        "source_id": "lmarena_current_document",
        "benchmark": "arena_document_overall",
        "name": "LMArena Document Arena overall",
        "url": "https://arena.ai/leaderboard/document",
    },
    {
        "source_id": "lmarena_current_search",
        "benchmark": "arena_search_overall",
        "name": "LMArena Search Arena overall",
        "url": "https://arena.ai/leaderboard/search",
    },
]


CATALOG: list[dict[str, str]] = [
    {
        "eval_id": "mmlu",
        "name": "MMLU",
        "family": "knowledge_exam",
        "modality": "text",
        "capability": "Broad academic and professional knowledge",
        "what_people_do": "Answer multiple-choice questions across many subjects.",
        "construction": "Static set of human-written exam-style questions.",
        "scoring": "Accuracy.",
        "benchbench_lesson": "Easy to adopt, but static broad QA saturates and is contamination-prone.",
        "source_url": "https://arxiv.org/abs/2009.03300",
    },
    {
        "eval_id": "mmlu_pro",
        "name": "MMLU-Pro",
        "family": "knowledge_exam",
        "modality": "text",
        "capability": "Harder broad knowledge and reasoning",
        "what_people_do": "Answer harder multiple-choice questions with more answer options.",
        "construction": "Cleans and extends MMLU-style items; removes noisy/trivial items.",
        "scoring": "Accuracy with prompt stability analysis.",
        "benchbench_lesson": "A new eval can be valuable by de-noising and hardening an existing construct.",
        "source_url": "https://arxiv.org/abs/2406.01574",
    },
    {
        "eval_id": "gpqa",
        "name": "GPQA",
        "family": "expert_qa",
        "modality": "text",
        "capability": "Graduate-level science reasoning",
        "what_people_do": "Answer expert-written biology, physics, and chemistry questions.",
        "construction": "Expert-authored, Google-resistant multiple-choice questions with human baselines.",
        "scoring": "Accuracy.",
        "benchbench_lesson": "Hardness is meaningful only when expert humans can solve the task.",
        "source_url": "https://arxiv.org/abs/2311.12022",
    },
    {
        "eval_id": "humanitys_last_exam",
        "name": "Humanity's Last Exam",
        "family": "expert_qa",
        "modality": "text_multimodal",
        "capability": "Frontier-level academic knowledge and reasoning",
        "what_people_do": "Answer difficult closed-ended expert questions across many fields.",
        "construction": "Expert-authored multimodal questions with verifiable answers.",
        "scoring": "Accuracy and calibration on closed-ended answers.",
        "benchbench_lesson": "Pre-screen current models, keep answers verifiable, and retain hidden/private sets.",
        "source_url": "https://arxiv.org/abs/2501.14249",
    },
    {
        "eval_id": "frontiermath",
        "name": "FrontierMath",
        "family": "expert_math",
        "modality": "text",
        "capability": "Advanced mathematical problem solving",
        "what_people_do": "Solve original expert-level math problems.",
        "construction": "Problems crafted and vetted by mathematicians; some private/hidden.",
        "scoring": "Exact answers or proof-style verification depending on item.",
        "benchbench_lesson": "Original expert problems can stay hard, but grading and QA must be exceptionally careful.",
        "source_url": "https://epoch.ai/frontiermath/the-benchmark",
    },
    {
        "eval_id": "aime",
        "name": "AIME",
        "family": "competition_math",
        "modality": "text",
        "capability": "Contest math",
        "what_people_do": "Solve short-answer high-school contest math problems.",
        "construction": "Annual math competition problems; often used by year as fresh evals.",
        "scoring": "Exact integer answer accuracy.",
        "benchbench_lesson": "Recent public competitions are useful for time-based contamination control but saturate fast.",
        "source_url": "https://artofproblemsolving.com/wiki/index.php/AIME_Problems_and_Solutions",
    },
    {
        "eval_id": "math",
        "name": "MATH",
        "family": "competition_math",
        "modality": "text",
        "capability": "Mathematical reasoning",
        "what_people_do": "Solve competition-style math questions with final answers.",
        "construction": "Curated problem set across math topics and difficulty levels.",
        "scoring": "Exact final answer match, often with boxed-answer extraction.",
        "benchbench_lesson": "Final-answer grading is cheap, but solution validity and leakage remain problems.",
        "source_url": "https://arxiv.org/abs/2103.03874",
    },
    {
        "eval_id": "gsm8k",
        "name": "GSM8K",
        "family": "math_word_problems",
        "modality": "text",
        "capability": "Grade-school arithmetic word reasoning",
        "what_people_do": "Solve natural-language arithmetic word problems.",
        "construction": "Human-written grade-school problems with numeric answers.",
        "scoring": "Exact numeric answer.",
        "benchbench_lesson": "Small clean tasks are useful, but model progress can saturate them.",
        "source_url": "https://arxiv.org/abs/2110.14168",
    },
    {
        "eval_id": "bbh",
        "name": "BIG-Bench Hard",
        "family": "reasoning_suite",
        "modality": "text",
        "capability": "Diverse hard reasoning tasks",
        "what_people_do": "Answer selected BIG-bench tasks that were difficult for earlier models.",
        "construction": "Subset of BIG-bench tasks where prior models underperformed.",
        "scoring": "Task-specific accuracy or exact match.",
        "benchbench_lesson": "A hard subset can age out as models improve; refresh and discriminability matter.",
        "source_url": "https://arxiv.org/abs/2210.09261",
    },
    {
        "eval_id": "big_bench",
        "name": "BIG-bench",
        "family": "reasoning_suite",
        "modality": "text",
        "capability": "Broad probing of LM behavior",
        "what_people_do": "Run many contributed tasks spanning knowledge, reasoning, bias, and games.",
        "construction": "Community-contributed suite with 200+ tasks.",
        "scoring": "Task-specific metrics.",
        "benchbench_lesson": "Community task generation scales coverage but needs strong quality gates.",
        "source_url": "https://github.com/google/BIG-bench",
    },
    {
        "eval_id": "hellaswag",
        "name": "HellaSwag",
        "family": "commonsense",
        "modality": "text",
        "capability": "Commonsense continuation selection",
        "what_people_do": "Pick the plausible ending for a short scenario.",
        "construction": "Adversarially filtered commonsense completion dataset.",
        "scoring": "Multiple-choice accuracy.",
        "benchbench_lesson": "Adversarial filtering helps initially, but static artifacts can become shortcuts.",
        "source_url": "https://arxiv.org/abs/1905.07830",
    },
    {
        "eval_id": "arc",
        "name": "ARC Challenge",
        "family": "commonsense_science",
        "modality": "text",
        "capability": "Elementary science reasoning",
        "what_people_do": "Answer multiple-choice science exam questions.",
        "construction": "Science questions selected for difficulty against retrieval/baselines.",
        "scoring": "Accuracy.",
        "benchbench_lesson": "Good benchmark names outlive their difficulty; keep measuring saturation.",
        "source_url": "https://arxiv.org/abs/1803.05457",
    },
    {
        "eval_id": "winogrande",
        "name": "WinoGrande",
        "family": "commonsense_coreference",
        "modality": "text",
        "capability": "Commonsense coreference",
        "what_people_do": "Choose the correct referent in Winograd-style sentences.",
        "construction": "Large-scale adversarially filtered Winograd schema dataset.",
        "scoring": "Accuracy.",
        "benchbench_lesson": "Narrow constructs can be useful if they retain item-level validity.",
        "source_url": "https://arxiv.org/abs/1907.10641",
    },
    {
        "eval_id": "truthfulqa",
        "name": "TruthfulQA",
        "family": "truthfulness",
        "modality": "text",
        "capability": "Avoiding imitative falsehoods",
        "what_people_do": "Answer questions designed to elicit common misconceptions.",
        "construction": "Human-written adversarial questions around false beliefs.",
        "scoring": "Truthfulness and informativeness via references/judges.",
        "benchbench_lesson": "A good eval can target a specific failure mode rather than general intelligence.",
        "source_url": "https://arxiv.org/abs/2109.07958",
    },
    {
        "eval_id": "ifeval",
        "name": "IFEval",
        "family": "instruction_following",
        "modality": "text",
        "capability": "Verifiable instruction following",
        "what_people_do": "Produce outputs satisfying explicit checkable constraints.",
        "construction": "Prompt set with objectively checkable instruction constraints.",
        "scoring": "Prompt-level and instruction-level rule satisfaction.",
        "benchbench_lesson": "Deterministic checkers are valuable for open-ended-looking tasks.",
        "source_url": "https://arxiv.org/abs/2311.07911",
    },
    {
        "eval_id": "musr",
        "name": "MuSR",
        "family": "long_context_reasoning",
        "modality": "text",
        "capability": "Multistep soft reasoning over long narratives",
        "what_people_do": "Answer questions requiring reasoning over long generated narratives.",
        "construction": "Synthetic long-form tasks such as murder mysteries and object placements.",
        "scoring": "Multiple-choice accuracy.",
        "benchbench_lesson": "Long-context benchmarks need controls against shallow retrieval within the prompt.",
        "source_url": "https://arxiv.org/abs/2310.16049",
    },
    {
        "eval_id": "livebench",
        "name": "LiveBench",
        "family": "dynamic_general",
        "modality": "text",
        "capability": "Contamination-resistant general capabilities",
        "what_people_do": "Answer frequently updated questions from recent sources and harder variants.",
        "construction": "Fresh questions from recent math, arXiv, news, datasets, and coding sources.",
        "scoring": "Objective ground-truth scoring.",
        "benchbench_lesson": "Live refresh is one of the cleanest anti-leakage mechanisms.",
        "source_url": "https://github.com/livebench/livebench",
    },
    {
        "eval_id": "livecodebench",
        "name": "LiveCodeBench",
        "family": "coding",
        "modality": "text_code",
        "capability": "Code generation and coding reasoning",
        "what_people_do": "Solve fresh contest-style programming tasks and related code tasks.",
        "construction": "Continuously collects new problems from LeetCode, AtCoder, and Codeforces.",
        "scoring": "Functional correctness and task-specific metrics.",
        "benchbench_lesson": "Time-based sourcing plus executable tests gives practical contamination resistance.",
        "source_url": "https://arxiv.org/abs/2403.07974",
    },
    {
        "eval_id": "humaneval",
        "name": "HumanEval",
        "family": "coding",
        "modality": "code",
        "capability": "Python function synthesis",
        "what_people_do": "Write Python functions from docstrings that pass unit tests.",
        "construction": "Hand-written programming problems with hidden tests.",
        "scoring": "pass@k functional correctness.",
        "benchbench_lesson": "Executable grading is powerful, but small static sets saturate.",
        "source_url": "https://arxiv.org/abs/2107.03374",
    },
    {
        "eval_id": "mbpp",
        "name": "MBPP",
        "family": "coding",
        "modality": "code",
        "capability": "Basic Python programming",
        "what_people_do": "Write short Python programs from natural-language specs.",
        "construction": "Crowdsourced Python tasks with examples/tests.",
        "scoring": "Functional correctness against tests.",
        "benchbench_lesson": "Representative coding microtasks are cheap but need hidden robust tests.",
        "source_url": "https://arxiv.org/abs/2108.07732",
    },
    {
        "eval_id": "bigcodebench",
        "name": "BigCodeBench",
        "family": "coding",
        "modality": "code",
        "capability": "Practical code generation with library use",
        "what_people_do": "Implement more realistic Python functions involving dependencies and composition.",
        "construction": "Large code task suite with executable unit tests.",
        "scoring": "Functional correctness.",
        "benchbench_lesson": "Move beyond toy functions when evaluating real coding ability.",
        "source_url": "https://arxiv.org/abs/2406.15877",
    },
    {
        "eval_id": "swe_bench",
        "name": "SWE-bench",
        "family": "software_engineering",
        "modality": "code_repo",
        "capability": "Real GitHub issue resolution",
        "what_people_do": "Patch real repositories to resolve issues.",
        "construction": "Issues and pull requests from Python repos with test-based validation.",
        "scoring": "Resolved if tests pass after patch.",
        "benchbench_lesson": "Real executable tasks make strong evals, but environments and flakiness matter.",
        "source_url": "https://github.com/SWE-bench/SWE-bench",
    },
    {
        "eval_id": "mle_bench",
        "name": "MLE-bench",
        "family": "ml_engineering",
        "modality": "code_data",
        "capability": "Machine-learning engineering",
        "what_people_do": "Compete on offline Kaggle-style ML tasks.",
        "construction": "75 Kaggle competitions repackaged with local data and graders.",
        "scoring": "Competition-specific score with medal baselines.",
        "benchbench_lesson": "Human competition ecosystems provide useful baselines and graders.",
        "source_url": "https://github.com/openai/mle-bench",
    },
    {
        "eval_id": "re_bench",
        "name": "RE-Bench",
        "family": "research_engineering",
        "modality": "code_research",
        "capability": "AI R&D and research engineering",
        "what_people_do": "Complete controlled research-engineering tasks under budgets.",
        "construction": "METR task standard with human expert comparisons.",
        "scoring": "Task-specific outcome under time and tool budgets.",
        "benchbench_lesson": "Long-horizon benchmarks must specify scaffold, budget, and environment.",
        "source_url": "https://github.com/METR/RE-Bench",
    },
    {
        "eval_id": "osworld",
        "name": "OSWorld",
        "family": "computer_use",
        "modality": "desktop",
        "capability": "Computer-use agents",
        "what_people_do": "Control real desktop and web apps to complete tasks.",
        "construction": "Tasks in real OS/app environments with resettable states.",
        "scoring": "Execution-based task success.",
        "benchbench_lesson": "Environment reproducibility is part of the benchmark, not a footnote.",
        "source_url": "https://arxiv.org/abs/2404.07972",
    },
    {
        "eval_id": "webarena",
        "name": "WebArena",
        "family": "web_agent",
        "modality": "browser",
        "capability": "Autonomous web navigation and task completion",
        "what_people_do": "Use simulated real websites to complete user tasks.",
        "construction": "Self-hosted web environments with realistic sites and goals.",
        "scoring": "Programmatic and manual task success checks.",
        "benchbench_lesson": "Agent benchmarks need resettable realistic environments and objective end states.",
        "source_url": "https://arxiv.org/abs/2307.13854",
    },
    {
        "eval_id": "tau_bench",
        "name": "tau-bench",
        "family": "tool_agent",
        "modality": "text_tools",
        "capability": "Tool-using conversational agents",
        "what_people_do": "Interact with users and APIs in simulated service workflows.",
        "construction": "Domain-specific user simulations and tool APIs.",
        "scoring": "Task success and policy compliance.",
        "benchbench_lesson": "Tool-use evals should test policy, state, and interaction, not just API syntax.",
        "source_url": "https://arxiv.org/abs/2406.12045",
    },
    {
        "eval_id": "bfcl",
        "name": "Berkeley Function Calling Leaderboard",
        "family": "tool_calling",
        "modality": "text_tools",
        "capability": "Function calling and structured tool use",
        "what_people_do": "Select and format function calls in single-turn and multi-turn scenarios.",
        "construction": "Realistic function schemas and tool-use tasks, periodically updated.",
        "scoring": "AST/execution-style correctness and cost metrics.",
        "benchbench_lesson": "Narrow tool subskills can be measured with high precision.",
        "source_url": "https://gorilla.cs.berkeley.edu/leaderboard",
    },
    {
        "eval_id": "gaia",
        "name": "GAIA",
        "family": "agent_reasoning",
        "modality": "text_web_tools",
        "capability": "General assistant reasoning with tools",
        "what_people_do": "Answer questions that often require browsing, files, calculation, or multimodal evidence.",
        "construction": "Human-authored tasks with unambiguous answers and tool use allowed.",
        "scoring": "Exact or normalized answer match.",
        "benchbench_lesson": "Agentic tasks can remain human-solvable while exposing tool/reasoning gaps.",
        "source_url": "https://arxiv.org/abs/2311.12983",
    },
    {
        "eval_id": "browsecomp",
        "name": "BrowseComp",
        "family": "web_research",
        "modality": "text_web",
        "capability": "Hard web browsing and information retrieval",
        "what_people_do": "Find hard-to-locate answers using the web.",
        "construction": "Human-designed questions requiring persistent search.",
        "scoring": "Answer match or rubric-based correctness.",
        "benchbench_lesson": "Search benchmarks need current sources and answer-verification discipline.",
        "source_url": "https://openai.com/index/browsecomp/",
    },
    {
        "eval_id": "simpleqa",
        "name": "SimpleQA",
        "family": "factuality",
        "modality": "text",
        "capability": "Short factual question answering and hallucination resistance",
        "what_people_do": "Answer short fact-seeking questions or abstain when uncertain.",
        "construction": "Fact questions with reference answers and grader.",
        "scoring": "Correct, incorrect, or not attempted.",
        "benchbench_lesson": "Separate knowing from guessing when scoring factuality.",
        "source_url": "https://openai.com/index/introducing-simpleqa/",
    },
    {
        "eval_id": "mmmu",
        "name": "MMMU",
        "family": "multimodal_reasoning",
        "modality": "image_text",
        "capability": "College-level multimodal understanding",
        "what_people_do": "Answer expert-level questions involving images and text.",
        "construction": "Curated multimodal questions across disciplines.",
        "scoring": "Accuracy.",
        "benchbench_lesson": "Multimodal evals should require reasoning over the image, not OCR alone.",
        "source_url": "https://arxiv.org/abs/2311.16502",
    },
    {
        "eval_id": "mathvista",
        "name": "MathVista",
        "family": "visual_math",
        "modality": "image_text",
        "capability": "Mathematical and diagram reasoning over visuals",
        "what_people_do": "Solve math questions grounded in charts, diagrams, and images.",
        "construction": "Multimodal math benchmark drawn from diverse visual sources.",
        "scoring": "Accuracy with answer normalization.",
        "benchbench_lesson": "Visual math can test genuine grounding if constructed against text-only shortcuts.",
        "source_url": "https://arxiv.org/abs/2310.02255",
    },
    {
        "eval_id": "chartqa",
        "name": "ChartQA",
        "family": "visual_data",
        "modality": "chart_text",
        "capability": "Chart understanding and quantitative visual reasoning",
        "what_people_do": "Answer questions about charts.",
        "construction": "Human-written and machine-generated chart QA examples.",
        "scoring": "Relaxed exact match / numeric tolerance.",
        "benchbench_lesson": "Grading visual quantitative answers needs normalization and tolerance rules.",
        "source_url": "https://arxiv.org/abs/2203.10244",
    },
    {
        "eval_id": "docvqa",
        "name": "DocVQA",
        "family": "document_understanding",
        "modality": "document_image_text",
        "capability": "Document reading and extraction",
        "what_people_do": "Answer questions over scanned or rendered documents.",
        "construction": "Document images with question-answer annotations.",
        "scoring": "ANLS / normalized string similarity.",
        "benchbench_lesson": "Document tasks need layout fidelity and answer-normalization rules.",
        "source_url": "https://arxiv.org/abs/2007.00398",
    },
    {
        "eval_id": "chatbot_arena",
        "name": "Chatbot Arena / LMArena",
        "family": "preference",
        "modality": "text_multimodal",
        "capability": "Human preference over model responses",
        "what_people_do": "Humans vote in blind model-vs-model battles.",
        "construction": "Live user prompts and randomized pairwise comparisons.",
        "scoring": "Bradley-Terry/Elo-style rating and ranks.",
        "benchbench_lesson": "Preference data is powerful but not ground truth; use as an external comparison axis.",
        "source_url": "https://arena.ai/leaderboard/text",
    },
    {
        "eval_id": "arena_hard",
        "name": "Arena-Hard",
        "family": "preference",
        "modality": "text",
        "capability": "Hard open-ended chat prompts",
        "what_people_do": "Answer difficult real-user prompts scored by a judge model.",
        "construction": "Samples from Chatbot Arena queries; clusters and filters for diversity and quality.",
        "scoring": "Automated preference judging calibrated against Arena.",
        "benchbench_lesson": "Use real prompts, diversity filters, and human-rank validation when using judge-based evals.",
        "source_url": "https://www.lmsys.org/blog/2024-04-19-arena-hard/",
    },
    {
        "eval_id": "mt_bench",
        "name": "MT-Bench",
        "family": "judge_based",
        "modality": "text",
        "capability": "Multi-turn chat helpfulness",
        "what_people_do": "Respond to fixed two-turn prompts.",
        "construction": "Curated multi-turn prompt set.",
        "scoring": "LLM judge scores.",
        "benchbench_lesson": "Fast and cheap, but judge calibration and bias matter.",
        "source_url": "https://arxiv.org/abs/2306.05685",
    },
    {
        "eval_id": "helm",
        "name": "HELM",
        "family": "evaluation_framework",
        "modality": "mixed",
        "capability": "Holistic model evaluation across scenarios and metrics",
        "what_people_do": "Run many scenarios with standardized metrics beyond accuracy.",
        "construction": "Benchmark framework and scenario suite.",
        "scoring": "Multiple metrics including accuracy, calibration, robustness, toxicity, fairness, and efficiency.",
        "benchbench_lesson": "Benchmark quality includes metrics, not just task items.",
        "source_url": "https://crfm.stanford.edu/helm/",
    },
    {
        "eval_id": "opencompass",
        "name": "OpenCompass",
        "family": "evaluation_framework",
        "modality": "mixed",
        "capability": "Broad standardized model evaluation",
        "what_people_do": "Run many public benchmarks under standardized prompts and settings.",
        "construction": "Open-source evaluation platform with leaderboard.",
        "scoring": "Benchmark-specific metrics aggregated by suite.",
        "benchbench_lesson": "Use frameworks to reduce prompt/protocol variance when comparing evals.",
        "source_url": "https://opencompass.org.cn/leaderboard-llm",
    },
    {
        "eval_id": "dynabench",
        "name": "Dynabench",
        "family": "dynamic_adversarial",
        "modality": "text",
        "capability": "Robustness under model-in-the-loop data collection",
        "what_people_do": "Humans write examples that fool target models while staying valid for humans.",
        "construction": "Dynamic rounds of adversarial human data collection.",
        "scoring": "Task-specific metrics across rounds.",
        "benchbench_lesson": "The closest ancestor of BenchBench: fool the model, not the human.",
        "source_url": "https://arxiv.org/abs/2104.14337",
    },
]


def mkdirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SOURCE_TABLES.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_eval_catalog() -> None:
    fieldnames = [
        "eval_id",
        "name",
        "family",
        "modality",
        "capability",
        "what_people_do",
        "construction",
        "scoring",
        "benchbench_lesson",
        "source_url",
    ]
    write_csv(OUT / "eval_catalog.csv", CATALOG, fieldnames)
    lines = [
        "# Eval Catalog",
        "",
        f"Generated: {dt.datetime.now(dt.UTC).isoformat()}",
        "",
        "| eval | family | what people do | scoring | source |",
        "|---|---|---|---|---|",
    ]
    for row in CATALOG:
        lines.append(
            f"| {row['name']} | {row['family']} | {row['what_people_do']} | "
            f"{row['scoring']} | {row['source_url']} |"
        )
    (OUT / "eval_catalog.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect_openllm() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    parquet_path = hf_hub_download(OPENLLM_REPO, OPENLLM_PARQUET, repo_type="dataset")
    df = pd.read_parquet(parquet_path)
    rename = {
        "fullname": "model",
        "Average ⬆️": "openllm_average",
        "IFEval": "ifeval",
        "BBH": "bbh",
        "MATH Lvl 5": "math_lvl_5",
        "GPQA": "gpqa",
        "MUSR": "musr",
        "MMLU-PRO": "mmlu_pro",
        "#Params (B)": "params_b",
        "Model": "model_short",
        "Type": "type",
        "Architecture": "architecture",
        "Available on the hub": "available_on_hub",
        "Submission Date": "submission_date",
        "Upload To Hub Date": "upload_to_hub_date",
        "Generation": "generation",
        "Base Model": "base_model",
    }
    keep = [col for col in rename if col in df.columns]
    out = df[keep].rename(columns=rename)
    out["source"] = "open_llm_leaderboard_v2"
    out["source_url"] = OPENLLM_URL
    out_path = SOURCE_TABLES / "open_llm_leaderboard_v2_scores.csv"
    out.to_csv(out_path, index=False)

    long_rows: list[dict[str, Any]] = []
    for _, row in out.iterrows():
        for metric in ["openllm_average", "ifeval", "bbh", "math_lvl_5", "gpqa", "musr", "mmlu_pro"]:
            value = row.get(metric)
            if pd.isna(value):
                continue
            long_rows.append(
                {
                    "source": "open_llm_leaderboard_v2",
                    "benchmark": f"openllm_{metric}",
                    "model": row["model"],
                    "score": float(value),
                    "score_type": "percent_or_index",
                    "rank": "",
                    "uncertainty": "",
                    "n": "",
                    "source_url": OPENLLM_URL,
                    "notes": "",
                }
            )
    return out, long_rows


def parse_int(text: str) -> int | None:
    text = text.replace(",", "").strip()
    if not text or text.upper() == "N/A":
        return None
    match = re.search(r"-?\d+", text)
    return int(match.group(0)) if match else None


def parse_arena_score(text: str) -> tuple[float | None, str]:
    clean = text.replace("Preliminary", "").strip()
    match = re.search(r"(-?\d+(?:\.\d+)?)", clean)
    if not match:
        return None, ""
    score = float(match.group(1))
    rest = clean[match.end() :].strip()
    return score, rest


def collect_arena_current() -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    long_rows: list[dict[str, Any]] = []
    for page in ARENA_PAGES:
        response = requests.get(page["url"], headers={"User-Agent": USER_AGENT}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        page_rows: list[dict[str, Any]] = []
        for tr in soup.select("tbody tr"):
            cells = tr.find_all("td")
            if len(cells) < 5:
                continue
            rank = parse_int(cells[0].get_text(" ", strip=True))
            rank_spread = cells[1].get_text(" ", strip=True)
            model_cell = cells[2]
            model_link = model_cell.find("a")
            model = (
                model_link.get("title")
                if model_link and model_link.get("title")
                else model_link.get_text(" ", strip=True)
                if model_link
                else model_cell.get_text(" ", strip=True)
            )
            model_text = model_cell.get_text(" ", strip=True)
            license_text = ""
            org = ""
            if " · " in model_text:
                before_license, license_text = model_text.rsplit(" · ", 1)
                before_model = before_license.replace(model, "").strip()
                if before_model:
                    org = before_model.split()[-1]
            score, uncertainty = parse_arena_score(cells[3].get_text(" ", strip=True))
            votes = parse_int(cells[4].get_text(" ", strip=True))
            price = cells[5].get_text(" ", strip=True) if len(cells) > 5 else ""
            context = cells[6].get_text(" ", strip=True) if len(cells) > 6 else ""
            row = {
                "source": page["source_id"],
                "benchmark": page["benchmark"],
                "benchmark_name": page["name"],
                "rank": rank,
                "rank_spread": rank_spread,
                "model": model,
                "organization": org,
                "license": license_text,
                "score": score,
                "uncertainty": uncertainty,
                "votes": votes,
                "price_per_million_input_output": price,
                "context": context,
                "source_url": page["url"],
            }
            page_rows.append(row)
            all_rows.append(row)
            if score is not None:
                long_rows.append(
                    {
                        "source": page["source_id"],
                        "benchmark": page["benchmark"],
                        "model": model,
                        "score": score,
                        "score_type": "arena_rating",
                        "rank": rank or "",
                        "uncertainty": uncertainty,
                        "n": votes or "",
                        "source_url": page["url"],
                        "notes": page["name"],
                    }
                )
        pd.DataFrame(page_rows).to_csv(SOURCE_TABLES / f"{page['source_id']}.csv", index=False)
        manifest.append(
            {
                "source": page["source_id"],
                "benchmark": page["benchmark"],
                "url": page["url"],
                "rows": len(page_rows),
            }
        )
    df = pd.DataFrame(all_rows)
    df.to_csv(SOURCE_TABLES / "lmarena_current_scores.csv", index=False)
    return df, long_rows, manifest


def collect_arena_archive() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    archive_path = hf_hub_download(LMARENA_ARCHIVE_REPO, LMARENA_ARCHIVE_FILE, repo_type="space")
    df = pd.read_csv(archive_path)
    df["source"] = "lmarena_archive_20250409"
    df["source_url"] = LMARENA_ARCHIVE_URL
    df.to_csv(SOURCE_TABLES / "lmarena_archive_20250409.csv", index=False)
    long_rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        rating = row.get("rating")
        if pd.isna(rating):
            continue
        long_rows.append(
            {
                "source": "lmarena_archive_20250409",
                "benchmark": "lmarena_archive_battle_rating_20250409",
                "model": row.get("Model") or row.get("key"),
                "score": float(rating),
                "score_type": "arena_rating",
                "rank": row.get("final_ranking", ""),
                "uncertainty": "",
                "n": row.get("num_battles", ""),
                "source_url": LMARENA_ARCHIVE_URL,
                "notes": "Historical Hugging Face-hosted Chatbot Arena table.",
            }
        )
    return df, long_rows


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def read_benchmark_name(spec_path: Path) -> str:
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except Exception:
        return spec_path.parent.name
    for key in ["name", "benchmark_name", "benchmark", "benchmark_id"]:
        value = spec.get(key)
        if value:
            return str(value)
    return spec_path.parent.name


def solver_model_from_score_path(path: Path) -> tuple[str, str]:
    if path.stem.startswith("score_specialist_"):
        return path.stem.replace("score_", ""), "baseline"
    name = path.stem.replace("score_solver_", "")
    effort = "default"
    if "xhigh" in name:
        effort = "xhigh"
    elif "high" in name:
        effort = "high"
    name = name.replace("grid_", "").replace("high_", "").replace("xhigh_", "")
    match = re.search(r"gpt_5_[245]", name)
    if not match:
        return name.replace("_", "-"), effort
    return match.group(0).replace("_", "-").replace("gpt-5-", "gpt-5."), effort


def collect_benchbench_scores() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    run_roots = [
        ROOT / "experiments" / "001_three_model_grid_pilot" / "run",
        ROOT / "experiments" / "002_broad_sweep_20260515_220653" / "run",
    ]
    for run_root in run_roots:
        if not run_root.exists():
            continue
        experiment = run_root.parent.name
        for candidate_dir in sorted(run_root.glob("candidate_created_by_gpt_5_*")):
            creator = candidate_dir.name.replace("candidate_created_by_", "").replace("_", "-").replace("gpt-5-", "gpt-5.")
            benchmark_name = read_benchmark_name(candidate_dir / "benchmark_spec.json")
            benchmark_slug = f"benchbench_{slugify(benchmark_name)}"
            score_paths = sorted(candidate_dir.glob("score_solver*.json"))
            score_paths += sorted(candidate_dir.glob("score_specialist*.json"))
            for score_path in score_paths:
                try:
                    score = json.loads(score_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                solver, effort = solver_model_from_score_path(score_path)
                total = score.get("total", score.get("n_items"))
                correct = score.get("correct", score.get("n_correct"))
                accuracy = score.get("accuracy")
                if accuracy is None and total:
                    accuracy = correct / total
                rows.append(
                    {
                        "experiment": experiment,
                        "benchmark": benchmark_slug,
                        "benchmark_name": benchmark_name,
                        "creator_model": creator,
                        "solver_model": solver,
                        "solver_effort": effort,
                        "correct": correct,
                        "total": total,
                        "accuracy": accuracy,
                        "score_path": str(score_path.relative_to(ROOT)),
                    }
                )
    df = pd.DataFrame(rows)
    df.to_csv(SOURCE_TABLES / "benchbench_candidate_scores.csv", index=False)
    long_rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        if pd.isna(row.get("accuracy")):
            continue
        model_name = row["solver_model"]
        if row["solver_effort"] == "xhigh":
            model_name += "-xhigh"
        long_rows.append(
            {
                "source": "benchbench_local",
                "benchmark": row["benchmark"],
                "model": model_name,
                "score": float(row["accuracy"]),
                "score_type": "accuracy_fraction",
                "rank": "",
                "uncertainty": "",
                "n": row.get("total", ""),
                "source_url": row.get("score_path", ""),
                "notes": f"creator={row['creator_model']}; experiment={row['experiment']}",
            }
        )
    return df, long_rows


def write_model_aliases() -> None:
    rows = [
        {
            "canonical_model": "gpt-5.2",
            "alias": "gpt-5.2-chat-latest-20260210",
            "confidence": "medium",
            "notes": "BenchBench Codex model versus LMArena chat endpoint; compare cautiously.",
        },
        {
            "canonical_model": "gpt-5.4",
            "alias": "gpt-5.4",
            "confidence": "high",
            "notes": "Same public model label where present.",
        },
        {
            "canonical_model": "gpt-5.4",
            "alias": "gpt-5.4-high",
            "confidence": "low",
            "notes": "High-reasoning Arena variant, not identical to low-effort BenchBench solver.",
        },
        {
            "canonical_model": "gpt-5.5",
            "alias": "gpt-5.5",
            "confidence": "high",
            "notes": "Same public model label where present.",
        },
        {
            "canonical_model": "gpt-5.5-xhigh",
            "alias": "gpt-5.5-xhigh (codex-harness)",
            "confidence": "medium",
            "notes": "Arena Codex-harness xhigh variant; useful but not guaranteed identical to local Codex run.",
        },
    ]
    write_csv(OUT / "model_aliases.csv", rows)


def write_long_and_wide(all_long_rows: list[dict[str, Any]]) -> pd.DataFrame:
    long_df = pd.DataFrame(all_long_rows)
    long_df.to_csv(OUT / "model_score_matrix_long.csv", index=False)
    if not long_df.empty:
        wide = long_df.pivot_table(index="model", columns="benchmark", values="score", aggfunc="max")
        wide.reset_index().to_csv(OUT / "model_score_matrix_wide.csv", index=False)
    return long_df


def write_prompt_pack(openllm: pd.DataFrame, arena: pd.DataFrame, benchbench: pd.DataFrame) -> None:
    top_arena = (
        arena[["benchmark", "rank", "model", "score"]]
        .dropna(subset=["score"])
        .sort_values(["benchmark", "rank"])
        .groupby("benchmark")
        .head(8)
    )
    lines = [
        "# Benchmark Landscape Prompt Pack",
        "",
        "Purpose: give BenchBench creators broad evidence about existing evals without steering them into a specific domain.",
        "",
        "## Current Creator Prompt Inputs",
        "",
        "The current broad sweep prompt reads this landscape pack plus the prior pilot summary.",
        "Before this pack existed, it read `benchbench_research_notes.md` plus `experiments/001_three_model_grid_pilot/README.md`.",
        "",
        "## Eval Families To Be Aware Of",
        "",
    ]
    by_family: dict[str, list[str]] = {}
    for row in CATALOG:
        by_family.setdefault(row["family"], []).append(row["name"])
    for family, names in sorted(by_family.items()):
        lines.append(f"- {family}: {', '.join(names[:8])}")
    lines += [
        "",
        "## High-Level Benchmark Design Lessons",
        "",
        "- State the capability claim before writing items.",
        "- Make the solver-visible task self-contained and the grader deterministic where possible.",
        "- Prefer hidden or fresh items, procedural generation, live sourcing, or expert provenance.",
        "- Measure human solvability; a benchmark that nobody can solve is not a win.",
        "- Require external solvability: the public solver packet must contain enough information for a qualified outside model or human specialist to determine the answer in principle.",
        "- Do not reward impossible, under-specified, private-keyed, or open-research-problem tasks just because frontier models score poorly.",
        "- Attack leakage, ambiguity, and shortcut baselines before counting model failures.",
        "- Use existing score matrices to test whether a new benchmark adds a residual measurement axis.",
        "",
        "## Machine-Readable Score Sources Included",
        "",
        f"- Open LLM Leaderboard v2: {len(openllm)} models x 7 score columns: average, IFEval, BBH, MATH Lvl 5, GPQA, MuSR, MMLU-Pro.",
        f"- Current LMArena scraped pages: {len(arena)} model rows across text, WebDev, Image-to-WebDev, vision, document, and search arenas.",
        f"- Local BenchBench runs: {len(benchbench)} model-on-candidate score rows.",
        "",
        "## Current LMArena Top Rows",
        "",
        "| benchmark | rank | model | score |",
        "|---|---:|---|---:|",
    ]
    for _, row in top_arena.iterrows():
        lines.append(f"| {row['benchmark']} | {int(row['rank'])} | {row['model']} | {row['score']:.0f} |")
    lines += [
        "",
        "## BenchBench Local Results To Date",
        "",
        "| experiment | benchmark | creator | solver | effort | score |",
        "|---|---|---|---|---|---:|",
    ]
    for _, row in benchbench.sort_values(["experiment", "benchmark", "solver_model"]).iterrows():
        lines.append(
            f"| {row['experiment']} | {row['benchmark_name']} | {row['creator_model']} | "
            f"{row['solver_model']} | {row['solver_effort']} | {row['correct']}/{row['total']} |"
        )
    lines += [
        "",
        "## How To Use This For Novelty",
        "",
        "For any generated benchmark, add solver scores to `model_score_matrix_long.csv`, align model aliases cautiously, then compute:",
        "",
        "1. Spearman/Kendall rank correlations against existing eval columns.",
        "2. Cross-validated regression from existing eval scores to the new benchmark score.",
        "",
        "A new benchmark is most interesting when it is reliable, human-solvable, not trivially solved by tools, and not strongly predictable from the existing eval basket.",
    ]
    (OUT / "creator_prompt_landscape_pack.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_method_doc() -> None:
    lines = [
        "# Benchmark Similarity And Novelty Method",
        "",
        "This is the scoring-side check for BenchBench.",
        "",
        "## Inputs",
        "",
        "- A long score table: `model`, `benchmark`, `score`, `source`, and optional rank/uncertainty columns.",
        "- A target generated benchmark with enough solver models to overlap public score sources.",
        "- A model alias table for cases like local Codex model labels versus public Arena endpoint labels.",
        "",
        "## Rank Correlation",
        "",
        "For each existing benchmark with overlapping model scores:",
        "",
        "- compute Spearman rho on scores/ranks;",
        "- compute Kendall tau as a stricter rank-order check;",
        "- require an overlap floor before interpreting anything.",
        "",
        "Interpretation:",
        "",
        "- high positive correlation: the new benchmark mostly follows an existing ladder;",
        "- low correlation with stable item reliability: possible new measurement axis;",
        "- negative correlation: interesting only if the reversal has a clear construct explanation;",
        "- no spread or all-zero target scores: not analyzable as a leaderboard.",
        "",
        "## Regression / Predictor Test",
        "",
        "Fit:",
        "",
        "```text",
        "new_benchmark_score(model) ~ existing_eval_scores(model)",
        "```",
        "",
        "Use cross-validated R2, preferably leave-one-out or repeated K-fold depending on `n`.",
        "",
        "```text",
        "predictive_novelty = 1 - cross_validated_R2",
        "```",
        "",
        "Guardrails:",
        "",
        "- do not run regression with only three local models and call it evidence;",
        "- include weaker and mid-tier models so the target benchmark has score spread;",
        "- include specialist baselines if the benchmark is not meant to be general-purpose;",
        "- report confidence intervals or bootstrap variation once there are enough rows.",
        "",
        "Current limitation: the existing BenchBench local results have only GPT-5.2, GPT-5.4, GPT-5.5, and a GPT-5.5 xhigh sanity check. That is enough for a smoke-test rank view, not enough for a serious regression novelty score.",
    ]
    (OUT / "similarity_method.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(
    openllm: pd.DataFrame,
    arena: pd.DataFrame,
    archive: pd.DataFrame,
    benchbench: pd.DataFrame,
    long_df: pd.DataFrame,
    manifest: list[dict[str, Any]],
) -> None:
    lines = [
        "# Benchmark Landscape Pack",
        "",
        f"Generated: {dt.datetime.now(dt.UTC).isoformat()}",
        "",
        "## What Is Here",
        "",
        "- `eval_catalog.csv` / `eval_catalog.md`: curated list of evals, descriptions, construction, scoring, and source URLs.",
        "- `creator_prompt_landscape_pack.md`: compact version meant to be pasted into creator prompts.",
        "- `source_score_tables/`: raw-ish public score tables by source.",
        "- `model_score_matrix_long.csv`: normalized long-form scores for correlations and regressions.",
        "- `model_score_matrix_wide.csv`: sparse wide pivot, convenient for quick inspection.",
        "- `model_aliases.csv`: cautious aliases for local BenchBench model labels versus public leaderboards.",
        "- `similarity_method.md`: the rank-correlation and regression procedure.",
        "",
        "## Score Coverage",
        "",
        f"- Open LLM Leaderboard v2 rows: {len(openllm)}.",
        f"- Current LMArena rows scraped from official pages: {len(arena)}.",
        f"- Historical LMArena archive rows from Hugging Face Space CSV: {len(archive)}.",
        f"- Local BenchBench candidate score rows: {len(benchbench)}.",
        f"- Normalized long score rows: {len(long_df)}.",
        "",
        "## Current Prompt Input",
        "",
        "The broad BenchBench creator script now prefers `benchmark_landscape/creator_prompt_landscape_pack.md` and falls back to `benchbench_research_notes.md` if the pack is missing. It also still includes the Experiment 001 pilot README.",
        "",
        "## Important Limitations",
        "",
        "- This is thorough enough to work from, not a universal all-benchmarks/all-models database.",
        "- Public score tables use inconsistent model names and protocols.",
        "- Open LLM Leaderboard is strong for open-weight models but misses most frontier proprietary models.",
        "- LMArena is current and broad, but it is preference/rating data rather than objective task accuracy.",
        "- BenchBench novelty regression is not meaningful until we run many more solver models on the generated benchmarks.",
        "",
        "## Sources Collected",
        "",
    ]
    for item in manifest:
        lines.append(f"- {item['source']}: {item['rows']} rows from {item['url']}.")
    lines += [
        f"- open_llm_leaderboard_v2: {len(openllm)} rows from {OPENLLM_URL}.",
        f"- lmarena_archive_20250409: {len(archive)} rows from {LMARENA_ARCHIVE_URL}.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_source_manifest(manifest: list[dict[str, Any]], openllm_rows: int, archive_rows: int) -> None:
    data = {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "sources": [
            {
                "source": "open_llm_leaderboard_v2",
                "url": OPENLLM_URL,
                "rows": openllm_rows,
                "notes": "Hugging Face dataset parquet; contains open-weight model scores.",
            },
            {
                "source": "lmarena_archive_20250409",
                "url": LMARENA_ARCHIVE_URL,
                "rows": archive_rows,
                "notes": "Historical CSV in the LMArena Hugging Face Space.",
            },
            *manifest,
        ],
        "local_sources": [
            "experiments/001_three_model_grid_pilot/run/*/score_solver*.json",
            "experiments/002_broad_sweep_20260515_220653/run/*/score_solver*.json",
        ],
    }
    (OUT / "source_manifest.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    mkdirs()
    write_eval_catalog()
    write_model_aliases()
    openllm, openllm_long = collect_openllm()
    arena, arena_long, arena_manifest = collect_arena_current()
    archive, archive_long = collect_arena_archive()
    benchbench, benchbench_long = collect_benchbench_scores()
    all_long = openllm_long + arena_long + archive_long + benchbench_long
    long_df = write_long_and_wide(all_long)
    write_prompt_pack(openllm, arena, benchbench)
    write_method_doc()
    write_readme(openllm, arena, archive, benchbench, long_df, arena_manifest)
    write_source_manifest(arena_manifest, len(openllm), len(archive))
    print(f"Wrote benchmark landscape pack to {OUT}")
    print(f"Eval catalog rows: {len(CATALOG)}")
    print(f"Open LLM rows: {len(openllm)}")
    print(f"LMArena current rows: {len(arena)}")
    print(f"Long score rows: {len(long_df)}")


if __name__ == "__main__":
    main()
