# BenchBench prompt setup v2

Purpose: make benchmark-creator models construct valid benchmark artifacts, not merely describe clever evals.

Last updated: 2026-05-15

## What must change from v1

The v1 generator prompt asked for:

- a benchmark idea
- 5 sample items
- gold answers
- a self-critique

That was enough to reveal a real weakness, but it was not enough to produce a proper benchmark. GPT-5.5 produced good concepts, then made gold-key and uniqueness mistakes. The v2 setup should therefore require benchmark creators to use the workspace to build and verify a benchmark package.

The core edit:

> Do not ask the creator model to hand-write final items. Require it to create a generator, verifier, scorer, validation report, and solver-visible packet. Hand-written examples are allowed only as dev examples, never as the submitted private test set.

## BenchBench creator contract

A benchmark creator model must produce a complete artifact directory:

```text
candidate_<id>/
  README.md
  benchmark_spec.json
  generator.py
  verifier.py
  scorer.py
  items_dev.jsonl
  items_private_sample.jsonl
  solver_packet.md
  gold_private_sample.jsonl
  validation_report.md
  failure_modes.md
```

Required properties:

- `generator.py` creates items from private/random seeds.
- `verifier.py` proves or checks each item has a unique valid gold answer.
- `scorer.py` scores solver outputs deterministically.
- `solver_packet.md` contains only solver-visible instructions and items.
- `gold_private_sample.jsonl` contains gold answers and machine-readable grading metadata.
- `validation_report.md` reports generation counts, rejection counts, verifier results, known risks, and expected residual signal.

If the creator cannot build a verifier, it must submit a failed candidate rather than invent unverified gold answers.

## Should Codex be required?

Yes, for creator models in the serious version.

BenchBench should have two creator tracks:

1. **Text-only creator track**
   - The model can only propose a benchmark package in text.
   - This is useful as a cheap ideation baseline.
   - It should not be treated as the main benchmark-generation result.

2. **Codex constructor track**
   - The model gets a writable workspace and can run code.
   - It must write a generator, verifier, scorer, and validation report.
   - This should be the main track, because real benchmark construction is an engineering task.

Codex CLI is enough for the current harness. We do not need a separate SDK yet. A future production harness could use the OpenAI API/Responses SDK for cleaner orchestration, but the key capability is not the SDK; it is requiring runnable artifacts and verification.

## Creator prompt v2

Use this prompt for each creator model/variant.

```text
You are a benchmark-constructor model participating in BenchBench.

Your job is not to write a clever list of questions. Your job is to construct a valid benchmark package that could survive an adversarial solver and an independent verifier.

You have a writable workspace. Use it. You may write Python scripts, generate data, run checks, and revise your own candidate. You may use web search if it materially improves construct validity, contamination checks, or comparison to existing evals.

Goal:
Create a benchmark that reveals a real residual capability not well predicted by the standard benchmark basket, while remaining human-solvable, objectively gradable, contamination-resistant, and hard for GPT-5.5-class solvers.

Standard benchmark basket to consider:
- MMLU / MMLU-Pro
- GPQA
- AIME / math contest evals
- SWE-bench / code repair
- LiveBench / LiveCodeBench
- Chatbot Arena / Arena-Hard
- BFCL / tool calling
- OSWorld / computer-use agents

You should optimize for validated residual signal, not raw anticorrelation. A ranking reversal is valuable only if it reflects an interpretable skill and passes validity checks.

Required artifact directory:
candidate_<short_name>/
  README.md
  benchmark_spec.json
  generator.py
  verifier.py
  scorer.py
  items_dev.jsonl
  items_private_sample.jsonl
  solver_packet.md
  gold_private_sample.jsonl
  validation_report.md
  failure_modes.md

Hard requirements:
1. No hand-written private test items without generator and verifier support.
2. Every private item must have a unique gold answer under the stated rules.
3. The verifier must reject ambiguous items, impossible items, duplicate-gold items, and items with alternate minimal solutions.
4. The scorer must be deterministic.
5. The solver packet must not leak gold answers.
6. The validation report must include:
   - capability axis
   - why existing evals likely miss it
   - expected correlation/residual pattern
   - human baseline protocol
   - frontier failure hypothesis
   - generation count
   - rejection count and rejection reasons
   - verifier command and result
   - scorer command and result on a dummy response
   - known risks
7. If you cannot satisfy the artifact requirements, write `FAILED_CANDIDATE.md` explaining why.

Suggested design pattern:
- Choose a capability where correctness can be generated and checked mechanically.
- Generate many candidate items.
- Verify uniqueness and solvability constraints.
- Add decoys or distractors only when the verifier can prove they do not introduce alternate answers.
- Keep the private sample small enough to inspect, but generated from a scalable process.

Completion criteria:
- Run the verifier on `items_private_sample.jsonl`.
- Run the scorer on at least one deliberately wrong dummy response and one gold response.
- Write a short final answer pointing to the artifact directory and summarizing pass/fail.
```

