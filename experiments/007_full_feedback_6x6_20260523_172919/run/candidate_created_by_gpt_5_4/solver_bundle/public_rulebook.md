# Catalog Royalty Forensics (Public Rulebook)

This benchmark asks you to compute a quarter-end royalty statement from public contract documents and public sales evidence.

## Answer fields

Return JSON with exactly these fields:
- `included_units`: integer
- `earned_royalty_cents`: integer
- `recouped_advance_cents`: integer
- `payable_cents`: integer

## 1) Inclusion rules

A sales row contributes only if all of the following are true:
1. `sale_date` falls within the licensed effective window.
2. `territory` is licensed and not carved out.
3. `format` is licensed.
4. `channel` is not excluded by the base rider or a later amendment.
5. `is_promo` is `0` unless a later amendment explicitly says otherwise.

Negative `units` or negative money values represent reversals or returns. If the original row type would have been included, the negative row also counts and subtracts from totals.

## 2) Document precedence

Use the latest applicable rule in this order:
1. Later amendment
2. Base rights rider
3. This public rulebook

The finance memo is authoritative only for opening advance balance and reserve release.

## 3) Recognized base per row

Start from the row's `gross_cents`.

Then apply these public adjustments in order:
1. If `channel = bundle`, use `bundle_allocated_cents` instead of `gross_cents`.
2. If the row is included, check the contractual discount floor. Compute the row's actual unit price as `gross_cents / units` using absolute values. If that unit price is below `discount_floor_pct` of `list_price_cents`, and the channel is not floor-exempt, replace the recognized base with `units * floor(discount_floor_pct * list_price_cents / 100)` while preserving the original sign.
3. If an amendment applies a base multiplier for that row, multiply the recognized base by that percentage and round down toward zero.

## 4) Rate selection

Each format has a base royalty rate in basis points.
An amendment may override the rate for a format, channel, territory set, or date window.
Use the latest applicable override. If multiple filters are listed, all of them must match.

## 5) Row earnings and units

For each included row:
- `included_units` adds the signed `units` value.
- Row royalty earnings are `trunc_toward_zero(recognized_base_cents * rate_bps / 10000)`.

Truncation toward zero means:
- `123.9 -> 123`
- `-123.9 -> -123`

## 6) Reserve withholding

Current-quarter reserve withholding applies only to included physical rows (`paperback` and `hardcover`) whose royalty earnings are positive.
Reserve withheld is `floor(sum(positive physical-row earnings) * reserve_withhold_pct / 100)`.

## 7) Advance recoupment and payable amount

- `earned_royalty_cents` is the sum of all included row earnings.
- `recouped_advance_cents = min(max(earned_royalty_cents, 0), opening_advance_cents)`.
- `payable_cents = max(0, earned_royalty_cents + reserve_release_cents - reserve_withheld_cents - recouped_advance_cents)`.

Reserve release increases payable but does not reduce recoupment.
