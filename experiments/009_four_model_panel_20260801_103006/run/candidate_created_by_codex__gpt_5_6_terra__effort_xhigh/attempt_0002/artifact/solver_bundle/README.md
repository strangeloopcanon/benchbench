# Patchwork Access Logic (PAL)

Each line of `items_private_sample.jsonl` is one independent policy-delta
problem. For every item, return one JSON object with exactly `id` and `answer`.
No explanation is scored. The answer must concatenate its ten query outcomes in
the displayed query order, with no spaces:

```
q00=D@DEFAULT>D@DEFAULT;q01=A@R07>D@R07;...;q09=A@R12>A@R12
```

For each query, the left side is the decision/source for `base_policy`; the
right side is the decision/source after applying every `patches` entry in array
order. `A` means allow and `D` means deny. `DEFAULT` is the source if no rule
matches. A source is always the winning rule's `id`, even if the decision stays
the same after a patch.

## Public semantics

All integer time intervals are closed: `start <= query.time <= end`. A record
is usable only when `active` is true, its interval contains the query time, and
its `devices` includes either the query device or `"*"`.

### Effective membership

A principal directly belongs to every usable `memberships` record with that
principal. A usable `links` record means membership in `child` also gives
membership in `parent`. Repeat this implication transitively until no new
groups are reached. (The supplied link graph is acyclic.) A rule with
`subject_type: "P"` matches only its named principal; one with `"G"` matches
when the query principal is effectively a member of its named group under that
query's time and device.

### Rule matching

A rule matches a query exactly when all of these hold:

1. The rule itself is usable at the query time/device.
2. Its `action` equals the query action, or is `"*"`.
3. Its subject matches by the membership rule above.
4. `scope_mode: "SELF"` requires the query resource to equal `scope`.
   `scope_mode: "TREE"` permits the scope resource itself and every descendant
   of it in the `resources` parent tree.
5. Every `all_tags` tag occurs on the query resource; if `any_tags` is nonempty,
   at least one of its tags occurs; none of `forbid_tags` occurs.

Tags live only on the queried resource—ancestor tags are not inherited. An
empty `all_tags`, `any_tags`, or `forbid_tags` imposes no condition of that
kind.

### Winner and decision

Among all matching rules, select the maximum tuple:

```
(priority, depth(scope), position_in_rules_array)
```

where root `O00` has depth 0 and children have depth one more than their
parent. Thus larger priority wins; ties go to the deeper scope; remaining ties
go to the rule appearing later in `rules`. The winner produces `A` for effect
`ALLOW` and `D` for effect `DENY`. If nothing matches, the result is
`D@DEFAULT`.

### Patches

Start from a deep copy of `base_policy`, then apply `patches` in listed order.
`rule_field`, `membership_field`, and `link_field` replace the named field on
the object with that `target` id. A `tag` patch adds its tag if `present` is
true and absent, or removes all occurrences if `present` is false. No other
field changes. Then evaluate the same queries against that patched policy.

The policy itself is the complete evidence: no external facts or customary
access-control conventions apply.
