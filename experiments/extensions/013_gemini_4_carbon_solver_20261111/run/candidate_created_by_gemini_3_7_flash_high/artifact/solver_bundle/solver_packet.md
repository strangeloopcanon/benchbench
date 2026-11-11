# CloudSLA-Forensics Solver Packet

## Benchmark Overview
CloudSLA-Forensics evaluates an agent's capability to perform forensic financial and technical arbitration on complex enterprise cloud Service Level Agreement (SLA) claims.

For each case, you are provided with:
1. `contract.md`: The governing Master Service Agreement, Availability Target, Tier Credit Schedule, and custom Addenda.
2. `billing_statement.json`: The monthly billing summary with Monthly Recurring Charges (MRC), variable charges, prior issued credits, and maximum credit cap.
3. `architecture_profile.json`: Deployment details (e.g. Multi-AZ vs Single-AZ status).
4. `telemetry/telemetry_events.json`: Telemetry logs of detected incident events.
5. `dossiers/`: Incident support tickets, Root Cause Analysis (RCA) reports, and maintenance window notices.

All rules, notice deadlines, RCA fault allocations, force majeure RTO grace periods, interval deduplications, tier math, and cap deductions are strictly governed by `CONTRACT_FRAMEWORK.md`.

## Task Instructions
For each case in `items_private_sample.jsonl`:
1. Read the contract terms and incident dossiers.
2. Calculate the exact Net Approved Service Credit (in integer USD cents) payable to the customer.
3. Format predictions as a JSON Lines file where each line has `{"id": "<case_id>", "answer": <integer_cents>}`.
