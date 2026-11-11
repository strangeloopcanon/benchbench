# AuditWeave solver packet

## Task

Each JSONL row is a self-contained forensic replay case. A four-way disputed
event must be reconstructed from checkpoint audits of a partially ordered log.
After reconstructing the log, run the listed counterfactual operations and
return the requested exact state.

A **reconstruction** consists of:

1. one label (`A`, `B`, `C`, or `D`) for the sole event containing
   `candidates`; and
2. one legal total order for each phase.

Phases run in numeric order. Within a phase, each event runs exactly once.
`before: [[x,y], ...]` means event `x` must run before event `y`; unconstrained
events may run in either order. The selected candidate is the operation of the
disputed event. At the end of every phase, every listed audit must equal its
published `value`. There are no other hidden constraints.

The cases are promised to be **answer-identifiable**: considering every label
and every legal phase order that satisfies all audits, the label and requested
post-query state are the same. Intermediate histories need not be unique.

## State and arithmetic

State is five integer registers `a` through `e` and four bits numbered 0
through 3. Registers are always reduced modulo 97 to the canonical range
0..96. Python-style mathematical modulo is intended, so `-1 mod 97 = 96`.
Bits are 0 or 1.

All fields not described as state are ordinary JSON integers or strings.

## Operation semantics

An operation is applied atomically to the current state.

- `{"op":"add","x":X,"n":N}`: `X := X + N (mod 97)`.
- `{"op":"affine","x":X,"m":M,"n":N}`:
  `X := M*X + N (mod 97)`.
- `{"op":"swap","x":X,"y":Y}`: exchange registers X and Y.
- `{"op":"mix","x":X,"y":Y,"n":N}`: using both old values
  simultaneously, set `X := old_X + old_Y + N` and
  `Y := old_X + 2*old_Y + N`, both modulo 97.
- `{"op":"cas","x":X,"q":Q,"r":R,"yes":Y,"no":N}`: if the
  current canonical value `X mod Q` equals R, set `X := Y mod 97`;
  otherwise set `X := X + N (mod 97)`.
- `{"op":"route","bit":I,"x":X,"y":Y,"n":N}`: if bit I is 1,
  add N to X; if it is 0, add N to Y (mod 97).
- `{"op":"toggle","bit":I}`: replace bit I by `1-bit_I`.
- `{"op":"flip_if","bit":I,"x":X,"q":Q,"r":R}`: toggle bit I
  exactly when the current canonical value `X mod Q` equals R.

After all three phases and their audits have been satisfied, apply every
operation in `query_ops` in listed array order. The query operations do not
participate in audits and do not change which candidate label was selected.

## Audit semantics

Let registers in order be `[a,b,c,d,e]` and bits be `[b0,b1,b2,b3]`.
Audit arithmetic uses the canonical register values present at that checkpoint.

- `linear`: dot product of `weights` with the five registers plus dot product
  of `bit_weights` with the four bits, reduced modulo `mod`.
- `quadratic`: sum `weights[i] * register[i]^2`, plus the same bit dot
  product as above, reduced modulo `mod`.
- `probe`: the named register reduced modulo `mod`.
- `bit_code`: `(1*b0 + 2*b1 + 3*b2 + 4*b3) mod mod`.

For each audit, the computed result must exactly equal `value`.

## Output

Write JSON Lines with exactly two keys per row:

```json
{"id":"aw-001","answer":"C|12,3,44,0,96|1010"}
```

The answer string is `LABEL|a,b,c,d,e|b0b1b2b3`, using canonical decimal
registers, no spaces or leading zeroes, and bits in index order. Produce one
row for every input id. Exact matching is used.

## A direct solving method

No generator knowledge is needed. Enumerate the four labels. For each phase,
enumerate topological orders permitted by `before`, replay them from every
state surviving the prior phase, deduplicate equal states, and retain states
matching all phase audits. Apply `query_ops` to every final survivor. The
identifiability promise says all resulting answer strings are identical.
