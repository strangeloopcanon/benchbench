# Review Queue

Run these checks before using a new low-scoring result as evidence or freezing a
candidate.

## 1. Reimbursement Forensics

Status: current target to beat.

Source: `004_feedback_sweep_20260522_225208`, with Claude Opus extension.

Why check it: it is the only current candidate where all six tested solvers
landed in the low nonzero band.

Review checks:

- Confirm the public solver bundle contains enough evidence for each item.
- Check that answer fields are identifiable without private labels or generator
  vocabulary.
- Review representative wrong solver answers against the gold answers.
- Confirm the scorer accepts the stated answer format and is not tied to
  hidden implementation details.
- Scan for leakage from private gold answers, generator logic, seeds, traces, or
  answer keys.

Decision after review:

- Promote to stable bank if the low scores reflect real difficulty.
- Repair and rerun if the package is good but the scorer or wording is unfair.
- Demote if the task is under-specified, leaky, or impossible from public
  evidence.

## 2. Service Credit Forensics

Status: raw Experiment 007 all-zero problem case.

Source: `007_full_feedback_6x6_20260523_172919`.

Why check it: all six solvers scored 0/30, but field-level inspection suggests
the eligible-downtime field may be the bottleneck rather than the whole task.

Review checks:

- Inspect the public packet for each item and confirm that eligible downtime is
  externally identifiable.
- Compare solver outputs to gold at the field level.
- Check whether solvers found the breach, credit percent, or credit amount but
  missed only one strict subfield.
- Verify the scorer is not rejecting semantically equivalent downtime
  calculations because of unstated rounding, interval, or exclusion rules.
- Decide whether a repaired scorer or clearer public rule would make the row
  low-nonzero instead of all-zero.

Decision after review:

- Keep as a challenger only if the all-zero result reflects real, fair
  difficulty.
- Otherwise mark it as a scorer or specification failure and do not use it as a
  benchmark-quality signal.
