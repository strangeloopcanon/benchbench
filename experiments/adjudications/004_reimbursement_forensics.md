# Adjudication: Reimbursement Forensics (Experiment 004)

Outcome: **#1 corrected historical candidate and a win over challengers;
original run invalid and not canonical**.

The historical generator and verifier convert a Decimal half-up dollar amount to cents through binary floating-point multiplication and integer truncation. That is not Decimal half-up rounding. The digest-locked evidence is recorded in `../registry.v1.json`.

The independent recomputation is executable with
`python scripts/audit_reimbursement_decimal.py`; its regression test is
`tests/test_reimbursement_decimal_audit.py`. It reads the preserved public
receipt assets and rates directly and performs every monetary operation with
`Decimal`.

| evidence | SHA-256 |
|---|---|
| `run/candidate_created_by_gpt_5_2/generator.py` | `559263a39ce315710182a559dc8af1af55322f51469cc59f8d5288a8e23fb775` |
| `run/candidate_created_by_gpt_5_2/verifier.py` | `64c953d2d8bc1350f63eaa07ad9782b280b1d10762b07ddec02b683957f5537c` |

An independent Decimal re-audit changes these gold answers:

| item | historical gold cents | Decimal half-up cents |
|---|---:|---:|
| `reifor_0000` | 15991 | 15992 |
| `reifor_0006` | 56636 | 56637 |
| `reifor_0029` | 30627 | 30629 |

The retained historical solver predictions rescore from `10, 14, 11, 12, 11, 11` to `12, 16, 11, 13, 11, 11` out of 30. No model was rerun.

## Historical comparison

On corrected gold, Reimbursement Forensics remains the **#1 historical
candidate** and should be counted as a **win over the challengers**. Every
retained solver remains in the low nonzero band (`11-16/30`). Later challenger
rows reach at least `25/30`, have invalid gold, or have incomplete panels. None
matches that complete, uniformly difficult score shape.

This does not repair or validate the original run. Its emitted gold was wrong,
so it cannot be a canonical incumbent or enter the stable benchmark bank. The
corrected rescore supports a qualified historical comparison only.

Required resolution: repair both generator and verifier with Decimal-only half-up rounding, create a new benchmark version, validate the public/private contract, and execute a complete fresh solver panel.
