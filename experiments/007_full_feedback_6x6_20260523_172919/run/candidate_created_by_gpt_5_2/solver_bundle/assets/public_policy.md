# NimbusCloud Service Credit Policy (Public)

This policy defines how to compute eligible downtime and service credits.

## 1) What counts as downtime

A downtime interval is any contiguous period where the service is either:
- **UNAVAILABLE** (requests fail), or
- **SEVERE_DEGRADED** (p95 latency exceeds the contract threshold).

Periods that are only **DEGRADED** (but not severe) do *not* count.

### Deriving state from monitoring evidence

Monitoring logs may contain either explicit `STATE` records or `METRIC` records.
If explicit `STATE` records exist, you may use them.
If you only have metrics, derive state per region using the contract rider parameters:
- `unavailable_error_rate_pct`: if `error_rate_pct >= unavailable_error_rate_pct`, state is UNAVAILABLE.
- `severe_p95_ms`: if `p95_ms >= severe_p95_ms` AND `error_rate_pct >= 10`, state is SEVERE_DEGRADED.
- Else if `p95_ms >= severe_p95_ms/2`, state is DEGRADED.
- Else state is OK.

## 2) Evidence precedence

Use the following precedence if sources disagree:
1. Internal incident timeline **when it provides explicit start/end timestamps** (and includes a correction note)
2. Monitoring log events (after applying clock drift correction)
3. Status page updates
4. Customer email thread

If the internal timeline is missing an explicit boundary (for example it says "use monitoring for exact end"),
then the monitoring log defines the missing boundary.

## 3) Clock drift correction (monitoring logs)

Monitoring logs may have a consistent clock drift. If a drift value is provided
in the item, *shift every monitoring timestamp by that drift* before using it.

## 4) Exclusions

Exclude time that falls within any of:
- Published maintenance windows (global policy asset for the item)
- Contract rider exclusions (customer-specific)

Exclusions subtract from downtime even if the service was unavailable.

## 5) Aggregation and rounding

Compute downtime as a set of UTC intervals. After applying exclusions:
- Merge overlapping/adjacent downtime intervals.
- Round **each remaining interval up to whole minutes**.
- Sum those rounded minutes to get `eligible_downtime_minutes`.

## 6) Multi-region scope

If the contract scope is `multi`, downtime is the union across regions.
If the scope is `single`, use only the named region in the contract.

## 7) SLA breach and credit table

SLA breach is `eligible_downtime_minutes` >= the tier threshold:
- STANDARD: 40 minutes
- BUSINESS: 20 minutes
- ENTERPRISE: 10 minutes

Credit percent is determined from eligible minutes (take the highest matching tier band):
- STANDARD: >=40 => 10%, >=80 => 25%, >=160 => 50%
- BUSINESS: >=20 => 10%, >=40 => 25%, >=80 => 50%
- ENTERPRISE: >=10 => 10%, >=20 => 25%, >=40 => 50%

Apply the customer contract cap: `credit_percent = min(credit_percent, cap_percent)`.

## 8) Credit calculation

`credit_usd_cents = floor(monthly_fee_cents * credit_percent / 100)`.
