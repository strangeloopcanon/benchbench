# Failure modes and mitigations

## Solver failure modes the benchmark intentionally exposes

- Treating file order as event order instead of enumerating DAG linearizations.
- Applying `mix` sequentially rather than from two old register values.
- Applying a `route` or `flip_if` condition after, rather than before, its own update.
- Mishandling negative modulo or failing to canonicalize registers after every operation.
- Checking only the last audit, or applying audits after query operations.
- Selecting the first locally feasible candidate without propagating states through later phases.
- Losing distinct states by deduplicating on audit values rather than full state plus label.
- Returning the reconstructed checkpoint state instead of the post-query state.

## Benchmark-design risks and mitigations

- **Ambiguity:** a weak audit can admit many histories. Generation exhaustively rejects an item unless all audit-consistent histories yield exactly one answer; verification repeats the search from public data.
- **Impossible/private-keyed reasoning:** every transition, precedence edge, audit formula, candidate, and query is in the solver bundle. The stated direct enumeration algorithm is sufficient.
- **Label-position shortcut:** the planted operation is shuffled uniformly among A-D and labels carry no semantic ordering. The exact answer also requires a post-query state.
- **Input-order shortcut:** JSON event order is independent of the planted legal order. A measured input-order/A baseline is reported in validation.
- **Audit inversion shortcut:** audits are lossy modular projections, not encodings of the requested post-query state. Multiple internal histories may survive; answer-identifiability, not hidden-history uniqueness, is the criterion.
- **Generator leakage:** solver ids expose only sequence number. The public manifest omits generation seed and attempt counts; private audit metadata stays outside the bundle.
- **Tool triviality:** exhaustive search is intentionally allowed, but requires a faithful implementation of eight conditional/noncommutative operations, DAG enumeration, checkpoint filtering, and counterfactual execution. Runtime is modest so the benchmark measures reasoning/implementation, not compute access.
- **Overfitting to one sample:** the deterministic generator supports fresh seeds and counts. Scores from differently seeded releases should not be compared without recording the release parameters privately.

## Scope limitations

The language is synthetic and tests formal reconstruction rather than domain
knowledge. Exact-match scoring gives no partial credit. The included sample has
not yet been calibrated across a broad model panel, so difficulty claims are
based on structural baselines and task analysis, not a model rank matrix.
