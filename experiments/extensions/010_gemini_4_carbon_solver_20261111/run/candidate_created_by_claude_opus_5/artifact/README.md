# Consolidation Point

A benchmark for **time-indexed normative reasoning**: can a solver work out what
a rule actually said *for a particular event*, when the rule has been amended
eleven times and the amendments do not agree about when they bite?

## The task in one paragraph

A fictional jurisdiction charges a levy on harbour landings under an Act passed
in 2011. Over the next thirteen years the Act is amended by later Acts,
suspended in part by a temporary emergency Act, and re-rated by ministerial
orders. The solver is given the Act as originally enacted plus every instrument
that has since touched it, in chronological order and **not consolidated**.
Each item is a fact pattern - a landing on a stated date, at a stated time, of
a stated tonnage, assessed on a stated date - and the answer is the levy, an
exact whole number. Everything needed is in the bundle; nothing outside it is
relevant.

## Why this is hard

The arithmetic is trivial: three to six operations per item, no fractions
beyond a percentage or two. All of the difficulty is in deciding *which* rule
applies. The instruments are drafted the way real ones are, which means:

- an Act commences on one date but its individual sections apply from different
  later dates;
- one amendment keys off the **landing** date while another keys off the
  **assessment** date, so an old landing assessed late is computed under old
  rates but new rounding;
- an Act confers a power to appoint a commencement day, and the notice that
  follows appoints a day for only some of its sections - the rest never became
  law at all;
- a rate order is revoked before the date from which it was to have effect, so
  it never bites;
- a temporary Act suspends a charge for exactly twelve months and then expires;
- a repeal is accompanied by a savings provision that is itself limited by
  licence class and sunsets three years later;
- a later Act adds an eligibility condition to a discount that already existed.

A solver that flattens the timeline in either direction fails. Applying only
the original 2011 law scores 2/30. Applying only the fully consolidated 2024
law scores 6/30. Neither is close to solvable-by-shortcut.

Tool use helps less than it usually does. Writing a resolver is easy; the hard
part is knowing what predicates to put in it, and running the code cannot tell
you whether your reading of a savings provision was right.

## Package layout

```
README.md                      this file
benchmark_spec.json            capability claim, scoring, novelty argument
generator.py                   rebuilds gold + the whole solver bundle from corpus/
verifier.py                    structural, leakage and provenance checks
scorer.py                      exact-match scoring, writes score_report.json
gold_private_sample.jsonl      30 rows of {id, answer}
predictions.jsonl              gold self-score input (a copy of the gold answers)
validation_report.md           validation, baselines, solvability argument
failure_modes.md               known and anticipated failure modes
corpus/statute_pack.md         authored source: the legislative pack
corpus/items.json              authored source: cases, answers, trap tags
audit/gold_derivations.md      private worked derivation of all 30 answers
baselines/                     shortcut baseline prediction files
solver_bundle/                 the public bundle (no answers)
  SOLVER_MANIFEST.json
  README.md
  solver_packet.md             task, answer format, worked non-graded example
  items_private_sample.jsonl
  assets/statute_pack.md
```

`corpus/` is authored source, not generated output. `generator.py` reads it and
writes the gold file and the entire solver bundle, so deleting both and
regenerating reproduces the package exactly.

## Commands

```bash
python3 generator.py --sample-count 30 --seed 20260516 --out-dir .
python3 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
python3 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

Only the Python standard library is required. Any CPython 3.8 or later works;
the package was authored against 3.12.

Scoring a shortcut baseline instead:

```bash
python3 scorer.py --gold gold_private_sample.jsonl \
  --predictions baselines/predictions_current_law_only.jsonl \
  --out score_report_baseline.json
```

## Closest existing benchmarks, and why this is not one of them

Closest in spirit are **IFEval** and **tau-bench** (following a supplied rule
set), **MuSR** (multi-hop reasoning over a long supplied text), and **GSM8K**
(a numeric answer at the end). It differs from all of them in the same way:
those benchmarks give you one rule set and ask you to apply it, whereas this
one gives you a stack of dated diffs and makes *choosing the version of the
rule* the entire task. The arithmetic is deliberately kept trivial so that
numeric skill contributes almost nothing to the score.

It differs from **GPQA** and **Humanity's Last Exam** by rewarding no recalled
knowledge at all: the jurisdiction, the Act and every instrument in it are
invented for this benchmark, so retrieval and memorisation are worth zero and
there is no training corpus to leak from. It differs from **SWE-bench** and the
coding families because a tool-enabled solver can trivially write the resolver
and still get the answers wrong, since the difficulty is in the predicates
rather than the implementation.

See `benchmark_spec.json` for the itemised comparison.
