# BenchBench Prompt Setup v3 Delta

Date: 2026-05-15

This is the v3 delta after the corrected GPT-5.5 constructor pilot.

## Core Change

The v2 prompt made creators build valid benchmark packages. That worked.

The v3 prompt must make creators build packages that survive a tool-enabled frontier solver. That requires adversarial item selection and solver-bundle isolation, not just generator/verifier/scorer discipline.

## Add To Creator Contract

Creators must now produce:

```text
candidate_<id>/
  README.md
  benchmark_spec.json
  generator.py
  verifier.py
  scorer.py
  items_dev.jsonl
  items_private_pool.jsonl
  items_private_sample.jsonl
  gold_private_pool.jsonl
  gold_private_sample.jsonl
  solver_bundle/
    SOLVER_MANIFEST.json
    solver_packet.md
    items_private_sample.jsonl
  validation_report.md
  adversarial_selection_report.md
  failure_modes.md
```

`solver_bundle/` is the only directory the blind solver may see.

## New Hard Requirements

1. Generate a larger private pool, not just the final sample.
2. Verify every item in the pool.
3. Run at least one baseline or heuristic solver over the pool.
4. Select the final private sample from verified items that survive the baseline.
5. State why a GPT-5.5+Codex solver cannot trivially convert the visible task into a deterministic script.
6. Include `SOLVER_MANIFEST.json` with item count, allowed tools, disallowed files, output schema, and benchmark rules.
7. The validator must check that the solver bundle contains the expected item count.
8. The validator must fail any package where private items are only available outside the solver bundle.

## Solver Tracks

BenchBench should report separate scores for:

- `chat_no_tools`: model sees solver packet and items, no code execution.
- `codex_tools`: model may use Codex and local computation, but only inside the solver bundle.
- `web_allowed`: model may browse only when benchmark rules require external retrieval.

The corrected pilot shows that `codex_tools` is much harder to beat. A benchmark that is hard in `chat_no_tools` but easy in `codex_tools` is still useful, but it should not be labeled frontier-resistant for the Codex track.

## Creator Prompt Insert

Add this block to every serious creator prompt:

```text
You are designing for a tool-enabled GPT-5.5+Codex solver, not just a chat model.

Assume the solver can:
- write scripts
- parse JSON
- brute-force small search spaces
- recompute deterministic rules
- inspect all files inside the solver bundle

Do not rely on arithmetic burden, formatting burden, large but regular tables, or visible deterministic transformations as the source of hardness.

Your benchmark must either:
- test a capability that remains difficult even with local computation, or
- explicitly define itself as a no-tools/chat-only benchmark.

Generate a larger verified item pool, run a baseline or heuristic solver, and select final items that the baseline fails for interpretable reasons. Report the selection procedure.
```

## Validator Prompt Insert

Add:

```text
Before validating hardness, validate solver isolation.

Check:
1. `solver_bundle/SOLVER_MANIFEST.json` exists.
2. The bundle contains the expected number of private items.
3. The bundle contains no gold, oracle fields, verifier logic, generator logic, score files, prior predictions, or validation reports.
4. The solver can complete the benchmark using only files in the bundle.
5. If the task is deterministic and all rules/data are visible, estimate whether a short script would solve it.

Fail the package if the solver bundle is incomplete or contaminated.
```

## Final Judge Change

The final judge should compute:

```text
Package validity: pass/fail
Solver isolation: pass/fail
Human solvability plan: pass/fail
Chat no-tools score: numeric
Codex tools score: numeric
Best frontier score: max over frontier solver tracks
Accepted frontier-resistant: best frontier score <= threshold
```

The current pilot's candidates would score:

- package validity: pass/conditional
- solver isolation: initially failed for two candidates, corrected manually
- Codex tools scores: 100%, 100%, 96.7%
- accepted frontier-resistant: no

## Practical v3 Run Plan

Run one expensive but cleaner pilot before broadening to major models:

1. Three GPT-5.5 creator variants.
2. One independent GPT-5.5 validator per candidate.
3. One GPT-5.5 no-tools solver per candidate.
4. One GPT-5.5+Codex solver per candidate in isolated solver bundle.
5. One final judge.

Only after a candidate gets below 50% on GPT-5.5+Codex should we spend human-baseline effort.

