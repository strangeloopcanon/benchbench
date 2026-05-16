# Benchmark Landscape Prompt Pack

Purpose: give BenchBench creators broad evidence about existing evals without steering them into a specific domain.

## Current Creator Prompt Inputs

The current broad sweep prompt reads this landscape pack plus the prior pilot summary.
Before this pack existed, it read `benchbench_research_notes.md` plus `experiments/001_three_model_grid_pilot/README.md`.

## Eval Families To Be Aware Of

- agent_reasoning: GAIA
- coding: LiveCodeBench, HumanEval, MBPP, BigCodeBench
- commonsense: HellaSwag
- commonsense_coreference: WinoGrande
- commonsense_science: ARC Challenge
- competition_math: AIME, MATH
- computer_use: OSWorld
- document_understanding: DocVQA
- dynamic_adversarial: Dynabench
- dynamic_general: LiveBench
- evaluation_framework: HELM, OpenCompass
- expert_math: FrontierMath
- expert_qa: GPQA, Humanity's Last Exam
- factuality: SimpleQA
- instruction_following: IFEval
- judge_based: MT-Bench
- knowledge_exam: MMLU, MMLU-Pro
- long_context_reasoning: MuSR
- math_word_problems: GSM8K
- ml_engineering: MLE-bench
- multimodal_reasoning: MMMU
- preference: Chatbot Arena / LMArena, Arena-Hard
- reasoning_suite: BIG-Bench Hard, BIG-bench
- research_engineering: RE-Bench
- software_engineering: SWE-bench
- tool_agent: tau-bench
- tool_calling: Berkeley Function Calling Leaderboard
- truthfulness: TruthfulQA
- visual_data: ChartQA
- visual_math: MathVista
- web_agent: WebArena
- web_research: BrowseComp

## High-Level Benchmark Design Lessons

- State the capability claim before writing items.
- Make the solver-visible task self-contained and the grader deterministic where possible.
- Prefer hidden or fresh items, procedural generation, live sourcing, or expert provenance.
- Measure human solvability; a benchmark that nobody can solve is not a win.
- Require external solvability: the public solver packet must contain enough information for a qualified outside model or human specialist to determine the answer in principle.
- Do not reward impossible, under-specified, private-keyed, or open-research-problem tasks just because frontier models score poorly.
- Attack leakage, ambiguity, and shortcut baselines before counting model failures.
- Use existing score matrices to test whether a new benchmark adds a residual measurement axis.

## Machine-Readable Score Sources Included

- Open LLM Leaderboard v2: 4576 models x 7 score columns: average, IFEval, BBH, MATH Lvl 5, GPQA, MuSR, MMLU-Pro.
- Current LMArena scraped pages: 635 model rows across text, WebDev, Image-to-WebDev, vision, document, and search arenas.
- Local BenchBench runs: 23 model-on-candidate score rows.

## Current LMArena Top Rows

| benchmark | rank | model | score |
|---|---:|---|---:|
| arena_code_image_to_webdev_overall | 1 | claude-opus-4-7-thinking | 1581 |
| arena_code_image_to_webdev_overall | 2 | claude-sonnet-4-6 | 1557 |
| arena_code_image_to_webdev_overall | 3 | claude-opus-4-7 | 1556 |
| arena_code_image_to_webdev_overall | 4 | claude-opus-4-6-thinking | 1538 |
| arena_code_image_to_webdev_overall | 5 | gpt-5.5-xhigh (codex-harness) | 1537 |
| arena_code_image_to_webdev_overall | 6 | claude-opus-4-6 | 1534 |
| arena_code_image_to_webdev_overall | 7 | kimi-k2.6 | 1522 |
| arena_code_image_to_webdev_overall | 8 | gpt-5.5-high (codex-harness) | 1519 |
| arena_code_webdev_overall | 1 | claude-opus-4-7-thinking | 1567 |
| arena_code_webdev_overall | 2 | claude-opus-4-7 | 1559 |
| arena_code_webdev_overall | 3 | claude-opus-4-6-thinking | 1546 |
| arena_code_webdev_overall | 4 | claude-opus-4-6 | 1541 |
| arena_code_webdev_overall | 5 | glm-5.1 | 1532 |
| arena_code_webdev_overall | 6 | claude-sonnet-4-6 | 1524 |
| arena_code_webdev_overall | 7 | kimi-k2.6 | 1519 |
| arena_code_webdev_overall | 8 | muse-spark | 1509 |
| arena_document_overall | 1 | claude-opus-4-6-thinking | 1522 |
| arena_document_overall | 2 | claude-opus-4-6 | 1513 |
| arena_document_overall | 3 | claude-opus-4-7 | 1510 |
| arena_document_overall | 4 | claude-opus-4-7-thinking | 1509 |
| arena_document_overall | 5 | gpt-5.5-high | 1496 |
| arena_document_overall | 6 | claude-sonnet-4-6 | 1495 |
| arena_document_overall | 7 | gpt-5.5 | 1492 |
| arena_document_overall | 8 | gpt-5.4 | 1474 |
| arena_search_overall | 1 | claude-opus-4-6-search | 1251 |
| arena_search_overall | 2 | gpt-5.5-search | 1239 |
| arena_search_overall | 3 | claude-opus-4-7 | 1237 |
| arena_search_overall | 4 | ernie-5.1 | 1226 |
| arena_search_overall | 5 | claude-sonnet-4-6-search | 1219 |
| arena_search_overall | 6 | gemini-3.1-pro-grounding | 1216 |
| arena_search_overall | 7 | gpt-5.2-search | 1210 |
| arena_search_overall | 8 | grok-4.20-multi-agent-beta-0309 | 1209 |
| arena_text_overall | 1 | claude-opus-4-6-thinking | 1502 |
| arena_text_overall | 2 | claude-opus-4-7-thinking | 1500 |
| arena_text_overall | 3 | claude-opus-4-6 | 1498 |
| arena_text_overall | 4 | claude-opus-4-7 | 1492 |
| arena_text_overall | 5 | muse-spark | 1490 |
| arena_text_overall | 6 | gemini-3.1-pro-preview | 1489 |
| arena_text_overall | 7 | gemini-3-pro | 1486 |
| arena_text_overall | 8 | gpt-5.5-high | 1484 |
| arena_vision_overall | 1 | claude-opus-4-7-thinking | 1305 |
| arena_vision_overall | 2 | claude-opus-4-7 | 1303 |
| arena_vision_overall | 3 | claude-opus-4-6-thinking | 1300 |
| arena_vision_overall | 4 | muse-spark | 1299 |
| arena_vision_overall | 5 | claude-opus-4-6 | 1292 |
| arena_vision_overall | 6 | gpt-5.5 | 1290 |
| arena_vision_overall | 7 | gemini-3-pro | 1289 |
| arena_vision_overall | 8 | gpt-5.5-high | 1282 |

