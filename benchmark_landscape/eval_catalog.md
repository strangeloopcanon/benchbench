# Eval Catalog

Generated: 2026-05-16T15:57:28.982886+00:00

| eval | family | what people do | scoring | source |
|---|---|---|---|---|
| MMLU | knowledge_exam | Answer multiple-choice questions across many subjects. | Accuracy. | https://arxiv.org/abs/2009.03300 |
| MMLU-Pro | knowledge_exam | Answer harder multiple-choice questions with more answer options. | Accuracy with prompt stability analysis. | https://arxiv.org/abs/2406.01574 |
| GPQA | expert_qa | Answer expert-written biology, physics, and chemistry questions. | Accuracy. | https://arxiv.org/abs/2311.12022 |
| Humanity's Last Exam | expert_qa | Answer difficult closed-ended expert questions across many fields. | Accuracy and calibration on closed-ended answers. | https://arxiv.org/abs/2501.14249 |
| FrontierMath | expert_math | Solve original expert-level math problems. | Exact answers or proof-style verification depending on item. | https://epoch.ai/frontiermath/the-benchmark |
| AIME | competition_math | Solve short-answer high-school contest math problems. | Exact integer answer accuracy. | https://artofproblemsolving.com/wiki/index.php/AIME_Problems_and_Solutions |
| MATH | competition_math | Solve competition-style math questions with final answers. | Exact final answer match, often with boxed-answer extraction. | https://arxiv.org/abs/2103.03874 |
| GSM8K | math_word_problems | Solve natural-language arithmetic word problems. | Exact numeric answer. | https://arxiv.org/abs/2110.14168 |
| BIG-Bench Hard | reasoning_suite | Answer selected BIG-bench tasks that were difficult for earlier models. | Task-specific accuracy or exact match. | https://arxiv.org/abs/2210.09261 |
| BIG-bench | reasoning_suite | Run many contributed tasks spanning knowledge, reasoning, bias, and games. | Task-specific metrics. | https://github.com/google/BIG-bench |
| HellaSwag | commonsense | Pick the plausible ending for a short scenario. | Multiple-choice accuracy. | https://arxiv.org/abs/1905.07830 |
| ARC Challenge | commonsense_science | Answer multiple-choice science exam questions. | Accuracy. | https://arxiv.org/abs/1803.05457 |
| WinoGrande | commonsense_coreference | Choose the correct referent in Winograd-style sentences. | Accuracy. | https://arxiv.org/abs/1907.10641 |
| TruthfulQA | truthfulness | Answer questions designed to elicit common misconceptions. | Truthfulness and informativeness via references/judges. | https://arxiv.org/abs/2109.07958 |
| IFEval | instruction_following | Produce outputs satisfying explicit checkable constraints. | Prompt-level and instruction-level rule satisfaction. | https://arxiv.org/abs/2311.07911 |
| MuSR | long_context_reasoning | Answer questions requiring reasoning over long generated narratives. | Multiple-choice accuracy. | https://arxiv.org/abs/2310.16049 |
| LiveBench | dynamic_general | Answer frequently updated questions from recent sources and harder variants. | Objective ground-truth scoring. | https://github.com/livebench/livebench |
| LiveCodeBench | coding | Solve fresh contest-style programming tasks and related code tasks. | Functional correctness and task-specific metrics. | https://arxiv.org/abs/2403.07974 |
| HumanEval | coding | Write Python functions from docstrings that pass unit tests. | pass@k functional correctness. | https://arxiv.org/abs/2107.03374 |
| MBPP | coding | Write short Python programs from natural-language specs. | Functional correctness against tests. | https://arxiv.org/abs/2108.07732 |
| BigCodeBench | coding | Implement more realistic Python functions involving dependencies and composition. | Functional correctness. | https://arxiv.org/abs/2406.15877 |
| SWE-bench | software_engineering | Patch real repositories to resolve issues. | Resolved if tests pass after patch. | https://github.com/SWE-bench/SWE-bench |
| MLE-bench | ml_engineering | Compete on offline Kaggle-style ML tasks. | Competition-specific score with medal baselines. | https://github.com/openai/mle-bench |
| RE-Bench | research_engineering | Complete controlled research-engineering tasks under budgets. | Task-specific outcome under time and tool budgets. | https://github.com/METR/RE-Bench |
| OSWorld | computer_use | Control real desktop and web apps to complete tasks. | Execution-based task success. | https://arxiv.org/abs/2404.07972 |
| WebArena | web_agent | Use simulated real websites to complete user tasks. | Programmatic and manual task success checks. | https://arxiv.org/abs/2307.13854 |
| tau-bench | tool_agent | Interact with users and APIs in simulated service workflows. | Task success and policy compliance. | https://arxiv.org/abs/2406.12045 |
| Berkeley Function Calling Leaderboard | tool_calling | Select and format function calls in single-turn and multi-turn scenarios. | AST/execution-style correctness and cost metrics. | https://gorilla.cs.berkeley.edu/leaderboard |
| GAIA | agent_reasoning | Answer questions that often require browsing, files, calculation, or multimodal evidence. | Exact or normalized answer match. | https://arxiv.org/abs/2311.12983 |
| BrowseComp | web_research | Find hard-to-locate answers using the web. | Answer match or rubric-based correctness. | https://openai.com/index/browsecomp/ |
| SimpleQA | factuality | Answer short fact-seeking questions or abstain when uncertain. | Correct, incorrect, or not attempted. | https://openai.com/index/introducing-simpleqa/ |
| MMMU | multimodal_reasoning | Answer expert-level questions involving images and text. | Accuracy. | https://arxiv.org/abs/2311.16502 |
| MathVista | visual_math | Solve math questions grounded in charts, diagrams, and images. | Accuracy with answer normalization. | https://arxiv.org/abs/2310.02255 |
| ChartQA | visual_data | Answer questions about charts. | Relaxed exact match / numeric tolerance. | https://arxiv.org/abs/2203.10244 |
| DocVQA | document_understanding | Answer questions over scanned or rendered documents. | ANLS / normalized string similarity. | https://arxiv.org/abs/2007.00398 |
| Chatbot Arena / LMArena | preference | Humans vote in blind model-vs-model battles. | Bradley-Terry/Elo-style rating and ranks. | https://arena.ai/leaderboard/text |
| Arena-Hard | preference | Answer difficult real-user prompts scored by a judge model. | Automated preference judging calibrated against Arena. | https://www.lmsys.org/blog/2024-04-19-arena-hard/ |
| MT-Bench | judge_based | Respond to fixed two-turn prompts. | LLM judge scores. | https://arxiv.org/abs/2306.05685 |
| HELM | evaluation_framework | Run many scenarios with standardized metrics beyond accuracy. | Multiple metrics including accuracy, calibration, robustness, toxicity, fairness, and efficiency. | https://crfm.stanford.edu/helm/ |
| OpenCompass | evaluation_framework | Run many public benchmarks under standardized prompts and settings. | Benchmark-specific metrics aggregated by suite. | https://opencompass.org.cn/leaderboard-llm |
| Dynabench | dynamic_adversarial | Humans write examples that fool target models while staying valid for humans. | Task-specific metrics across rounds. | https://arxiv.org/abs/2104.14337 |
