# BenchBench GPT-5.5 Constructor Pilot - Corrected Summary

Date: 2026-05-15

Run directory:

`/Users/rohit/Documents/Codex/2026-05-14/can-we-also-make-a-benchbench/runs/gpt55_benchbench_v2_constructor_20260515_002648`

## What Was Tested

This run tested whether GPT-5.5, using Codex, could construct real benchmark packages rather than merely describe benchmark ideas.

The prompt required each creator to produce:

- `generator.py`
- `verifier.py`
- `scorer.py`
- `items_private_sample.jsonl`
- `gold_private_sample.jsonl`
- `solver_packet.md`
- validation and failure-mode notes

Then GPT-5.5+Codex was used as a blind solver against the generated benchmark items.

## Main Result

The constructor setup worked. GPT-5.5 produced substantially better benchmark artifacts once forced to build generator/verifier/scorer packages.

But no candidate was frontier-resistant against GPT-5.5+Codex.

| Candidate | Capability Tested | Package Validity | GPT-5.5+Codex Solver Score | Result |
| --- | --- | --- | --- | --- |
| `constraint_delta_hard` | Minimal downstream edits after an operational spec change | Valid / conditional on solver isolation | 30/30 | Clean package, not hard |
| `state_machine_residual` | Repair stale ledger rows after a state-machine transition patch | Valid / conditional on solver isolation | 30/30 | Best validation hygiene, not hard |
| `web_grounded_residual` | Repair synthetic web-grounded tracker rows using source precedence rules | Valid / conditional on solver isolation | 29/30 | Best resistance, still not hard |

The strongest candidate by validation hygiene was `state_machine_residual`.

The strongest candidate by observed solver resistance was `web_grounded_residual`, but it only caused one miss out of thirty items.

## Corrected Solver Note

The original automated solver pass was invalid for `state_machine_residual` and `web_grounded_residual` because their `solver_packet.md` files did not include the actual private item payloads. The corrected solver runs supplied both `solver_packet.md` and `items_private_sample.jsonl`.

Corrected scores:

- `candidate_state_machine_residual/score_solver_with_items.json`: 30/30
- `candidate_web_grounded_residual/score_solver_with_items.json`: 29/30

The pre-correction `final_judge.md` is useful for the validation pass, but its "inconclusive" judgments for those two candidates are stale.

## The One GPT-5.5 Miss

`web_grounded_residual` item `WGR-12345-001` required three row updates: `R01`, `R06`, and `R07`.

GPT-5.5 returned only `R06` and `R07`. It missed `R01`, where the current authoritative source before the `2026-06-01` as-of date superseded an older current tracker row, while a later authority source had to be ignored as future-dated.

That is a real failure mode: source precedence plus stale-current detection. But one miss in thirty is not enough for BenchBench acceptance.

## Token Use

Original v2 run:

- 10 GPT-5.5 Codex calls
- 697,387 reported tokens

Corrected solver reruns:

- `state_machine_residual`: 164,122 reported tokens
- `web_grounded_residual`: 148,215 reported tokens

Total including corrections:

- 1,009,724 reported tokens

## What Worked

- Requiring runnable artifacts fixed the v1 problem where good benchmark ideas had broken or ambiguous gold keys.
- Generator/verifier/scorer discipline made the packages inspectable and reproducible.
- The best candidates targeted plausible residual axes: change-impact repair, state transition residuals, and source-precedence ledger repair.

## What Did Not Work

- GPT-5.5+Codex could solve the deterministic benchmark packages by turning visible rules into computation.
- The candidates were residual-looking, but not frontier-resistant.
- Solver-bundle construction was under-specified: two candidates had valid items but incomplete solver packets.

## Prompt/Setup Lessons

For the next version, BenchBench should require:

1. A solver-visible bundle manifest proving exactly what the blind solver receives.
2. A validator check that the solver bundle contains the expected number of private items.
3. Strict isolation: the solver must run in a clean directory with no gold, generator, verifier, scorer, validation, or prior prediction files.
4. Separate solver tracks:
   - tool-enabled Codex solver
   - no-tools text solver
   - web-enabled solver, only if benchmark rules require web
5. An adversarial pre-screen loop: the creator must generate many verified items, run or simulate baseline solvers, and select only items that survive.
6. Explicit resistance to code-reduction for the Codex track. If all rules and data are visible and deterministic, GPT-5.5+Codex will often convert the task into a script.

## Bottom Line

BenchBench looks viable as a meta-eval of benchmark construction quality. The constructor-mode prompt is much better than idea-only prompting.

But this pilot did not produce a benchmark that GPT-5.5+Codex could not beat. The best observed frontier-resistant signal was only a 3.3% error rate.

