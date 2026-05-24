# Failure Modes: Service Credit Forensics (SCF) v1

- **Ignoring precedence rules**: treating status page or email estimates as authoritative instead of the internal timeline / corrected monitoring.
- **Forgetting drift correction**: using monitoring timestamps without applying the provided `clock_drift_seconds`.
- **Not deriving state from metrics**: treating metric lines as informational only, instead of converting them to OK/DEGRADED/SEVERE_DEGRADED/UNAVAILABLE per the public policy and contract thresholds.
- **Wrong rounding**: rounding total minutes at the end instead of rounding up per remaining interval.
- **Not subtracting exclusions**: forgetting maintenance windows or contract-specific exclusion ranges.
- **Scope confusion**: treating `single` as `multi` or vice versa; missing that `single` limits to the primary region.
- **Confusing DEGRADED vs SEVERE_DEGRADED**: counting non-severe degraded time as downtime.
- **Percent/cents arithmetic**: not applying cap percent; not flooring cents correctly.
