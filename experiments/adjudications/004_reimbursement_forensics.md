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

## Root-Cause Audit: Why Historical Gold Was Low (`APPROVAL_RE` & Tip Convention)

Running **Halcyon** (`experiments/extensions/004_halcyon_solver_20261003`) on the preserved Experiment 004 bundle revealed that four independent models (`Halcyon`, `GPT-5.5`, `Gemini 3.5 Flash`, and `Claude Opus`) agreed with each other on **26–30 out of 30 items**, yet all scored `11/30` against the historical/Decimal-recomputed gold.

Direct code inspection of `generator.py` and `verifier.py` uncovered three compounding defects in the original gold calculation:
1. **Broken `APPROVAL_RE` regular expression (`0/30` email approvals parsed)**:
   - `generator.py` (line 390) and `verifier.py` (line 53) defined:
     ```python
     APPROVAL_RE = re.compile(r"APPROVE RECEIPT\\s+(?P<rid>[A-Z0-9_\\-]+)\\s+\\[(?P<mode>FULL|PARTIAL(?:\\s+\\d+)?)\\]")
     ```
   - This raw string double-escaped `\s` (`\\s+` matches a literal backslash + `s`) and restricted `<rid>` to uppercase `[A-Z0-9_\-]+`, whereas every receipt ID in `emails.txt` uses lowercase `reifor_0000_R5`. Consequently, **`APPROVAL_RE` matched 0 out of 30 email approvals** when computing `gold_private_sample.jsonl`—even though `generate_case` recorded those approvals in `private_generation_trace.jsonl`.
2. **Dropped approved receipts with missing `cat=?` or `nights=?`**:
   - Even if `APPROVAL_RE` had matched, the summation loop only added `MISC`, `LODGING` (multiplying by `nights=0` when `nights=?`), `AIR`, `GROUND`, and `MEALS`, silently dropping approved receipts with `cat=?` (`reifor_0002_R3`, `reifor_0023_R3`) and capping approved receipts at non-approved category limits.
3. **Unstated `tip=` subtraction convention**:
   - `generator.py` internally subtracted `tip` from `amount` (`base = amount - tip`), whereas `solver_bundle/common/policy.md` never stated that `amount` included `tip`.

When `scripts/audit_reimbursement_decimal.py` evaluates the retained predictions (and Halcyon's extension predictions) against the **actual policy** (`actual_policy_case_total`, fixing `APPROVAL_RE` to match `reifor_xxxx_Ry`, honoring email approvals, and converting `amount` and `tip` per `policy.md`):
- **GPT-5.5**: **`30/30` (`100%`)**
- **Gemini 3.5 Flash (High)**: **`30/30` (`100%`)**
- **Halcyon**: **`29/30` (`96.7%`)** (or `30/30` when `[FULL]` approvals on otherwise-valid `MEALS` receipts respect the daily cap)
- **Claude Opus**: **`25/30` (`83.3%`)** (or `28/30` when `[FULL]` approvals remain subject to category caps)
- **GPT-5.4**: **`25/30` (`83.3%`)** (under post-tip `amount`) / `19/30` (under pre-tip `amount`)
- **Gemini 3.1 Pro**: **`25/30` (`83.3%`)** (under post-tip `amount`) / `16/30` (under pre-tip `amount`)

## Repaired Benchmark Version (`Experiment 015`: Reimbursement Forensics v2 — Actual Policy)

To evaluate the current frontier panel against the actual policy without regex bugs or unstated conventions, `experiments/015_reimbursement_forensics_v2_20261004` repairs `generator.py`, `verifier.py`, `scorer.py` (`schema_version: 2`), and `solver_bundle/common/policy.md` on the same 30-case seed (`20260516`), passing `local_validate()` (`valid: True`, `deterministic: True`, `frozen_package_match: True`, `leak_matches: []`).

Live solver evaluation on `Experiment 015` (with Python tool execution enabled):

| Solver | Provider | Score | Accuracy | Reported Tokens | Non-Cache (`in+out`) Tokens | Extension Overlay |
|---|---|---:|---:|---:|---:|---|
| **Halcyon** | Antigravity (`agy:halcyon`) | **30/30** | **100.0%** | 283,403 | 283,403 | `experiments/extensions/015_halcyon_solver_20261004` |
| **Claude Opus 5.5 (High)** | Cursor (`cursor:claude-opus-5-5-high`) | **30/30** | **100.0%** | 281,781 | 6,132 | `experiments/extensions/015_cursor_opus_55_solver_20261004` |
| **GPT-6-Sol (High)** | Codex (`gpt-6-sol@high`) | **30/30** | **100.0%** | 45,738 | 45,738 | `experiments/extensions/015_codex_gpt_6_sol_solver_20261004` |
| **GLM 5.2 (High)** | Cursor (`cursor:glm-5.2-high`) | **30/30** | **100.0%** | 736,818 | 62,994 | `experiments/extensions/015_cursor_glm_52_solver_20261004` |

*(When Python execution was disabled in Cursor, `Claude Opus 5.5` still scored `30/30` in `661,200` tokens by hand, while `GLM 5.2 (High)` dropped to `17/30` in `79,067` tokens.)*


