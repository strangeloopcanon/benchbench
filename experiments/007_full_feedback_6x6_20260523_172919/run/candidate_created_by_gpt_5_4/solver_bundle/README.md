# Catalog Royalty Forensics (CRF) v1 Solver Packet

This bundle is sufficient for an external solver.

For each item, read:
- `public_rulebook.md`
- the item's `rights_rider.md`
- the item's `amendments.md`
- the item's `finance_memo.md`
- the item's `sales_statement.csv`

Then produce one JSON answer object per item with exactly these keys:
- `included_units`
- `earned_royalty_cents`
- `recouped_advance_cents`
- `payable_cents`

No hidden labels are required. Every answer field is determined by public rows and public rules.
