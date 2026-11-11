# CFPS failure modes and boundaries

## What this benchmark is meant to catch

- Reversing the two levels of Boolean composition: a channel is OR over recipes; an operation is AND over channels.
- Treating a revoked permission as satisfying a recipe instead of breaking it.
- Blocking an attack only when every channel closes.  CFPS requires only one required channel to close.
- Preserving a service when one channel remains open.  CFPS requires every service channel to remain open.
- Finding a feasible policy but ignoring cost, cardinality, or canonical lexicographic tie-breaking.
- Using an optimizer with a subtly different model and accepting a plausible-looking policy without simulation.

## Deliberate limits

The instances are finite, static, monotone Boolean policy models.  They do not claim to simulate real authorization systems, network topology, temporal access, probabilistic risk, or adversarial adaptation.  CFPS measures formal policy synthesis under its stated rules, not practical security expertise.

## Evaluation hazards

- Gold answers must never be placed in `solver_bundle/`, including as comments, filenames, cached output, or generator code.
- A solver should not be rewarded for outputting a noncanonical but equivalent policy: canonicalization is part of the task and scoring is exact.
- Natural-language explanations should not receive partial credit; the response contract accepts only JSONL `id`/`answer` pairs.
- Future larger releases should use unseen seeds and should retain semantic recomputation in the verifier.  A fixed 30-item sample is appropriate for package validation, not for training-data-contamination claims.
