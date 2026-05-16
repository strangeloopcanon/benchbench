# BenchBench GPT-5.5 v3 Deep Run - Corrected Summary

Date: 2026-05-15

Run directory:

`/Users/rohit/Documents/Codex/2026-05-14/can-we-also-make-a-benchbench/runs/gpt55_benchbench_v3_deep_20260515_011910`

## Prompt Change

This run gave GPT-5.5 a much richer creator prompt:

- broad map of existing evals: MMLU/MMLU-Pro, GPQA, HLE, FrontierMath, AIME, SWE-bench, LiveBench, LiveCodeBench, BFCL, OSWorld, Arena-Hard, MLE-bench, RE-Bench
- correlation lesson: many benchmark rankings correlate, so reversals only matter if they reflect an interpretable residual skill
- previous BenchBench lesson: valid deterministic packages are easy for GPT-5.5+Codex to turn into code
- explicit instruction to think deeply about new, interesting, under-covered benchmark axes
- v3 package requirement: private pool, adversarial selection, verifier/scorer, and isolated `solver_bundle/`

## Benchmark Produced

GPT-5.5 built **Provenance Benchmark Audit**.

Capability tested:

> Benchmark-quality auditing under conflicting evidence provenance and authority hierarchy.

Each item presents a mini benchmark item with:

- a subject entity
- a review date
- messy-looking evidence records
- four candidate answer options
- a claimed gold answer

The solver must audit whether the mini benchmark is:

- `VALID`
- `GOLD_WRONG:<letter>`
- `NON_UNIQUE:<letters>`
- `NO_VALID`

This is closer to BenchBench's core purpose than the v2 candidates: it tests whether a model can detect bad golds, no-valid cases, non-unique answers, and provenance mistakes.

## Validation

After repair, the package is valid.

The initial validator marked it `CONDITIONAL` for two reasons:

1. the harness overwrote the creator's valid wrong-answer fixture with schema-invalid dummy answers
2. the solver packet needed clearer action precedence

I repaired those without changing item logic:

- patched the generator/packet wording to say that `AUTH_MISSING` or `AUTH_CONFLICT` escalates before open holds block
- regenerated with the same seed
- reran verifier and scorer

Corrected validation:

- private pool: 120/120 verified
- private sample: 30/30 verified
- sample distribution: `GOLD_WRONG=8`, `NON_UNIQUE=8`, `NO_VALID=8`, `VALID=6`
- gold scorer: 30/30
- wrong scorer: 0/30
- solver bundle: only `SOLVER_MANIFEST.json`, `solver_packet.md`, and `items_private_sample.jsonl`

## Solver Result

Blind solver:

- GPT-5.5+Codex
- isolated solver bundle only
- no browsing
- local computation allowed

Score:

- **30/30**
- **accuracy = 1.0**

The solver reconstructed the visible rules and wrote a parser/reasoner from the solver bundle.

## Final Judgment

The benchmark is a valid artifact, but it is **not frontier-resistant**.

It beat the naive baseline: the creator's claim-trusting baseline got 6/30 on the selected sample.

It did not beat GPT-5.5+Codex: GPT-5.5+Codex got 30/30.

## Token Use

Original v3 harness:

- creator: 311,399
- validator: 84,313
- stale pre-solver judge: 27,693
- subtotal: 423,405

Manual corrected passes:

- isolated GPT-5.5+Codex solver: 142,583
- corrected final judge: 59,147

Total reported GPT-5.5 tokens:

- **625,135**

## What Worked

- The richer prompt produced a much more BenchBench-relevant concept.
- The package discipline worked: generator, verifier, scorer, pool, sample, and solver bundle all exist.
- The benchmark attacks benchmark validity itself, not just object-task solving.
- Isolated solver-bundle handling is now much better.
- Adversarial selection beat a naive baseline.

## What Failed

- The task was still too regular.
- The solver-visible evidence had a uniform grammar.
- The full decision rule list was compact and explicit.
- The answer options exposed the exact fields to compare.
- Once GPT-5.5+Codex wrote a parser, all 30 items fell.

## Next Setup Lesson

The next BenchBench prompt should keep the benchmark-audit direction, but force the creator away from a single clean synthetic grammar.

Better target:

> Valid, human-auditable, exact-scoreable, but not reducible to a regex parser plus precedence rules.

Concrete next constraints:

- multi-format evidence: emails, tables, memos, checklists, contracts, screenshots/OCR-like snippets
- varied wording and source formats across items
- cross-document policy fragments rather than one compact rule list
- hidden multi-seed private generation
- larger item sample after solver pre-screening
- explicit anti-regex/anti-parser stress test in validation
- run a tool-enabled frontier solver during creator-side adversarial selection, not only after packaging

