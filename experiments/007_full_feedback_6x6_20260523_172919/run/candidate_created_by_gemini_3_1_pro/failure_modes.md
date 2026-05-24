# Failure Modes

This benchmark is designed to defeat both pure-LLM zero-shot solvers and pure-scripting heuristic solvers.

## Pure LLM Solvers
An LLM attempting to solve this zero-shot by just reading all files in context will almost certainly fail because:
- The arithmetic involves tracking 15-25 separate expenses, summing them accurately, and then performing long division and multiplication with large numbers (often in the billions of square-foot-days).
- They routinely drop or hallucinate terms when adding large tables of numbers in text.

## Heuristic / Scripting Solvers
An agent that writes a Python script to parse the CSVs and JSON will likely fail because:
- **Unstructured Overrides:** Emails casually override the base rules (e.g., reclassifying a specific OpEx as a CapEx or a Direct Charge). The phrasing of these emails is randomly varied, so a simple regex like `re.search(r"Direct Charge to (Tenant [A-Z])", text)` might fail on variations like "Accounting, ensure that Tenant C pays the full 15000 cents... It's not a shared expense."
- **Edge Case Thresholds:** The rule for CapEx is `>= 500000`. The generator occasionally injects an expense of exactly `500000` cents. Solvers that script `amount > 500000` will incorrectly include this in the OpEx pool.
- **Categorization Traps:** The rules explicitly exclude late fees and penalties. The expense ledger includes items like "Property tax late fee". If the script blindly accepts all expenses under 500k without checking the textual description against the exclusion rules, it will fail.
- **Temporal Complexity:** Tenants can expand mid-year. A simple script might just take the start/end dates from the CSV and ignore the emails that say a tenant took over an additional suite on Day 150.
