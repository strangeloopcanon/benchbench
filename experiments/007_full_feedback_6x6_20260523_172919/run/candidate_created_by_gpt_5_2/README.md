# Service Credit Forensics (SCF) v1

SCF is a BenchBench benchmark about **cross-document incident accounting**.
Each item is a self-contained “mini audit” of a cloud incident.

You get:

- A public SLA policy (what counts as downtime; how to aggregate; rounding).
- A customer contract rider (monthly fee, service tier, custom exclusions/caps).
- Messy evidence: monitoring logs, an internal incident timeline, status-page
  updates, and an email thread.

You must compute an exact answer JSON with:

- `eligible_downtime_minutes` (integer)
- `sla_breached` (boolean)
- `credit_percent` (integer)
- `credit_usd_cents` (integer)

The challenge is **not** a single clean algorithm. It’s careful evidence
reconciliation: timezones, clock drift corrections, overlapping windows,
exclusions, and tier-specific rules.

## How it’s graded

Grading is deterministic. The scorer parses your prediction as JSON (or a JSON
string) and checks each required field. A row is correct only if all fields
match the gold values exactly.

## Run the full contract (creator-side)

From this directory:

1) Generate the sample set:

`/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .`

2) Verify consistency:

`/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl`

3) Score predictions:

`/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json`

## Solver-side

Use only the `solver_bundle/` directory. The solver packet fully specifies the
rules and includes all evidence needed to solve each item.
