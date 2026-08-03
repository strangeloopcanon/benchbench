# BenchBench

BenchBench tests whether a model can create a benchmark package that strong
solvers cannot simply clear. A creator supplies public solver evidence, private
gold, a generator, verifier, scorer, and an explanation of likely failures.

## Current Result

**There is no validated incumbent.**

Reimbursement Forensics remains the **#1 corrected historical candidate** and
counts as a win over the later challengers. Recomputing its gold with Decimal
half-up arithmetic and rescoring the retained predictions gives `12/30,
16/30, 11/30, 13/30, 11/30, 11/30`: all six scores remain low and nonzero,
while later challenger rows reach at least `25/30`, are invalid, or are
incomplete. No model was rerun for this comparison.

That historical win is not a canonical promotion. The original Reimbursement
Forensics run remains invalid because its emitted gold violated Decimal
half-up rounding. Service Credit Forensics is also invalid because its public
evidence and gold use conflicting precedence rules. The Fable creator run is
incomplete: GPT-5.2 had a provider error and Claude Opus timed out. Those are
execution states, not `0/30` results.

### Experiment 010 results

| Creator | Candidate | Sol high | Terra extra high | Gemini 3.6 Flash high | Opus 5 high |
|---|---|---:|---:|---:|---:|
| Sol | AuditWeave | 30/30 | 30/30 | 30/30 | Did not complete |
| Terra | Counterfactual Firewall Policy Synthesis | 30/30 | 30/30 | 30/30 | Did not complete |
| Gemini Flash | No valid candidate | — | — | — | — |
| Opus | Consolidation Point | 30/30 | 30/30 | 30/30 | 30/30 |

Gemini produced no mechanically valid candidate, but its three solver results
are valid and remain in the record. “Did not complete” is an execution state,
not `0/30`; the retained Opus runtime identity is requested/unverified.

![Canonical status](experiments/canonical/figures/canonical_status.svg)

The complete, digest-backed record is in
[`experiments/registry.v1.json`](experiments/registry.v1.json). The generated
canonical view preserves historical numbers as noncanonical evidence and
promotes nothing without a fresh validated run:
[`experiments/canonical/README.md`](experiments/canonical/README.md).

## What BenchBench Measures

A valid candidate needs more than low scores. It needs public evidence that
supports every answer, a private gold path that follows the public rules,
deterministic scoring, complete successful solver cells, and an execution
environment that keeps private material inaccessible to solvers.

That is why a `0/30` can mean several different things: hard task, invalid
gold, provider error, timeout, malformed output, or an incomplete panel. Only
the first can contribute to a benchmark claim, and only after adjudication.

## Next Run

The target panel is Codex GPT-5.6 Sol high, Codex GPT-5.6 Terra extra high,
Gemini 3.6 Flash through Antigravity, and Claude Opus 5. Live execution is
enabled for Codex and Antigravity. Cursor remains preflight-only until it has a
credential-safe shell boundary, so a new four-model run needs another audited
Opus provider. Exact commands and safety limits are in
[`docs/running.md`](docs/running.md).

Treat Reimbursement Forensics as the historical target to beat, not as a
validated incumbent or reusable benchmark package. Do not reuse Service Credit
Forensics as an incumbent, and do not backfill failed solver cells as scores.
Historical run folders remain immutable; solver extensions publish into new
overlay roots.

The required historical resolutions are in:

- [`experiments/adjudications/004_reimbursement_forensics.md`](experiments/adjudications/004_reimbursement_forensics.md)
- [`experiments/adjudications/007_service_credit_forensics.md`](experiments/adjudications/007_service_credit_forensics.md)
- [`experiments/adjudications/008_fable_creator_sweep.md`](experiments/adjudications/008_fable_creator_sweep.md)
- [`experiments/adjudications/010_four_model_panel.md`](experiments/adjudications/010_four_model_panel.md)
- [`experiments/adjudications/010_provider_recovery_20260802.md`](experiments/adjudications/010_provider_recovery_20260802.md)

## Repo Map

- `run_broad_three_model_sweep.py`: creator/solver sweep harness.
- `benchbench_model_backends.py`: provider dispatch.
- `benchbench_results.py`: prediction and score parsing.
- `experiments/registry.v1.json`: authoritative experiment and adjudication registry.
- `scripts/build_6x6_result_artifacts.py`: deterministic canonical-status generator.
- `scripts/prepare_public_evidence.py`: public-evidence sanitizer and digest rebinder.
- `scripts/build_benchmark_landscape_pack.py`: landscape pack builder.
- `docs/methodology.md`: evaluation method.