## BenchBench Local Results To Date

| experiment | benchmark | creator | solver | effort | score |
|---|---|---|---|---|---:|
| 001_three_model_grid_pilot | Folded Strip Order (FSO) v1 | gpt-5.2 | gpt-5.2 | default | 16/30 |
| 001_three_model_grid_pilot | Folded Strip Order (FSO) v1 | gpt-5.2 | gpt-5.4 | default | 14/30 |
| 001_three_model_grid_pilot | Folded Strip Order (FSO) v1 | gpt-5.2 | gpt-5.5 | default | 19/30 |
| 001_three_model_grid_pilot | occluded_tile_provenance | gpt-5.4 | gpt-5.2 | default | 7/30 |
| 001_three_model_grid_pilot | occluded_tile_provenance | gpt-5.4 | gpt-5.4 | high | 4/30 |
| 001_three_model_grid_pilot | occluded_tile_provenance | gpt-5.4 | gpt-5.5 | high | 5/30 |
| 001_three_model_grid_pilot | occluded_tile_provenance | gpt-5.4 | gpt-5.5 | xhigh | 10/30 |
| 001_three_model_grid_pilot | Shadow Weave Topology | gpt-5.5 | gpt-5.2 | default | 15/30 |
| 001_three_model_grid_pilot | Shadow Weave Topology | gpt-5.5 | gpt-5.4 | high | 24/30 |
| 001_three_model_grid_pilot | Shadow Weave Topology | gpt-5.5 | gpt-5.5 | high | 26/30 |
| 002_broad_sweep_20260515_220653 | IgnoreSense | gpt-5.2 | gpt-5.2 | default | 4/30 |
| 002_broad_sweep_20260515_220653 | IgnoreSense | gpt-5.2 | gpt-5.4 | default | 7/30 |
| 002_broad_sweep_20260515_220653 | IgnoreSense | gpt-5.2 | gpt-5.5 | default | 7/30 |
| 002_broad_sweep_20260515_220653 | IgnoreSense | gpt-5.2 | gpt-5.5 | xhigh | 7/30 |
| 002_broad_sweep_20260515_220653 | protocol_archaeology | gpt-5.5 | gpt-5.2 | default | 0/30 |
| 002_broad_sweep_20260515_220653 | protocol_archaeology | gpt-5.5 | gpt-5.4 | default | 0/30 |
| 002_broad_sweep_20260515_220653 | protocol_archaeology | gpt-5.5 | gpt-5.5 | default | 0/30 |
| 002_broad_sweep_20260515_220653 | protocol_archaeology | gpt-5.5 | gpt-5.5 | xhigh | 0/30 |
| 002_broad_sweep_20260515_220653 | protocol_archaeology | gpt-5.5 | specialist_oracle_family_search | baseline | 0/30 |
| 002_broad_sweep_20260515_220653 | protocol_archaeology | gpt-5.5 | specialist_public_expr | baseline | 0/30 |
| 002_broad_sweep_20260515_220653 | Spectrum Assembly with Side Constraints | gpt-5.4 | gpt-5.2 | default | 30/30 |
| 002_broad_sweep_20260515_220653 | Spectrum Assembly with Side Constraints | gpt-5.4 | gpt-5.4 | default | 30/30 |
| 002_broad_sweep_20260515_220653 | Spectrum Assembly with Side Constraints | gpt-5.4 | gpt-5.5 | default | 30/30 |

## How To Use This For Novelty

For any generated benchmark, add solver scores to `model_score_matrix_long.csv`, align model aliases cautiously, then compute:

1. Spearman/Kendall rank correlations against existing eval columns.
2. Cross-validated regression from existing eval scores to the new benchmark score.

A new benchmark is most interesting when it is reliable, human-solvable, not trivially solved by tools, and not strongly predictable from the existing eval basket.
