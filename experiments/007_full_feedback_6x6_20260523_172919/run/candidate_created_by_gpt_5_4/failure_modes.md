# Failure Modes

## Likely solver mistakes

- Applying only the base rider and missing that later amendments override rate, territory, promo, or channel terms.
- Treating promo rows as always excluded or always included, instead of checking for a later promo exception and partial multiplier.
- Using `gross_cents` for bundle rows instead of `bundle_allocated_cents`.
- Forgetting the discount floor on deeply discounted rows, or applying the floor to exempt channels.
- Computing reserve withholding from total earnings rather than only positive physical-row earnings.
- Letting reserve release reduce advance recoupment, even though recoupment is against earned royalties only.
- Dropping negative included rows instead of letting returns and reversals subtract from units and earnings.

## Benchmark risks I tried to avoid

- No private answer labels or scorer-only strings.
- No hidden generator trick is needed; every answer field is evidence-backed from solver-visible documents.
- The task is not an impossible open-research problem; a careful accountant, rights analyst, or tool-enabled model can solve it from the packet.
- The package does not rely on a type mismatch artifact. The scorer accepts integer fields given either as integers or integer strings.
