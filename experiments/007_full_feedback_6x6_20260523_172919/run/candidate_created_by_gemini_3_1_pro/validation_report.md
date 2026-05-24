# Validation Report

## Solvability and Identifiability Argument
This benchmark is fully externally solvable without guessing or referencing any private generator state.
- All rules for categorization (OpEx vs. CapEx based on a strict `< 500,000` cent threshold, exclusion of late fees/penalties) are explicitly documented in `lease_manual.md`.
- All tenant occupancies are completely specified between the `rent_roll.csv` and the `communications.txt` emails.
- All building layouts are fully defined in `property_data.json`.
- All expense instances are fully listed in `expenses_ledger.csv`.
- All mathematical operations (addition, floor division, caps) are meticulously defined in `lease_manual.md` with an unambiguous order of operations and integer math enforcement.

A human specialist (like a CPA) or a careful agent can trace the exact state of the world on any given day. There is no hidden vocabulary or required external knowledge.

## Evidence for External Verification
For each tenant's final CAM charge (the answer field), an external solver can verify it by producing a transparent audit trail from the public packet:
1. **Occupancy Profile:** Calculate the `Tenant Total Square-Foot-Days` by cross-referencing `property_data.json` for suite sizes and `rent_roll.csv` + `communications.txt` for the start/end days.
2. **Base OpEx Pool:** List all expenses from `expenses_ledger.csv`. Filter them using the explicit definitions in `lease_manual.md` (e.g. keeping routine maintenance, excluding late fees and items exactly >= 500,000 cents). Then apply any explicit reclassifications (OpEx to Direct Charge, or OpEx to CapEx) mentioned in `communications.txt`.
3. **Total Pool:** Apply the 5% property management fee formula (integer division) to the Base OpEx Pool.
4. **Pro-Rata Calculation:** Divide the Total Pool by the building's Total Square-Foot-Days, multiplied by the tenant's Square-Foot-Days.
5. **Caps:** Identify if a cap applies from `communications.txt` and cap the Base Charge accordingly.
6. **Direct Charges:** Add any expenses explicitly noted as Direct Charges for that tenant in `communications.txt`.

By following this mechanical procedure, the answers are perfectly recoverable and verifiable from the public assets. There are no private labels or magic strings.
