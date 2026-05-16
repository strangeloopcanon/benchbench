# Failure Modes

## Benchmark Failure Risks

- The generated transformations may be too easy for agents that immediately
  write a broad program synthesizer.
- Some items may be underdetermined in a mathematical sense even if the intended
  transformation is unique under the generator family.
- Human baselines are planned, not yet measured, so the current package should
  be treated as an MVP candidate rather than a validated leaderboard.
- Exact matching can undercount answers with harmless formatting differences;
  this is deliberate to keep grading deterministic and cheap.

## Solver Failure Modes This Benchmark Targets

- Overfitting a response pattern from one or two examples.
- Assuming the transformation is linear when parity-gated swaps create branch
  behavior.
- Treating byte positions independently despite permutation and folded checksum
  coupling.
- Producing plausible-looking hex without validating it against all examples.
- Writing brittle one-off code that fits sample traces but fails on the query.

## Repair Policy

Bad items should be retired by id, not silently edited after publication. A new
version should record the seed, verifier output, item-level pass rates, and the
reason each retired item failed.

