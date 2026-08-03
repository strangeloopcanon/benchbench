# Review Queue

## 1. Reimbursement Forensics — historical #1, original run invalid

Repair generator and verifier rounding with Decimal-only half-up arithmetic.
Create a new benchmark version, validate it from public evidence, and run a
complete fresh panel before canonical promotion. The existing Decimal audit
and retained-prediction rescore are enough for the historical comparison:
`12, 16, 11, 13, 11, 11` remains the best complete low-nonzero profile and
counts as a win over the challengers. No model rerun was used for that finding.

Evidence and affected item IDs are recorded in
[`adjudications/004_reimbursement_forensics.md`](adjudications/004_reimbursement_forensics.md).

## 2. Service Credit Forensics — invalid

Compute gold from the same public precedence rule that says corrected internal
timeline entries override monitoring states. Regenerate, validate, and rerun a
new version. The recorded all-zero row is not a difficulty signal.

Evidence is recorded in
[`adjudications/007_service_credit_forensics.md`](adjudications/007_service_credit_forensics.md).

## 3. Fable Creator Sweep — infrastructure incomplete

Model calls must emit typed terminal states. GPT-5.2's provider error and
Claude Opus's timeout need reruns after provider preflight and state handling
are repaired. They must not enter a score grid as `0/30`.

Evidence is recorded in
[`adjudications/008_fable_creator_sweep.md`](adjudications/008_fable_creator_sweep.md).
