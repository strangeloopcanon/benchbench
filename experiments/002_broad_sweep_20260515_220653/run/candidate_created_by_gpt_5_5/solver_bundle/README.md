# Solver Packet: Protocol Archaeology

You are given observed traces from unknown deterministic byte protocols. For
each item, infer the response for the held-out query packet.

Read `items_private_sample.jsonl`. Write predictions as JSONL with exactly:

```json
{"id":"pa-0000","answer":"0123abcd"}
```

The answer must be exactly 8 lowercase hex characters.

You may use local computation, scripts, search, and notes. Do not inspect files
outside this `solver_bundle`; the gold answers, generator, verifier, scorer,
audit traces, hidden seeds, and validation reports are private.

