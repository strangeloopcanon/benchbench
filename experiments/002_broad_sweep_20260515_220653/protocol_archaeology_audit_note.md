# Protocol Archaeology Audit Note

Status: unresolved, audit pending.

The broad sweep showed that GPT-5.2, GPT-5.4, GPT-5.5, and GPT-5.5 xhigh all
scored 0/30 on Protocol Archaeology.

A later public-bundle-only specialist expression search also scored 0/30. That
is useful evidence, but it is not a final verdict. It raises the concern that
the public packet may be under-specified: the solver sees examples and a vague
protocol-family description, while the hidden generator uses fresh salts,
weights, a permutation, parity gates, nibble substitution, and folding.

Protocol Archaeology should therefore not be treated as a clean BenchBench win
yet. It should get a separate audit run that checks whether the public evidence
identifies the answer under a stated protocol class.

The audit run should answer:

- Is the public protocol class precise enough?
- Are the hidden parameters identifiable from the examples?
- Does a stronger specialist baseline score above chance?
- Can qualified humans or domain specialists solve a meaningful fraction under
  the same public packet?

Artifacts currently present in the candidate package:

- `score_specialist_public_expr.json`
- `score_specialist_oracle_family_search.json`
- `specialist_public_expr_audit.json`
- `specialist_oracle_family_search_audit.json`
- `predictions_specialist_public_expr.jsonl`
- `predictions_specialist_oracle_family_search.jsonl`
