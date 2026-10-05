# ReiFor Failure Modes

## Leakage / shortcut risks

- **Hidden answer key in solver bundle**: prevented by keeping `gold_private_sample.jsonl` and `private_generation_trace.jsonl` outside `solver_bundle/`.
- **Generator logic leaked**: prevented by shipping only the policy and case exhibits (no generator/verifier/scorer in solver bundle).
- **Trivial pattern hack**: receipts are rendered with shuffled fields and occasional noise fields; cases include adversarial mixes of caps/approvals/duplicates so a single brittle heuristic tends to fail.

## Ambiguity risks

- **Rounding disputes**: policy fixes half-up rounding at 2 decimals before cents.
- **Timezone/day boundaries**: policy defines the day as the receipt local date exactly as written.
- **Receipt validity**: policy enumerates required fields and explicit exception syntax.

## Baseline pitfalls (expected model errors)

- Forgetting per-day caps for MEALS/GROUND and instead capping per receipt.
- Not detecting duplicates (same merchant+date+currency+amount).
- Ignoring missing `nights` invalidation for LODGING.
- Mishandling tip caps (20% of pre-tip base).
- Treating approvals as advisory rather than overriding invalidity/caps (within stated limits).
