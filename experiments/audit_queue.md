# Audit Queue

Run these checks before using the next experiment as evidence or freezing a new
candidate.

## 1. Reimbursement Forensics

Status: frozen incumbent, not accepted.

Source: `004_feedback_sweep_20260522_225208`, with Claude Opus extension.

Why audit it: it is the only current candidate where all six tested solvers
landed in the low nonzero band.

Audit checks:

- Confirm the public solver bundle contains enough evidence to solve each item.
- Check that answer fields are identifiable without private labels or generator
  vocabulary.
- Review representative wrong solver answers against the gold answers.
- Confirm the scorer accepts the stated answer format and is not overfitting to
  hidden implementation details.
- Scan for leakage from private gold answers, generator logic, seeds, traces, or
  answer keys.

Decision after audit:

- Promote to stable bank if the low scores reflect real difficulty.
- Repair and rerun if the package is good but the scorer or wording is unfair.
- Demote if the task is under-specified, leaky, or impossible from public
  evidence.

## 2. Service Credit Forensics

Status: all-zero challenger; audit required.

Source: `007_full_feedback_6x6_20260523_172919`.

Why audit it: all six solvers scored 0/30, but field-level inspection suggests
the exact eligible-downtime field may be the bottleneck rather than the whole
task.

Audit checks:

- Inspect the public packet for each item and confirm that eligible downtime is
  externally identifiable.
- Compare solver outputs to gold at the field level.
- Check whether solvers found the breach, credit percent, or credit amount but
  missed only one strict subfield.
- Verify the scorer is not rejecting semantically equivalent downtime
  calculations because of unstated rounding, interval, or exclusion rules.
- Decide whether a repaired scorer or clearer public rule would make the row
  low-nonzero instead of all-zero.

Decision after audit:

- Keep as a challenger only if the all-zero result reflects real, fair
  difficulty.
- Otherwise mark it as a scorer/specification failure and do not use it as a
  benchmark-quality signal.
