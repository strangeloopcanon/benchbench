# Validation report - Consolidation Point v1.0.0

## 0. A disclosure about how this package was validated

The authoring environment for this package had **no working shell**. Every
attempt to run a command, including `echo`, failed before the command was
reached:

```
Error: Failed to start network proxy: proxy startup failed:
  proxy_io_error__Failed_to_bind_UNIX_socket__Operation_not_permitted__os_error_1_
sandbox: policy strict enabled; network access disabled
sandbox-exec: sandbox_apply: Operation not permitted
```

Escalating out of the sandbox was declined, a subagent hit the identical wall,
and no code-execution MCP server was available. So the three CLI commands were
not executed by the author.

What that means in practice, and what was done instead:

- The **item content and every gold answer** were derived by hand and are
  recorded step by step in `audit/gold_derivations.md`. These do not depend on
  code at all; a human auditor can check all thirty in about fifteen minutes
  against `corpus/statute_pack.md`. This is the part of the package that
  matters most, and it is the part least exposed by the missing shell.
- The **shortcut baselines** in section 5 were likewise computed by hand under
  an explicitly stated wrong-but-plausible policy, so they can be re-derived
  and re-checked independently.
- The **three scripts** were written to be as close to unbreakable as possible:
  standard library only, no third-party imports, no clever constructs, no
  filesystem assumptions beyond `os.path`, and each one reviewed line by line
  against its own contract. They are deliberately boring.
- The package was made **self-healing** against the one class of error the
  missing shell really does expose, namely transcription drift between the
  hand-written artefacts. `verifier.py` cross-checks the gold file and the
  solver bundle against the authored corpus, including a byte comparison of
  the asset. If a hand-written line drifted, verification fails loudly rather
  than silently mis-grading. Re-running `generator.py` regenerates the gold
  file and the whole bundle from `corpus/`, which resolves any drift outright.

Sections 2 to 4 below therefore state the expected output of each command and
the reasoning that supports it, rather than a captured transcript. A reviewer
should run the three commands; they are cheap and they are the first thing to
check.

## 1. What the benchmark claims to measure

Time-indexed normative reasoning. Given a base enactment plus a chronological
stack of textual amending instruments - each carrying its own commencement rule
and, separately, its own application rule - reconstruct the operative rule set
for a specified event and apply it to a fact pattern to produce an exact
figure.

The arithmetic is intentionally trivial (three to six operations per item, at
most two percentages). Score variance should come from parameter selection, not
from computation.

## 2. Generation

```
python3 generator.py --sample-count 30 --seed 20260516 --out-dir .
```

Expected: 30 items, and the files

- `gold_private_sample.jsonl` (30 rows of exactly `id` and `answer`)
- `solver_bundle/items_private_sample.jsonl` (30 rows)
- `solver_bundle/assets/statute_pack.md`
- `solver_bundle/solver_packet.md`
- `solver_bundle/README.md`
- `solver_bundle/SOLVER_MANIFEST.json`

Determinism. The item bank is a fixed authored corpus, not a procedural sample.
Selection is `sorted(items, key=id)[:sample_count]`, so it does not consult the
random number generator at all. `--seed` is recorded in the manifest for
provenance and deliberately has no effect on content, which means regeneration
is byte-identical under any seed. Every write goes through one helper that
fixes `encoding="utf-8"` and `newline="\n"`, so output does not vary by
platform.

From-scratch behaviour. `generator.py` reads only `corpus/items.json` and
`corpus/statute_pack.md`, both authored source files, and never reads anything
under `solver_bundle/` or the gold file. Deleting `gold_private_sample.jsonl`
and the whole `solver_bundle/` directory and re-running reproduces both.

## 3. Verification

```
python3 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
```

Expected: `VERIFY: PASS`, preceded by informational notes.

Checks performed:

| check | what it catches |
|---|---|
| gold rows have exactly `id` and `answer` | data contract violation |
| gold answers match `^(0\|[1-9][0-9]*)$` | non-canonical or non-integer gold |
| item rows carry the declared fields | malformed items |
| item rows carry no field in a forbidden list (`answer`, `solution`, `label`, `rationale`, ...) | answer leakage through item schema |
| ids identical, same order, no duplicates | misalignment between the two files |
| every asset reference resolves inside the bundle, no absolute paths, no `..` | broken or escaping asset links |
| no bundle file name matches gold / answer_key / solution / generator / verifier / scorer / validation / failure_modes / audit | a private artefact shipped by mistake |
| no bundle line contains an item id together with that item's gold value | answer leakage through content |
| gold answers match `corpus/items.json` | transcription drift in the gold file |
| solver-visible questions match `corpus/items.json` | transcription drift in the bundle items |
| `solver_bundle/assets/statute_pack.md` is byte-identical to `corpus/statute_pack.md` | transcription drift in the asset |

The last three are what protect this package against the missing shell.

