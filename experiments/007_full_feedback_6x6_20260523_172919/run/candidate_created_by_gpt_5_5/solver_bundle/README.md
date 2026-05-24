# Prior Authorization Forensics (PAF) v1 Solver Packet

You are given 30 fictional health-insurance claim dossiers. For each id in
`items_private_sample.jsonl`, open the referenced Markdown dossier under
`dossiers/` and adjudicate the single claim line.

Return one JSONL prediction row per item:

```json
{"id":"PAF-001","answer":{"status":"approved","reason_code":"OK","allowed_cents":12345,"insurer_pays_cents":10000,"patient_owes_cents":2345}}
```

Allowed reason codes are `OK`, `NO_AUTH`, `NO_REF`, `OON`, `NOT_COVERED`, and
`DATE`. If the claim is denied, the benchmark convention is zero allowed,
zero insurer payment, and zero patient responsibility. Cents are integer cents,
with no dollar signs or commas.

The dossiers intentionally include only excerpts needed for each claim. The
task is to reconcile plan type, service schedule, riders, network status,
authorization/referral correspondence, document dates, and accumulators.