## Non-specific highlights to include in all creator prompts

These should be phrased as principles, not as one fixed domain:

- **Validity before hardness**: invalid hard tasks score zero.
- **Residual signal before anticorrelation**: decorrelation must be explainable.
- **Golds must be generated or checked**: no confident manual answer keys for complex state tasks.
- **Uniqueness is mandatory**: if two different answers satisfy the item, reject it.
- **Human solvability is mandatory**: qualified humans should beat frontier models under matched rules.
- **Decoys are allowed only if verified**: distractors should test discipline, not create ambiguity.
- **Hardness must survive solver variation**: prompt wording, parsing, and formatting should not be the source of failure.
- **Private items must be fresh**: use seeds/templates and keep public dev examples separate.
- **Measure failure mode**: missed dependency, over-editing, stale derived value, wrong invariant, invalid minimality, etc.

## Validator prompt

Run this after each creator finishes.

```text
You are the BenchBench package validator.

Inspect the candidate artifact directory. Do not solve items first. First decide whether the package is structurally valid.

Check:
1. Required files exist.
2. Generator can regenerate or extend the item set.
3. Verifier runs and rejects invalid/ambiguous items.
4. Scorer runs deterministically.
5. Solver packet does not leak gold answers.
6. Private sample gold answers are machine-readable.
7. The benchmark measures a named capability.
8. The expected residual signal is plausible and not merely "GPT-5.5 will make mistakes."

Then run:
- verifier on private sample
- scorer on a gold response if provided
- scorer on a deliberately wrong response

Return:
- PASS / FAIL / CONDITIONAL
- structural findings
- verifier/scorer command outputs
- top validity risks
- whether the package is ready for a blind solver run
```

## Blind solver prompt

Use only after validator passes or conditionally passes the package.

```text
You are a blind solver for BenchBench.

You receive only the solver-visible packet. Do not inspect gold files, generator code, verifier code, or scorer code. Do not browse unless the benchmark rules allow it.

Solve every item under the benchmark rules. Return answers in exactly the required format. Also flag ambiguity or invalidity, but do not use ambiguity as an excuse unless the item genuinely lacks a unique answer.
```

## Final judge prompt

```text
You are the final BenchBench judge.

Inputs:
- creator artifact directory
- validator report
- blind solver outputs
- scorer outputs
- optional human baseline data

Score the candidate in this order:
1. Structural validity
2. Gold/verifier validity
3. Deterministic scoring
4. Human-solvability plan or data
5. Solver performance gap
6. Residual/complementarity argument
7. Cost and reproducibility

Important:
- A benchmark with broken gold answers scores zero, even if the solver failed.
- A benchmark solved by GPT-5.5 can still be a good candidate concept, but it is not frontier-resistant.
- A benchmark that is anticorrelated because it rewards bad models, formatting quirks, or ambiguity scores zero.

Return:
- accepted / rejected / needs harder generated items
- score table
- exact failure reasons
- whether this should be scaled to a larger solver run
```

## Scoring changes

V1 treated each generated packet as directly solver-testable. V2 should separate scores:

```text
PackageValidityScore:
  required_files
  generator_runs
  verifier_runs
  scorer_runs
  no_gold_leakage
  unique_gold_rate

BenchmarkQualityScore:
  named_capability
  human_solvability
  deterministic_grading
  contamination_plan
  residual_signal_argument
  reproducibility

FrontierResistanceScore:
  best_solver_error_rate_on_verified_items
  error_validity_rate
  human_relative_gap
```

Overall score should be gated:

```text
if PackageValidityScore fails:
    OverallScore = 0
elif BenchmarkQualityScore fails:
    OverallScore = 0
else:
    OverallScore = BenchmarkQualityScore * FrontierResistanceScore
```

## Practical call plan

Cheap v2 pilot:

- 3 creator calls with Codex constructor access
- 3 validator calls
- 1 blind GPT-5.5 solver call on all validated packets
- 1 final judge call

Total: 8 GPT-5.5 calls plus whatever internal tool work each Codex creator performs.

Better v2 pilot:

- 5 creator calls
- 5 validator calls
- 2 blind solver calls with different prompt styles
- 1 final judge call

Total: 13 GPT-5.5 calls.

Full BenchBench run:

- multiple creator models
- independent validators
- solver gauntlet across models
- human baseline on only the best verified candidates

Do not spend human-baseline effort until the package passes generator/verifier/scorer gates.

## Best near-term benchmark direction from v1

The strongest v1 direction was **Constraint Delta Repair**:

- input: old operational spec + change request
- output: minimal required downstream edits
- gold: exact required edits and forbidden edits
- failure mode: over-editing, missing derived updates, stale derived text, touching unrelated clauses

To make it hard enough:

- require 2-4 dependent edits per item
- include decoy clauses that mention changed concepts but must not change
- include derived summaries, rule tables, user-facing text, and enforcement logic
- verify no alternate minimal edit set exists
- generate at least 50 private items and select a calibrated subset

