# Failure modes - Consolidation Point

Three sections: ways the benchmark itself could be wrong, ways a solver is
expected to fail, and ways the package could break operationally.

---

## A. Threats to the validity of the benchmark

### A1. A gold answer is simply wrong

**The main risk in this package.** The gold answers were derived by hand
because the authoring environment had no working shell (see section 0 of
`validation_report.md`). Hand derivation is exactly as reliable as the person
doing it.

Mitigations actually in place:

- Every answer has a written derivation in `audit/gold_derivations.md` that
  names the governing instrument for each parameter and shows the arithmetic.
  An auditor can re-check all thirty against the pack without re-deriving
  anything from scratch.
- The arithmetic per item is three to six operations on small integers, with at
  most two percentage steps, chosen so that manual derivation is reliable.
- Parameter values were chosen so that near-miss readings give visibly
  different totals rather than coincidentally equal ones. `sc-017` is the clear
  example: aggregating gives 790, computing separately gives 730.
- `verifier.py` cross-checks the gold file against `corpus/items.json`, so a
  transcription slip between the two fails loudly. It cannot, of course, detect
  an error that was made once in the corpus itself.

Residual risk: real. If an auditor finds a disagreement, the derivation trace
identifies which parameter is in dispute in one step, and the fix is a
one-line edit to `corpus/items.json` followed by regeneration.

### A2. An item admits two defensible answers

Ambiguity is the classic way a statutory benchmark rots. The specific risks
identified during authoring, and how each was closed, are tabulated in section
8 of `validation_report.md`: whole-tonne rounding, operator precedence, double
rounding, midway direction, inclusive time boundaries, threshold inclusivity,
gross versus chargeable tonnage, revival after expiry, revocation before
effect, per-landing versus per-aggregate charging, and the treatment of facts
that are not mentioned.

The general defence is that Part A of the pack states the interpretive
conventions *before* any legislative text, and the solver packet demonstrates
them on a fully worked non-graded example. If a reviewer nonetheless finds a
second defensible reading, that item is broken and should be repaired in
`corpus/` rather than defended.

### A3. The benchmark measures reading stamina rather than reasoning

The pack is roughly 350 lines. That is long enough to require organised
extraction but short enough that no solver fails purely on context length. The
countermeasure is that the pack is *shared* across all thirty items, so the
cost of reading it is paid once and the per-item score reflects application
rather than retrieval. The trade-off is noted as a limitation in section 9 of
`validation_report.md`.

### A4. Leakage or contamination

Structurally very low. The jurisdiction, the Act, all eleven instruments, every
operator, harbour and case are invented for this benchmark and appear nowhere
else. There is no real statute to retrieve, and memorising real harbour law is
worth nothing. The residual channel is the package itself leaking into a
training corpus, which would be visible as an implausible jump in scores with
no corresponding change in reasoning traces.

### A5. Shortcut solvable

Tested and rejected. Constant guessing caps at 2/30. Applying only the original
law scores 2/30. Applying only the fully consolidated modern law scores 6/30.
There is no answer-shape prior: 26 distinct values across 30 items, spanning
140 to 910, all multiples of 5 (which is a property of the rounding rules, not
a hint).

One shortcut is genuinely available and is worth flagging: a solver could
notice that the majority of items are unremarkable and only a handful turn on a
trap, then guess that the plain reading is right. That strategy scores about
what the current-law baseline scores, because the traps are distributed across
eras rather than concentrated in the modern one.

### A6. The traps are gotchas rather than skill

Every trap in this package is a real feature of how legislation works and how
practitioners are trained to read it: delayed application, unexercised
commencement powers, savings with sunset clauses, revocation before effect,
sunset of temporary measures, and application provisions keyed to the
assessment rather than to the taxable event. None of them depends on a
peculiar turn of phrase or a hidden negation. The trap inventory at the end of
`audit/gold_derivations.md` maps each one to the items that exercise it, so a
reviewer can judge this directly.

### A7. Small sample

