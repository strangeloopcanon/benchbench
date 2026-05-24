# Construction Progress Payment Certification (CPPC) — Solver Packet

## Task

You are a construction payment certifier. For each item in `items_private_sample.jsonl`, compute the **Certified Payment Amount in cents** according to the rules in `general_conditions.md`.

## Files

- `general_conditions.md` — The master contract conditions governing all payment computations. Read this CAREFULLY. It defines the exact computation sequence (Article 13) and all rules.
- `items_private_sample.jsonl` — 30 payment application items, one per line as JSON.

## Item Structure

Each item contains:
- `id`: Unique identifier (e.g., "cppc_001")
- `trade`: The construction trade/scope
- `project_name`: Project identifier
- `billing_period`: Human-readable period description
- `period_start_day`, `period_end_day`: Numeric period bounds
- `schedule_of_values`: Array of line items with scheduled values and progress
- `change_orders`: Array of change orders (may be empty)
- `stored_materials`: Array of stored material entries (may be empty)
- `backcharges`: Array of backcharge deductions (may be empty)
- `deficiencies`: Array of deficiency holdbacks (may be empty)
- `liquidated_damages`: Object with LD parameters (may be absent)
- `insurance_lapse`: Object with lapse window (may be absent)
- `cumulative_percent_complete`: Overall project completion percentage
- `previous_payments_cents`: Total of all prior payments in cents
- `tax_rate`: Applicable sales tax rate (decimal, e.g., 0.065 for 6.5%)
- `tax_exempt`: Boolean indicating tax exemption

## Answer Format

For each item, output a JSON line with exactly two fields:
```json
{"id": "cppc_001", "answer": 1234567}
```

Where `answer` is an integer representing the Certified Amount in **cents**. The value may be negative.

## Computation Steps (Summary)

Follow Article 13 of the General Conditions precisely (cumulative method):

1. For each line item: Work Completed to Date = scheduled_value × (current_pct / 100), rounded per line
2. Sum all line completions = Total Work Completed to Date
3. Change order earned per §8.3 status rules = CO Earned to Date
4. Stored Materials Credit per §7.4 (all 3 conditions must be true)
5. Total Completed & Stored = Work Completed + CO Earned + Stored Materials
6. Retention rate per §7.2 (10% if cumulative < 50%, 5% if ≥ 50%)
7. Retention = Total Completed & Stored × rate (rounded)
8. Net Earned to Date = Total Completed & Stored − Retention
9. − Backcharges (sum of all)
10. − Deficiency Holdbacks (sum of all)
11. − Liquidated Damages (per §9.1, check excusable flag!)
12. − Insurance Deduction (per §10.2, prorated on THIS PERIOD's work only)
13. + Sales Tax (per §11.1, on THIS PERIOD's materials only, if not exempt)
14. − Previous Payments (the `previous_payments_cents` value)
15. Result = Current Payment Due (integer cents)

Note on "this period's work" for insurance deduction:
= (Total Work Completed to Date) − (sum of each line's scheduled_value × prev_pct / 100, rounded per line) + CO Earned to Date

Note on "this period's materials" for tax:
= (material line items: current completed − previous completed, per line) + material-flagged CO earned

## Key Edge Cases

- Retention rate depends on `cumulative_percent_complete`, NOT individual line items
- Pending COs bill at 50%, Disputed at 25%, Rejected at $0
- ALL THREE stored material conditions must be true for credit
- Excusable delays mean NO liquidated damages
- Insurance deduction applies only to gross earned (not stored materials)
- Tax applies only to material-flagged items and COs
- Use banker's rounding (round half to even) for all intermediate calculations

## Output File

Write predictions to `predictions.jsonl` with one JSON object per line.