One informational note is expected and is not a failure: several gold values
also occur as standalone numbers somewhere in the bundle, because the statute
itself quotes money amounts. `180` is the clearest case - it is both the
post-2022 powered-berth surcharge and the answer to `sc-016`. That is a
coincidence of a small integer space, not a leak: the value carries no
association with any item id, and the check that would matter, id-and-answer on
the same line, is a hard failure and does not fire.

## 4. Gold self-score

```
python3 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

`predictions.jsonl` at the package root is a copy of the gold answers, so the
expected result is `30/30`, accuracy `1.0`. The report is a JSON object with
`schema_version: 2`, integer `total` (30) and `correct` (30), numeric
`accuracy` computed as `correct / total`, plus diagnostics (`incorrect`,
`missing_predictions`, `missing_ids`, `duplicate_prediction_ids`,
`unknown_prediction_ids`, `per_item`).

This confirms the scoring path end to end: normalisation is idempotent on
canonical integers, so gold compared against itself must be exact.

## 5. Baselines

All three baselines are hand-computed under an explicitly stated policy and
shipped as prediction files so they can be re-scored.

### 5.1 Constant guess - `baselines/predictions_constant_390.jsonl`

Answer `390` to everything. `390` is a modal gold value, appearing twice
(`sc-001`, `sc-020`). Four values tie for modal at two occurrences each - 350,
390, 500 and 670 - so `verifier.py`, which breaks the tie on the lowest value,
reports the same ceiling against `350`.

**Result: 2/30 (6.7%).** This is the ceiling for any constant guess. The 30
items take 26 distinct values spanning 140 to 910, so there is no answer-shape
prior to exploit.

### 5.2 Ignore the amendments - `baselines/predictions_original_law_only.jsonl`

Apply the Act exactly as enacted in 2011 to every case: rate 40, free allowance
2 tonnes, surcharge 150/60, small operator allowance 20%, no night supplement,
no community quay discount, no aggregation, rounding to the nearest 5 with
midway up.

**Result: 2/30 (6.7%)**, correct only on `sc-001` and `sc-024`, which are the
two cases whose landings genuinely predate every amendment.

### 5.3 Apply only the latest law - `baselines/predictions_current_law_only.jsonl`

The more dangerous shortcut, and the one a hasty solver actually takes:
consolidate everything, then apply the 2024 rule set to every case regardless
of date. Rate 62, free allowance 1 tonne, surcharge 180/75, night supplement
120, no small operator allowance, community quay discount for non-corporates,
aggregation on, rounding to the nearest 10 with midway down.

**Result: 6/30 (20%)**, correct on `sc-015`, `sc-016`, `sc-017`, `sc-018`,
`sc-019` and `sc-028` - precisely the six items whose landings fall in the
modern era, where current law happens to be the right law.

### 5.4 Reading of the baselines

The two flattening strategies bracket the naive solution space, and neither
gets past 20%. Beating them requires resolving the timeline per item, which is
the capability the benchmark claims to measure. The 20% figure is also a useful
interpretive floor: a solver scoring near 6/30 has probably consolidated
correctly and then forgotten to apply the result as at the relevant date.

## 6. External solvability and identifiability

**The claim.** A qualified external solver - a statutory-interpretation
specialist, or a model that systematically builds the parameter timeline - can
determine every answer from the public bundle alone.

**Why the items are identifiable.** Each answer is a deterministic function of
the facts, given the pack:

1. Every operative parameter has a value determined by a single date - either
   the landing date or, for rounding, the assessment date. Both dates are
   stated in every item.
2. Every parameter's timeline is fixed by explicit text. Commencement dates are
   stated in the instrument or in the reproduced commencement notice.
   Application provisions name the class of landings or assessments affected.
   There is no gap where a solver has to guess.
3. The composition order does not matter. Section 5 defines the levy as a sum
   of additive and subtractive components, and each component has its own
   independently defined base (the small operator allowance is a percentage of
   the base amount; the community quay discount is a percentage of the base
   amount plus the berth surcharge; the night supplement is a flat sum). So
   there is no operator-precedence ambiguity to resolve.
4. Rounding happens exactly once per levy, on an exact intermediate value, and
   the rule states its own tie-break direction in both versions.

**What evidence a solver uses.** For each item: the landing date fixes the base
rate (Part C instruments C1, C5, C7 with C8, C10), the free allowance (C2 s.2
plus the appointed day in C3), the berth surcharge (C9 s.3, subject to
suspension by C6), the night supplement (C2 s.3 plus C3, then C9 s.4), the
availability of the small operator allowance (C4 ss.2-3), the community quay
discount and its later body-corporate condition (C4 s.4, C11 s.3), and whether
the aggregation rule exists (C11 s.2). The assessment date fixes the rounding
rule (C9 s.2 with s.5). The facts of the case supply everything else.

**Conventions that would otherwise be contestable are pinned in Part A**, which
is deliberately written before the legislative text: completeness of the pack
(A1), the distinction between amending the text and applying the amendment
(A2), the default temporal rule (A3), inclusive date language (A4), the effect
of expiry (A5), the effect of revocation before an effect date (A6), no
intermediate rounding (A7), how to total more than one levy (A8), and
exhaustiveness of the facts (A9). The solver packet then works a full
non-graded example end to end so the arithmetic conventions are demonstrated
rather than merely asserted.

**What difficulty is not.** Nothing here depends on hidden generator state, on
a private key, on an unstated convention, or on an unsolved problem. The
fictional jurisdiction removes recall advantage without removing solvability:
there is no outside source to consult, but there is also nothing outside the
bundle that a solver would need.

**Estimated human performance.** A careful reader who builds the timeline table
before touching the cases should reach the high twenties out of thirty. The
items most likely to catch a careful human are `sc-011` and `sc-027` (the
assessment-date rounding rule) and `sc-029` (aggregation correctly *not*
applying). A reader who works case by case without building the table first
will do considerably worse, which is the intended discrimination.

## 7. Leakage inspection of the solver bundle

Contents of `solver_bundle/`:

```
SOLVER_MANIFEST.json
README.md
solver_packet.md
items_private_sample.jsonl
assets/statute_pack.md
```

- No gold answers. Item rows carry `id`, `case_ref`, `assets`, `question` and
  `answer_format` only.
- No generator, verifier or scorer source; no corpus; no audit trace; no
  validation report; no failure-mode notes; no seeds beyond the provenance
  integer in the manifest, which does not affect content.
- No filename in the bundle matches a private-artefact pattern.
- One near-miss was found and fixed during authoring: the draft solver packet
  illustrated the submission format with `{"id": "sc-001", "answer": "390"}`,
  which happens to be a real item id next to its real gold value. It is now
  `{"id": "sc-000", "answer": "370"}`, using a placeholder id that is not in
  the bank and the answer to the worked example. The verifier's
  id-next-to-its-own-answer check exists to catch exactly this and would have
  failed the package.
- The remaining numeric co-occurrences are the informational note described in
  section 3 and carry no item association.

## 8. Ambiguity audit

Each of the following was a place where a careless drafting choice would have
produced two defensible answers. The resolution is recorded so a reviewer can
confirm the items are well posed rather than merely hard.

| risk | resolution |
|---|---|
| Does a whole-tonne weight round up? | s.7(2) says explicitly that it does not. Six items turn on this. |
| Order of operations between allowance, discount and supplement | Each component has an independently defined base, so the sum is order-invariant. |
| Double rounding of percentages | Rule A7: exact intermediates, one rounding per levy. |
| Midway rounding direction | Both versions of s.11 state their own tie-break. Two items land exactly on a midpoint. |
| Is 22:00 or 05:00 inside the night window? | s.8A says "at or after 22:00 or before 05:00", so 22:00 is in and 05:00 is out. One item on each boundary. |
| Does "did not exceed 50 tonnes" include exactly 50? | Yes, by the words used. Boundary pair `sc-021` / `sc-022`. |
| Is the small operator test on gross or chargeable tonnage? | s.9(3) says gross landed weight, and the facts state the prior-year figure as gross. |
| What happens to the surcharge when the emergency Act expires? | A5 plus C6: the Act suspended the charge for events in the window without amending the text, so s.8 applies again afterwards. |
| Is an order revoked before its effect date still effective? | A6 answers this directly. |
| Under aggregation, is the surcharge charged once or per landing? | s.7A(3) says per constituent landing, and s.7A(5) says one rounding. |
| Which date governs an aggregated landing? | s.7A(4): the earliest constituent landing. |
| How do you total two separate levies? | A8: round each, then add. |
| A fact that is simply not mentioned | A9 makes the facts exhaustive, so an unmentioned condition is not satisfied. |

## 9. Known limitations

- Thirty items is a small sample. The standard error on a 50% score is about 9
  points, so this size supports coarse ranking, not fine distinctions. The
  corpus format supports extension without redesign: the statute pack is fixed
  and each new case is one more entry in `corpus/items.json`.
- The items share one statute pack. That makes the benchmark cheap to audit and
  keeps context length manageable, but it also means a solver that builds the
  timeline once amortises that cost across all thirty items. Scores should be
  read as measuring timeline construction plus per-case application, not
  thirty independent reasoning episodes.
- Difficulty was calibrated against the shortcut baselines and the trap
  inventory, not against a measured model run, because no model could be run
  from the authoring environment. If a strong solver clears 80%, the natural
  next version adds cases where two application provisions of different Acts
  interact on the same item, and cases with an amendment to an amendment.
- The rounding rules make some items sensitive to a single mark of error in the
  intermediate. That is deliberate - it is why the tie-break direction and the
  no-intermediate-rounding rule are stated explicitly - but it does mean a
  solver that gets the law right and slips on one multiplication loses the
  item outright. There is no partial credit.
