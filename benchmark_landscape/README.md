# Benchmark Landscape Pack

Generated: 2026-05-16T15:57:35.636322+00:00

## What Is Here

- `eval_catalog.csv` / `eval_catalog.md`: curated list of evals, descriptions, construction, scoring, and source URLs.
- `creator_prompt_landscape_pack.md`: compact version meant to be pasted into creator prompts.
- `source_score_tables/`: raw-ish public score tables by source.
- `model_score_matrix_long.csv`: normalized long-form scores for correlations and regressions.
- `model_score_matrix_wide.csv`: sparse wide pivot, convenient for quick inspection.
- `model_aliases.csv`: cautious aliases for local BenchBench model labels versus public leaderboards.
- `similarity_method.md`: the rank-correlation and regression procedure.

## Score Coverage

- Open LLM Leaderboard v2 rows: 4576.
- Current LMArena rows scraped from official pages: 635.
- Historical LMArena archive rows from Hugging Face Space CSV: 61.
- Local BenchBench candidate score rows: 23.
- Normalized long score rows: 32751.

## Current Prompt Input

The broad BenchBench creator script now prefers `benchmark_landscape/creator_prompt_landscape_pack.md` and falls back to `benchbench_research_notes.md` if the pack is missing. It also still includes the Experiment 001 pilot README.

## Important Limitations

- This is thorough enough to work from, not a universal all-benchmarks/all-models database.
- Public score tables use inconsistent model names and protocols.
- Open LLM Leaderboard is strong for open-weight models but misses most frontier proprietary models.
- LMArena is current and broad, but it is preference/rating data rather than objective task accuracy.
- BenchBench novelty regression is not meaningful until we run many more solver models on the generated benchmarks.

## Sources Collected

- lmarena_current_text: 357 rows from https://arena.ai/leaderboard/text.
- lmarena_current_code_webdev: 79 rows from https://arena.ai/leaderboard/code/webdev.
- lmarena_current_code_image_to_webdev: 23 rows from https://arena.ai/leaderboard/code/image-to-webdev.
- lmarena_current_vision: 123 rows from https://arena.ai/leaderboard/vision.
- lmarena_current_document: 24 rows from https://arena.ai/leaderboard/document.
- lmarena_current_search: 29 rows from https://arena.ai/leaderboard/search.
- open_llm_leaderboard_v2: 4576 rows from https://huggingface.co/datasets/open-llm-leaderboard/contents.
- lmarena_archive_20250409: 61 rows from https://huggingface.co/spaces/lmarena/chatbot-arena-leaderboard.
