# PAL failure modes and mitigations

| Risk | Why it matters | Mitigation in this package |
|---|---|---|
| Unstated real-world policy conventions | A solver might reasonably apply deny-overrides or inherited tags even though the item did not say so. | The packet supplies an exhaustive operational semantics, including the explicit winner tuple, default, and non-inherited tags. |
| Ambiguous precedence | Equal-priority policies can make a single decision unknowable. | Every tie is resolved deterministically by scope depth and array position. The verifier recomputes each gold answer. |
| Impossible private inference | A task could secretly depend on a seed or generator-only annotation. | Every fact used by evaluation occurs in the item; the seed and gold are not needed by a solver. |
| Answer-format accidents dominate | A correct interpreter can lose to punctuation. | The format is short, fixed, and has exactly ten ordered components; the scorer reports a component-level diagnostic in addition to strict score. |
| Default-deny shortcut | Always predicting a denial may earn misleadingly high performance. | Each generated item intentionally includes decision flips, provenance-only changes, stable allows, and stable denials; provenance is mandatory. |
| Generator bug or drift | Gold may not correspond to public rules. | `verifier.py` validates structure and independently recomputes every gold string from the public items. |
| Solver-bundle leakage | Gold labels or implementation traces could make the test trivial. | The manifest lists only the items and semantics README; validation includes a leakage scan. |
| Duplicate of ordinary access-control QA | The task might only measure familiarity with ACL vocabulary. | IDs are abstract and no conventional semantics are assumed. Difficulty comes from executing the stated two-world, transitive, ordered semantics with provenance. |
