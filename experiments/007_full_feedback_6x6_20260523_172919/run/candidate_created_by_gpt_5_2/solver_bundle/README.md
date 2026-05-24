# SCF Solver Packet

You may use any tools, but **only** files inside this `solver_bundle/` directory.

## Task

For each item in `items_private_sample.jsonl`, read the referenced assets and output a JSON prediction row:

```
{"id": "scf_000", "answer": {"eligible_downtime_minutes": 12, "sla_breached": false, "credit_percent": 0, "credit_usd_cents": 0}}
```

## Rules

The authoritative rules are in `assets/public_policy.md` and the item contract rider.
