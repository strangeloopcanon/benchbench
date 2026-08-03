# Failure modes and mitigations

## Solver failure modes the benchmark intends to expose

- Treating wrapped counter values as ordinary monotone timestamps.
- Assuming manifest station names equal local node names.
- Assigning rates independently and forgetting the all-different constraint.
- Matching send and receive records independently, breaking packet identity.
- Greedily choosing a locally plausible manifest instead of enforcing a route
  bijection.
- Fitting clocks to the corrupted point without robust one-error accounting.
- Finding a plausible explanation but failing to test whether another answer
  also satisfies every public rule.
- Producing malformed JSONL, duplicate IDs, or a correct record with the wrong
  repaired residue.

## Benchmark-design failure modes and current controls

- **Ambiguous gold:** generator acceptance and `verifier.py` enumerate public
  explanations and require one answer pair. If a fresh seed produces an
  ambiguous item, generation rejects it.
- **Private-keyed difficulty:** no secret predicate is used. The private answer
  is recomputed from the solver-visible constraints, not trusted from generator
  state.
- **Leakage:** public aliases and record IDs carry no answer bit; corruption
  location is sampled after chronological IDs are assigned. The bundle has a
  three-file allowlist and was text-inspected.
- **Order leakage:** record order is explicitly declared truthful and may be
  used. The reference certificate does not need it, so order is supporting
  evidence rather than an answer key.
- **Raw-jump shortcut:** modular clocks naturally have large clean jumps. The
  largest-adjacent-jump baseline scores 0/30.
- **Always blame a fixed node or position:** corruption is sampled uniformly
  over all 38 records per generated item. A larger release should audit the
  realized node/position distribution and may stratify it.
- **Generator overfitting:** the public packet states a general constraint
  model, while the canonical sample uses fixed node/count dimensions. Future
  versions should vary graph size, route multiplicity, and rate-set size while
  preserving the same rules.
- **Unmeasured frontier difficulty:** no claim is made from the weak baseline
  alone. Run strong tool-enabled solvers before treating results as calibrated;
  if they saturate, increase dimensions or introduce public clock-law variants
  rather than hiding information.
- **Reference implementation bug:** `verifier.py` checks structure and derives
  answers independently of stored generator state, but it shares
  `reference_core.py` with generation. An ideal external audit should implement
  the public equations separately and compare all 30 answers.
- **Metric gaming:** exact accuracy is primary. Component accuracies are labeled
  diagnostics so guessing one field cannot masquerade as solving an item.

## What should invalidate an item

An item should be removed if the public rules admit two different repair
answers, no repair answer, an offset that cannot be evidenced by public clean
records, inconsistent packet endpoints, or any solver-bundle content that
reveals private labels. A low model score by itself is not evidence of quality;
human or independent-solver identifiability remains mandatory.
