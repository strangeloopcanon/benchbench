# Validation Report

## Benchmark

Catalog Royalty Forensics (CRF) v1

CRF asks a solver to reconstruct exact quarter-end royalty outputs from public contract documents and public sales evidence. The benchmark is designed to look more like messy statement review than like a clean puzzle with one obvious abstraction.

## What I Ran

Generation:

`/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .`

Verifier:

`/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`

Result: `OK: items, assets, and gold answers are consistent.`

Gold self-score:

`/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

Result: `30/30`

Weak shortcut baseline:

- Baseline shape: parse only the base rider, ignore amendments, ignore promo revivals, use `gross_cents` rather than bundle allocation, and skip the contractual discount-floor logic.
- Score: `5/30`

This is the target direction: the benchmark is clearly solvable by a rules-following external solver, but brittle shortcut logic misses most rows.

## External Solvability And Identifiability

This package is externally solvable in principle.

Why:

- Every item exposes the full public rulebook.
- Every item exposes the base rights rider.
- Every item exposes all later amendments that can change inclusion, rate, territory, channel, promo treatment, or recognized-base multiplier.
- Every item exposes the finance memo with the opening advance and reserve release facts.
- Every item exposes the full sales statement CSV used for scoring.

No answer field depends on hidden labels, generator-only conventions, or private strings.

An external solver can determine each field as follows:

- `included_units`: inspect each public sales row, apply public inclusion rules plus public amendments, and sum signed included units.
- `earned_royalty_cents`: for each included row, derive public recognized base, choose the public applicable rate, truncate toward zero, and sum.
- `recouped_advance_cents`: apply the public `min(max(earned_royalty_cents, 0), opening_advance_cents)` rule using the public finance memo.
- `payable_cents`: compute public reserve withholding from positive physical-row earnings, then apply the public payable formula using the finance memo's reserve release and opening advance.

This is hard because the solver has to line up several public documents and several interacting rule layers, not because the package hides information.

## Leakage Check

I inspected the public solver bundle boundary.

- The solver bundle contains `README.md`, `SOLVER_MANIFEST.json`, `public_rulebook.md`, `items_private_sample.jsonl`, and per-item public assets only.
- It does not contain `gold_private_sample.jsonl`.
- It does not contain `generator.py`, `verifier.py`, `scorer.py`, `validation_report.md`, or private audit traces.
- Public files do mention the public answer field names, but they do not include per-item gold values or a hidden key.

The solver bundle currently contains 124 files, all under `solver_bundle/`.

## Generated Sample Shape

Across the 30 generated items:

- `included_units` ranges from `-37` to `49` with median `8.5`.
- `earned_royalty_cents` ranges from `-7712` to `11650` with median `2007.5`.
- `recouped_advance_cents` ranges from `0` to `11650` with median `2007.5`.
- `payable_cents` ranges from `0` to `31759` with median `17784.0`.
- `earned_royalty_cents` is negative on 4 items.
- `payable_cents` is positive on 29 of 30 items.

That spread is useful because not every row is a simple positive-earnings case; some items require handling returns, reversals, or negative quarter earnings correctly.

## Why This Is Not A Near-Duplicate

CRF is closest to Reimbursement Forensics in the broad sense that both are messy finite-evidence audit tasks with exact numeric outputs. But the actual reasoning object is different:

- contract rights scope instead of expense policy;
- later amendment precedence instead of claim-policy exceptions;
- royalty rates, bundle allocation, and discount floors instead of FX and per-diem arithmetic;
- reserve withholding and advance recoupment instead of reimbursement caps.

So the benchmark lives in the same design family but is not the same task in another costume.

## Known Limits

- The documents are synthetic rather than sourced from a live public catalog.
- A very strong solver with careful scripting may still perform well, since the task is fully specified and deterministic by design.
- Most generated items have positive payable because reserve release is often nonzero; future iterations could push more near-zero payable cases if needed.
