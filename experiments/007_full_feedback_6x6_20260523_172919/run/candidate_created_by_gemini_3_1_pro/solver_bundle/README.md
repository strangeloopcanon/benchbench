# Commercial Lease CAM Reconciliation

You are an automated accounting auditor. Your task is to calculate the final Commercial Area Maintenance (CAM) charges for a specific set of tenants in a commercial building for the year 2025.

## Data Provided
In each item's folder, you will find:
- `lease_manual.md`: The base rules for calculating CAM charges.
- `property_data.json`: The total square footage of the building and the square footage of each suite.
- `rent_roll.csv`: The initial record of when tenants occupied specific suites.
- `expenses_ledger.csv`: A list of all expenses incurred by the property throughout the year.
- `communications.txt`: Emails between property managers and accounting that may override or amend the base rules (e.g., reclassifying expenses, noting direct charges, or recording tenant expansions/CAM caps).

## Task
For each item in `items_private_sample.jsonl`, read all the documents in the item's folder. Follow the mathematical rules strictly, apply any email overrides, and compute the final CAM charge (in cents) for **each tenant listed in the initial rent roll** of that item.

## Output Format
Your output must be a JSONL file with one JSON object per line.
Each object must have the following structure:
```json
{"id": "item_000", "answer": {"Tenant A": 12345, "Tenant B": 67890}}
```
- `id` corresponds to the item ID from `items_private_sample.jsonl`.
- `answer` is a single dictionary mapping the EXACT tenant string (e.g. "Tenant A") to their final CAM charge as an INTEGER (in cents).
- You must output an entry for every tenant that appears in the `rent_roll.csv` for that item, even if their final charge is 0.
