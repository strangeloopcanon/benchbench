# Counterfeit Clock — Solver Packet

For every item, recover the one altered node-log timestamp.

## Public system rules

Each item is independent. It contains five local `nodes`, five
`manifest_nodes`, a prime `modulus`, five distinct `allowed_rates`, a trusted
global `manifests` ledger, and untrusted node `logs`.

For node `n`, there is an unknown rate `r_n` and offset `b_n`. The five nodes
use the five allowed rates bijectively: no two nodes use the same rate. Offsets
are arbitrary integers modulo `modulus`. At true integer time `t`, the node's
displayed counter is exactly

    tick_n(t) = (r_n * t + b_n) mod modulus.

The manifest station names and local node names are two different naming
systems. There is an unknown bijection between the five `nodes` and the five
`manifest_nodes`; a local record's `peer` is also a local node name. Every
manifest is one real packet and gives its trusted manifest-name source,
destination, global send time, and global receive time.

Every packet alias in the logs is also one real packet. Packet aliases and
manifest IDs are different naming systems. After applying the unknown station
bijection, within each ordered `(source, destination)` route there is an
unknown bijection between packet aliases and manifests. An alias's `send` and
`receive` records belong to the same packet.

The records for each node appear in chronological order within that node's
contiguous block in `logs`. Record order is correct even across counter wraps.
The manifest, endpoints, packet aliases, kinds, peers, record IDs, and order
are all correct. Across the entire item, exactly one `tick` value was replaced
by a different residue. All other ticks obey the clock equation.

## Required answer

Return one JSONL row per item, with exactly these outer keys:

    {"id":"CC-001","answer":{"record_id":"A-01","corrected_tick":42}}

`record_id` is the altered record. `corrected_tick` is its counter value before
alteration, an integer in `[0, modulus)`. Include every item exactly once.

## Auditable solving route

A complete finite search is practical. Enumerate the 5! station-name
bijections, rejecting those whose directed route multiplicities disagree. For
each surviving node/rate pairing, propose offsets from equations pairing a log
record with a compatible manifest event. Reject clock hypotheses that cannot
match all but at most one local tick multiset. Keep only five-node hypotheses
with distinct rates. For each route, enumerate the small within-route
alias/manifest permutations and retain explanations with exactly one unequal
tick overall. The supplied instances were accepted only when all valid
explanations give one identical `(record_id, corrected_tick)` answer.
