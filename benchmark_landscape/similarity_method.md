# Benchmark Similarity And Novelty Method

This is the scoring-side check for BenchBench.

## Inputs

- A long score table: `model`, `benchmark`, `score`, `source`, and optional rank/uncertainty columns.
- A target generated benchmark with enough solver models to overlap public score sources.
- A model alias table for cases like local Codex model labels versus public Arena endpoint labels.

## Rank Correlation

For each existing benchmark with overlapping model scores:

- compute Spearman rho on scores/ranks;
- compute Kendall tau as a stricter rank-order check;
- require an overlap floor before interpreting anything.

Interpretation:

- high positive correlation: the new benchmark mostly follows an existing ladder;
- low correlation with stable item reliability: possible new measurement axis;
- negative correlation: interesting only if the reversal has a clear construct explanation;
- no spread or all-zero target scores: not analyzable as a leaderboard.

## Regression / Predictor Test

Fit:

```text
new_benchmark_score(model) ~ existing_eval_scores(model)
```

Use cross-validated R2, preferably leave-one-out or repeated K-fold depending on `n`.

```text
predictive_novelty = 1 - cross_validated_R2
```

Guardrails:

- do not run regression with only three local models and call it evidence;
- include weaker and mid-tier models so the target benchmark has score spread;
- include specialist baselines if the benchmark is not meant to be general-purpose;
- report confidence intervals or bootstrap variation once there are enough rows.

Current limitation: the existing BenchBench local results have only GPT-5.2, GPT-5.4, GPT-5.5, and a GPT-5.5 xhigh sanity check. That is enough for a smoke-test rank view, not enough for a serious regression novelty score.
