# Prior Authorization Forensics (PAF) v1

PAF is a deterministic cross-document adjudication benchmark. Each item is a
fictional health-insurance claim dossier. A solver must decide whether the claim
is approved and compute the exact allowed amount, insurer payment, and patient
responsibility in integer cents.

The benchmark is meant to test careful forensic reasoning over messy but finite
evidence: plan type, service schedule, member riders, network status, prior
authorization, referral correspondence, service-date validity, deductible
accumulators, coinsurance, copays, and out-of-pocket caps.

## Required commands

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

## Output contract

Gold rows and prediction rows contain exactly `id` and `answer`. The answer is:

```json
{
  "status": "approved",
  "reason_code": "OK",
  "allowed_cents": 185000,
  "insurer_pays_cents": 110000,
  "patient_owes_cents": 75000
}
```

Allowed reason codes are `OK`, `NO_AUTH`, `NO_REF`, `OON`, `NOT_COVERED`, and
`DATE`. Denied claims use zero for all cent fields.

## Why this is not a duplicate

PAF is closest to Reimbursement Forensics because both use messy public evidence
and exact money calculations. It is not a copy: the hard parts here are
benefit-plan eligibility, authorization/referral denial precedence, out-of-
network handling, rider overrides, deductible/copay/coinsurance sequencing, and
out-of-pocket caps.

It is also adjacent to document-understanding and rule-following benchmarks,
but the task is neither open-ended extraction nor a clean algorithmic puzzle.
The public solver bundle contains all evidence, and the grader checks a closed
schema exactly.
