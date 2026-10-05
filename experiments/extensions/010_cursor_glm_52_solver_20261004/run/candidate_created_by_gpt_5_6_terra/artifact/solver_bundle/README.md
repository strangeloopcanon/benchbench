# CFPS solver packet

## Counterfactual Firewall Policy Synthesis v1

Each line of `items_private_sample.jsonl` is one independent policy-synthesis
instance.  Submit exactly one JSON line per item with its `id` and `answer`.

For an instance, choose a set `R` of permission names to revoke.  A permission
not in `R` is active.

- A recipe is a list of permissions.  It is **active** iff every listed
  permission is active (equivalently, none of its names is in `R`).
- A channel is **open** iff at least one of its recipes is active.
- A service is **operational** iff every one of its channels is open.
- An attack **succeeds** iff every one of its channels is open.  It is
  **blocked** iff at least one of its channels is not open.

A valid policy leaves every listed service operational and blocks every listed
attack.  Its primary objective is to minimize the sum of `revoke_cost` for all
permissions in `R`.  Break equal-cost ties by fewer revoked permissions, then
by the lexicographically smallest increasing tuple of permission names.  Names
are compared as ordinary strings (`p02` precedes `p10`).

The answer is that final increasing tuple as comma-separated names with no
spaces, e.g. `p03,p11,p14`.  If the tuple is empty, write `NONE`.

All information needed to solve an instance is in this packet.  A practical
method is to encode the rules as Boolean constraints or enumerate the 2^18
candidate revocation masks with cost-based pruning.
