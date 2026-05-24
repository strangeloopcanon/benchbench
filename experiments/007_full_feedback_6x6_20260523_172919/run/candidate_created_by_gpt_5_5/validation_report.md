# Validation Report

## Package status

Generated with:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
```

The package is designed so `verifier.py` checks item/gold id alignment, answer
schema, dossier asset existence, and absence of private files in the solver
bundle.

Verification run:

```text
verified 30 items
```

## Capability claim

PAF measures whether a solver can reconstruct a deterministic adjudication from
scattered public evidence rather than from a clean table or a single obvious
algorithm. The target capability is careful cross-document accounting and policy
reasoning under adversarial exceptions.

## Solvability and identifiability

Each item is externally solvable from the public solver bundle. The referenced
dossier contains the member plan, pre-claim accumulators, benefit-year date
window, service schedule row, rider text, provider-network status,
authorization/referral correspondence, service-date check, and claim line. Those
facts identify every answer field:

- `status` and `reason_code` follow from the denial precedence visible in the
  benefit manual excerpts and the item evidence: date window, noncovered rider,
  network rule, authorization rule, and referral rule.
- `allowed_cents` is zero for denied claims. For approved in-network claims it
  is the service schedule amount; for approved PPO out-of-network claims it is
  55 percent of that amount.
- `patient_owes_cents` follows from deductible first, then copay, then
  coinsurance, capped by remaining out-of-pocket maximum.
- `insurer_pays_cents` is the allowed amount minus patient responsibility.

A qualified external solver can audit an answer by pointing to the dossier
sections above and recomputing the cents manually or with a small spreadsheet.
No private seed, generator trace, or hidden label is needed.

## Leakage controls

The solver bundle contains only `SOLVER_MANIFEST.json`,
`items_private_sample.jsonl`, `README.md`, and dossier Markdown files. It does
not contain gold answers, scorer/verifier/generator code, private audit traces,
or validation text. The item file lists only ids and relative dossier paths.

## Baselines

An obvious shortcut baseline that approves every claim with zero payment should
score poorly because many items require exact dollar calculations and denial
codes. A second simple baseline that denies everything should also miss all
approved items. The intended benchmark shape is partial recoverability: a solver
that reads denial evidence can get some rows, but exact saturation requires
following all money rules and rider exceptions.

Observed checks on the generated 30-item sample:

- Gold copy self-score: `30/30`.
- Approve-everything-with-zero-cents baseline: `0/30`.
- Deny-everything-as-missing-authorization baseline: `5/30`.
- Gold reason-code distribution: 12 `OK`, 7 `DATE`, 5 `NO_AUTH`, 3 `OON`, 2
  `NOT_COVERED`, and 1 `NO_REF`.
