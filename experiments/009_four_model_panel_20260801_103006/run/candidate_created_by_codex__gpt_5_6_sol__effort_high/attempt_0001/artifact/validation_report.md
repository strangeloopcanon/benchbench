# Validation report

## Outcome

The canonical 30-item sample was generated with seed `20260516`. All 30 items
pass structural validation, admit exactly one public-constraint answer, and
agree with the private gold. Gold self-scoring is 30/30. The documented weak
shortcut scores 0/30.

Canonical sample SHA-256 digests:

- public items: `7c9529631dd017984143b8ffa306a5631651b03fcac0aa88aee6bfe070d90112`
- private gold: `376374216f9ac89b6272e598a420cac8e576e9c4f9638ca6cf9d0acef021c9e3`

Every item contains 19 manifests and 38 log records. Generation accepted all
30 canonical instances on the first candidate attempt; acceptance still
depends on the exhaustive identifiability check rather than that empirical
rate.

## Checks performed

1. Generated 30 items using the required count and seed.
2. Parsed every JSONL row and enforced exact public and gold schemas.
3. Checked unique IDs, packet endpoint consistency, send-before-receive global
   timing, residue ranges, and packet/manifest cardinality.
4. Independently enumerated all station mappings that preserve directed route
   multiplicities, all locally viable rate/offset assignments, all distinct
   rate allocations, and all within-route packet permutations with exactly
   one tick mismatch.
5. Required the set of resulting `(record_id, corrected_tick)` pairs to be a
   singleton and checked it against gold for each item.
6. Used the gold file itself as schema-compatible predictions: exact 30/30.
7. Ran `baseline.py`, which blames the second endpoint of the largest raw
   adjacent tick jump and copies the prior tick as its repair: exact 0/30,
   record-ID 1/30, corrected-tick 0/30.
8. Inspected the isolated bundle by filename, manifest allowlist, and text
   search. It contains only `SOLVER_MANIFEST.json`, `solver_packet.md`, and the
   public item JSONL. Matches for words such as “answer” and “corrected” occur
   only in format/rule instructions. No seed, gold row, answer key, clock
   assignment, station mapping, corruption label, generator, verifier, scorer,
   audit trace, or private code is present.

The creation shell could not load the mandated `<local-home>/.../python3.12`
dynamic library because that external path was denied by its sandbox. The same
three workflows were therefore executed with host Python 3.9.6. This is not a
language fallback in the package: all code is standard-library-only, compiles
under 3.9, and uses no behavior removed or changed in Python 3.12. As an
additional cross-version check, generation and verification were rerun under
Python 3.14.6 and produced the identical two canonical SHA-256 digests. The
exact Python 3.12 commands remain the declared execution interface.

## Solvability and identifiability

An external solver does not need generator internals. The public packet states
the complete clock equation, rate bijection, station-name bijection, packet
bijection scope, trusted fields, and exactly-one-corruption promise. The item
itself supplies both naming alphabets, every allowed rate, modulus, global send
and receive times, all packet endpoints and aliases, all observed ticks, and
the node-local chronological order.

Concrete evidence is available for every latent choice. Directed route counts
constrain station identities. Compatible manifest/log event pairs imply finite
offset candidates via `b = tick - r*t (mod modulus)`. Clean records repeatedly
support the correct clock hypothesis. The two endpoints of each packet jointly
test its within-route manifest match. Once these constraints agree on 37
records, the remaining disagreement both identifies the bad public record and
computes its corrected residue directly from the clock equation. The solver
packet gives this finite-search strategy without exposing an answer.

The reference enumerator is complete for the stated rules: any valid solution
must preserve route multiplicities; its offset appears in at least one clean
compatible event equation; its local multiset mismatch lower bound is at most
one; its rates are distinct; and its packet assignment is one of the explicitly
enumerated within-route permutations. Thus the singleton result is an
identifiability certificate, not merely a replay of hidden construction state.

## Reliability and interpretation

Scoring is exact JSON equality after schema checking, with no LLM judge and no
floating-point tolerance. Component metrics help distinguish localization from
repair but do not replace the primary exact score. The canonical data and gold
are deterministic. Items share a rule family, so a solver can amortize a sound
algorithm across them; failures should primarily reflect joint reasoning,
implementation correctness, or tool-use reliability.

No multi-model difficulty sweep was available during creation. The 0/30 weak
baseline demonstrates resistance to the most obvious raw-counter shortcut, not
a calibrated frontier-model score. This is explicitly a remaining empirical
validation need rather than evidence that the benchmark is necessarily at the
ideal frontier difficulty.
