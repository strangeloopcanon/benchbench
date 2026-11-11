# ReiFor Policy Excerpt (Public)

This excerpt is the full policy used for these benchmark items.

## Currency + rounding

- Base currency is USD.
- When converting a receipt amount from currency X to USD, use the exchange rate
  from `common/exchange_rates.csv` for the **receipt date** (YYYY-MM-DD).
- Convert as: `usd = round_half_up(amount * rate, 2)` and then to cents.
- `round_half_up` means 0.005 rounds up (e.g., 1.005 -> 1.01).

## Receipt validity

A receipt line is **invalid** (non-reimbursable) if any of the following apply:

- Missing a required field: date, currency code, amount, category.
- The receipt is marked `VOID`, `CANCELLED`, or `DUPLICATE`.
- The receipt appears twice (same merchant + date + currency + amount). Only the first occurrence is eligible.

Exception: if an email contains an explicit approval line of the form:
`APPROVE RECEIPT <receipt_id> [FULL|PARTIAL <usd_cents>]`
then that receipt is reimbursable as approved even if it would otherwise be invalid, and approved receipts are added directly to the case total without category or per-day caps.

Limits on approvals:
- A FULL approval cannot reimburse a receipt if its **date, currency, or amount**
  fields are missing (because conversion becomes undefined from public evidence).
- A FULL approval cannot override `VOID` or `CANCELLED` (whereas a `PARTIAL <usd_cents>` approval reimburses the explicit `<usd_cents>` amount directly).

## Categories and caps (per receipt)

Eligible categories and caps (post-conversion to USD, for non-approved receipts):

- LODGING: cap $260.00 per night. Receipt must indicate number of nights.
  - If `nights=N` is present, cap applies per night: cap = 260.00 * N.
  - If nights is missing, the receipt is invalid unless explicitly approved by email.
- GROUND: cap $90.00 per day (sum of all non-approved GROUND receipts on the same date).
- MEALS: cap $75.00 per day (sum of all non-approved MEALS receipts on the same date).
- AIR: no cap, but receipt must not be VOID/CANCELLED/DUPLICATE.
- MISC: cap $40.00 per receipt.

## Tips

If a receipt includes a `tip=` field, `amount=` is the pre-tip base amount; convert `amount` and `tip` to USD cents separately (`base_cents = round_half_up(amount * rate, 2) * 100`, `tip_cents = round_half_up(tip * rate, 2) * 100`).
Tips are reimbursable up to **20%** of `base_cents` (`max_tip_cents = round_half_up(base_cents / 100 * 0.20, 2) * 100`).
Anything above 20% is non-reimbursable unless explicitly approved by email (`[FULL]` reimburses `base_cents + tip_cents`).

## Day definition

All per-day caps use the receipt's local date as written on the receipt line.
