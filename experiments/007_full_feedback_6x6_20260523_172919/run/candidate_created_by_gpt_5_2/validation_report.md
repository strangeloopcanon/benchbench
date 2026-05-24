# Validation Report: Service Credit Forensics (SCF) v1

This report is written for BenchBench’s “is this fair and externally solvable?” requirement.

## What changed vs. typical clean puzzles

SCF is intentionally **messy but finite**:

- Multiple documents can disagree (status page lag, email estimates, drifted monitoring).
- The public policy specifies a precedence order and a drift correction rule.
- The answer is still deterministic: once evidence is reconciled, the credit is a closed-form calculation.

## External solvability / identifiability argument

For any item `scf_###`, an external solver can determine the gold answer using only the solver bundle because:

1. **All needed rules are public.**
   - Counting/rounding/aggregation rules are in `solver_bundle/assets/public_policy.md`.
   - Any additional caps or exclusions are in that item’s `contract_rider.md`.

2. **All needed evidence is public.**
   - Downtime candidates appear in monitoring logs and/or the internal timeline.
   - Maintenance windows and contract exclusions are explicit UTC ranges.

3. **Conflicts are resolvable with public precedence rules.**
   - If the email thread or status page differs from monitoring/timeline, the policy specifies which to trust.

4. **Each answer field is uniquely identified from public information.**
   - `eligible_downtime_minutes`: computed from the final excluded+merged downtime intervals, rounded per-interval as specified.
   - `sla_breached`: threshold comparison from tier (public) and eligible minutes.
   - `credit_percent`: public tier table + the contract cap percent.
   - `credit_usd_cents`: exact arithmetic from fee and percent (floor division rule is explicit).

### What evidence would a human auditor use?

For a given item:

- Use `internal_timeline.md` (UTC) to get corrected incident starts/ends.
- Use `monitoring_log.txt` (after applying the documented drift) to compute exact downtime boundaries; some items require deriving state from metrics using the contract thresholds.
- Subtract any overlap with `maintenance_windows.md` and `contract_rider.md` exclusions.
- Merge intervals, round each interval up to whole minutes, and sum.
- Apply the tier thresholds and credit table from the policy, then the cap from the contract, then compute cents.

## Reliability checks performed (creator-side)

- Deterministic generation with a fixed seed.
- Verifier ensures item ids match and all referenced assets exist under `solver_bundle/`.
- Scorer is deterministic and robust to JSON-string vs object predictions.

## Leakage audit

The solver bundle contains only:

- Public policy text
- Per-item evidence files (contract rider, maintenance windows, monitoring log, internal timeline, status page, email thread)
- Item index JSONL and manifest

It does not include gold answers, generator/verifier/scorer code, seeds, or private traces.

## Expected failure modes (qualitative)

See `failure_modes.md`.
