# Failure Modes

Expected patterns of solver failure on the CPPC benchmark, organized by the
rule they misinterpret or the implementation mistake they make.

## 1. Retention Threshold (14 items affected)

**Mistake**: Using flat 10% retention for all items instead of checking the
50% cumulative completion threshold.

**Impact**: Items with `cumulative_percent_complete >= 50.0` will have
retention over-deducted by 5% of the total completed and stored value. Typical
error magnitude: $5,000–$25,000.

**Detection**: Predictions systematically lower than gold for items with high
cumulative completion.

## 2. Change Order Status Rates (up to 21 items affected)

**Mistake**: Billing all change orders at 100% of earned value regardless of
status, or using wrong rates (e.g., 50% for disputed instead of 25%).

**Impact**: Items with pending, disputed, or rejected COs will have CO earned
over-stated or under-stated. Typical error: $1,000–$10,000.

**Detection**: Items with pending/disputed COs will be over-predicted if solver
uses 100% for all.

## 3. Stored Materials Triple Condition (11 items affected)

**Mistake**: Giving credit for all stored materials regardless of whether all
three conditions (documentation, protection, insurance) are met.

**Impact**: Items with stored materials that fail one or more conditions will
be over-predicted. Typical error: $2,000–$30,000.

**Detection**: Systematic over-prediction on items with stored materials where
some entries have `false` for one or more condition fields.

## 4. Per-Line Rounding vs Aggregate (all 30 items affected)

**Mistake**: Computing `sum(val * pct) / 100` as a single operation instead of
rounding each line item's completed value independently before summing.

**Impact**: Small rounding errors (typically 0–5 cents) that accumulate
differently with more line items. Usually not enough to cause failure alone,
but can combine with other small errors.

**Detection**: Off-by-one or off-by-few-cents errors with no pattern.

## 5. Insurance Deduction Scope (5 items affected)

**Mistake**: Applying the insurance deduction to the entire subtotal (including
stored materials) instead of only to "this period's work earned."

**Impact**: Over-deduction of the insurance amount. Typical error: $500–$5,000.

**Detection**: Under-prediction on items with both insurance lapse and
significant stored materials.

## 6. Excusable Delay LD Waiver (4 items affected)

**Mistake**: Applying liquidated damages even when `is_excusable` is true.

**Impact**: False deduction of LD amount (could be $1,000–$10,000+).

**Detection**: Under-prediction on items with excusable delays.

## 7. Tax Scope (material-only) (16+ items affected)

**Mistake**: Applying sales tax to ALL earned value instead of only
material-flagged line items and material-flagged change orders.

**Impact**: Over-statement of tax, leading to over-prediction. Typical error:
$500–$5,000.

**Detection**: Systematic over-prediction that correlates with tax rate × total
earned vs tax rate × materials earned.

## 8. Tax Exemption (5 items affected)

**Mistake**: Applying tax even when `tax_exempt` is true.

**Impact**: False addition of tax amount. Typical error: $500–$3,000.

**Detection**: Over-prediction on tax-exempt items.

## 9. Cumulative vs Incremental Method

**Mistake**: Using an incremental computation (earned this period only) rather
than the cumulative method (total completed to date, then subtract previous
payments). With correct previous payments this yields the same result, but
errors in intermediate rounding differ.

**Impact**: Small systematic rounding differences on all items.

**Detection**: Most items off by 1–10 cents.

## 10. Insurance Overlap Calculation

**Mistake**: Using exclusive endpoints instead of inclusive (off-by-one in day
counting), or not correctly handling lapses that extend before/after the period.

**Impact**: Wrong proration fraction for insurance deduction.

**Detection**: Incorrect insurance deduction on items where the lapse partially
overlaps the period boundaries.

## Interaction Effects

The most common failure pattern for strong solvers is a combination of 2–3
minor mistakes that individually might not cause many failures but together
reduce accuracy significantly. For example:

- Wrong retention (mistake 1) + wrong CO rates (mistake 2) together affect
  items that have BOTH high cumulative % AND non-approved COs.
- The "almost correct" baseline shows that fixing everything except retention
  still loses 14/30 items.

## Expected Score Distribution

Based on baseline analysis:
- **Solver that implements all rules correctly from the spec**: 27–30/30
  (may lose 1–3 due to subtle rounding or off-by-one in overlap)
- **Solver that misses one major rule**: 14–20/30
- **Solver that misses 2+ rules**: 6–14/30
- **Solver that uses heuristics without implementing the algorithm**: 0–6/30
