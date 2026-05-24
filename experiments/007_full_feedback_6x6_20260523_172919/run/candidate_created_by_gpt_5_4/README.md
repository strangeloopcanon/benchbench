# Catalog Royalty Forensics (CRF) v1

CRF is a benchmark about reconstructing quarter-end royalty statements from a public solver packet.

Each item includes:
- a public rulebook;
- a base rights rider;
- one or more amendments;
- a finance memo with advance and reserve-release facts;
- a sales statement CSV.

The solver must return exact JSON with:
- `included_units`
- `earned_royalty_cents`
- `recouped_advance_cents`
- `payable_cents`

The benchmark is closest to BenchBench's Reimbursement Forensics because both are messy finite-evidence audit tasks with exact numeric outputs. It is not a duplicate because the mechanics are different: this package centers on rights scope, later-amendment precedence, discount floors, promo exceptions, reserve withholding, and advance recoupment.

## Why this should be hard

This is not one clean algorithm with one clean state machine. The hard part is deciding which rows count, which later amendment wins, when promo rows revive at partial value, when bundle allocation replaces gross, and how reserve withholding and advance recoupment interact with net payable.

## Creator-side contract

Generate the 30-item sample:

`/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .`

Verify item and gold consistency:

`/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`

Score predictions:

`/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

## Solver-side boundary

An external solver should use only `solver_bundle/`. The bundle contains enough information in principle to derive every answer without private labels, hidden seeds, or creator-only conventions.