Thirty items gives a standard error of roughly 9 points at mid-range. Adequate
for pass/fail difficulty gating and coarse ranking; not adequate for
distinguishing two solvers a few points apart. Extension is cheap: the statute
pack is fixed and each new case is one entry in `corpus/items.json`.

---

## B. Expected solver failure modes

Ordered roughly by how likely they seem.

1. **Consolidate and forget the date.** Build a correct modern picture of the
   Act and apply it to every case. Scores about 6/30. The single most likely
   failure.
2. **Conflate commencement with application.** Treat the 2014 Act's
   commencement on 1 July 2014 as the date from which both of its amendments
   apply, missing that the allowance change applies only from 1 January 2015
   (`sc-002`).
3. **Apply an uncommenced provision.** Read the cold-chain rebate in the 2016
   Act as law and deduct 200 marks, without checking that the commencement
   notice appointed a day only for two of the three sections (`sc-004`).
4. **Use the landing date for the rounding rule.** The 2022 Act keys its
   rounding change to the assessment date, whenever the landing occurred. Both
   `sc-011` and `sc-027` punish the landing-date reading, and `sc-027` does so
   across a nine-year gap.
5. **Round to the nearest 5 out of habit, or break ties the wrong way.**
   `sc-011` and `sc-012` sit exactly on a midpoint under the post-2022 rule,
   which rounds *down*.
6. **Apply a revoked order.** Use 58 marks for a landing in 2022, missing that
   the order was revoked eleven days before the date from which it was to have
   effect (`sc-008`, `sc-014`).
7. **Miss the savings provision, or over-apply it.** Symmetric traps: `sc-007`
   needs the saving, `sc-006` must not have it (wrong licence class), and
   `sc-008` must not have it (the saving has sunsetted).
8. **Forget the emergency suspension, or extend it past expiry.** `sc-008`,
   `sc-009` and `sc-030` are inside the window; `sc-010` is sixteen days after
   it and the surcharge is back.
9. **Round a whole-tonne weight up.** Reading "rounded up to the next whole
   tonne" as always increasing, despite s.7(2). Costs six items.
10. **Aggregate when the rule does not yet exist, or fail to aggregate when it
    does.** `sc-029` predates the anti-avoidance Act and must be computed as
    two separately rounded levies; `sc-017` and `sc-028` must be aggregated,
    with the surcharge and night supplement still charged per constituent
    landing.
11. **Get the boundary of the night window wrong.** 22:00 is inside, 05:00 is
    outside (`sc-012`, `sc-013`).
12. **Miss the eligibility condition added in 2024.** Give a body corporate a
    community quay discount for a 2024 landing (`sc-018`).
13. **Apply the small operator threshold to chargeable rather than gross
    tonnage**, or to the wrong calendar year.
14. **Round intermediates.** Rounding the percentage step before the final
    rounding changes the answer on several items with fractional discounts.

---

## C. Operational failure modes

| symptom | likely cause | fix |
|---|---|---|
| `generator.py` exits 2 with "missing source file" | `corpus/` was not copied alongside the scripts | restore `corpus/statute_pack.md` and `corpus/items.json` |
| `verifier.py` reports gold disagreeing with the corpus | a hand-edited gold file, or a corpus edit without regeneration | re-run `generator.py` |
| `verifier.py` reports the bundle asset differing from the corpus | the same, for the statute pack | re-run `generator.py` |
| `verifier.py` reports a possible answer leak | new bundle text quotes an item id next to its gold value | reword the bundle text; do not weaken the check |
| `scorer.py` reports missing predictions | the solver omitted item ids | missing items score zero by design; no action needed |
| `scorer.py` reports duplicate prediction ids | the solver emitted an id twice | duplicated ids score zero by design, since the intended answer is not determined |
| accuracy of exactly 0.2 on a fresh solver | almost certainly the consolidate-and-forget-the-date failure | compare the run against `baselines/predictions_current_law_only.jsonl` before concluding anything about capability |
