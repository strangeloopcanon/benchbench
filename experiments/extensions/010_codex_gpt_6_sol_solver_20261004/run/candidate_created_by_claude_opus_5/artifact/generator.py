#!/usr/bin/env python3
"""Generator for the Consolidation Point benchmark.

Reads the authored source corpus in ./corpus and writes, from scratch:

    <out-dir>/gold_private_sample.jsonl
    <out-dir>/solver_bundle/items_private_sample.jsonl
    <out-dir>/solver_bundle/assets/statute_pack.md
    <out-dir>/solver_bundle/solver_packet.md
    <out-dir>/solver_bundle/README.md
    <out-dir>/solver_bundle/SOLVER_MANIFEST.json

The item bank is a fixed, hand-authored, hand-audited corpus rather than a
procedurally sampled one.  Item selection is therefore fully deterministic:
items are ordered by item id and the first --sample-count of them are emitted.
--seed is recorded in the manifest for provenance and deliberately does not
perturb selection or content, so regeneration is byte-identical for every seed.

Usage:
    python3 generator.py --sample-count 30 --seed 20260516 --out-dir .
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(HERE, "corpus")

BENCHMARK_NAME = "Consolidation Point"
BENCHMARK_VERSION = "1.0.0"


SOLVER_PACKET = """# Consolidation Point - Solver Packet

## The situation

You are acting as a levy assessor in the fictional Republic of Marnholt.

A single statute, the Harbour Dues and Aquaculture Levy Act 2011, charges a
levy on landings of farmed produce at harbours. Over the following thirteen
years that statute was repeatedly amended by later Acts, suspended in part by
a temporary emergency Act, and had its base rate changed by ministerial
orders. Those instruments do not arrive pre-consolidated. Each one carries its
own commencement rule and, separately, its own application rule saying which
landings or which assessments the change bites on. Some of them never came
into operation at all.

## What you are given

- `assets/statute_pack.md` - the complete legislative source pack. Part A sets
  out the interpretation and application rules, Part B is the principal Act as
  originally enacted, Part C is every instrument that has since affected it,
  in chronological order of making.
- `items_private_sample.jsonl` - one JSON object per line, each a graded case.
  Fields: `id`, `case_ref`, `assets`, `question`, `answer_format`.

Everything you need is in those two files. There is no external corpus to
retrieve, no real-world law to look up, and no hidden generator state. Two
solvers who read the pack correctly must arrive at the same number.

## Your task

For each case, work out the law as it stood for that landing and that
assessment, apply it to the stated facts, and report the levy.

The intended method is:

1. Build a timeline for each operative parameter (base rate, free allowance,
   berth surcharge, night landing supplement, small operator allowance,
   community quay discount, aggregation rule, rounding rule). For each
   parameter, record which value applies to which landings, and note where an
   application provision keys off something other than the landing date.
2. Check, for every instrument, whether it actually came into operation, and
   on what day. A power to appoint a day that was never exercised means the
   provision is not law. A subordinate order revoked before its own effect
   date never bites.
3. Read the facts of the case, select the parameter values that apply, and
   compute.

## Answer format

Reply with a single whole number: the total levy in marks. Digits only - no
currency symbol, no thousands separator, no words. Grading is exact match on
the normalised integer.

Your submission is a JSONL file with one object per line containing exactly
two keys, `id` and `answer`:

    {"id": "sc-000", "answer": "370"}

Every item id in `items_private_sample.jsonl` must appear exactly once.
(`sc-000` above is a placeholder; it is not one of the graded ids.)

## Worked example

This example is not one of the graded cases. It is given so that the
arithmetic conventions are unambiguous.

> On 6 May 2020, with discharge commencing at 21:00, Halvern Produce Limited
> (a body corporate) landed 4.3 tonnes gross of farmed produce at a scheduled
> harbour. The vessel occupied a powered berth. The quay is not a community
> quay. The operator's total gross landed weight at all scheduled harbours
> during 2019 was 900 tonnes. The operator held a Class A licence on
> 31 December 2018. The harbour master issued the notice of assessment on
> 1 June 2020.

Working:

- Base rate. The Levy Rates Order 2020 substituted 55 marks with effect for
  landings on or after 1 April 2020. This landing is later than that, so the
  rate is 55 marks per tonne.
- Chargeable tonnage. The free allowance was reduced from 2 tonnes to 1 tonne
  for landings on or after 1 October 2016. Gross weight 4.3 tonnes rounds up
  to 5 whole tonnes; less the 1 tonne free allowance gives chargeable tonnage
  of 4. Base amount = 55 x 4 = 220 marks.
- Berth surcharge. The increase to 180 marks applies only to landings on or
  after 1 July 2022, so the powered-berth surcharge here is 150 marks.
- Night landing supplement. The supplement applies to a landing commencing at
  or after 22:00 or before 05:00. Discharge commenced at 21:00, so no
  supplement.
- Small operator allowance. The allowance was repealed for landings on or
  after 1 January 2019 and this operator does not fall within the savings
  provision. In any event 900 tonnes in the preceding calendar year exceeds
  the 50 tonne threshold. No allowance.
- Community quay discount. Not a community quay. No discount.
- Total before rounding: 220 + 150 = 370 marks.
- Rounding. The replacement rounding rule applies to assessments issued on or
  after 1 July 2022. This assessment issued on 1 June 2020, so the original
  rule applies: nearest multiple of 5 marks, midway rounded up. 370 is already
  a multiple of 5.

Answer: `370`

## Ground rules

- All amounts are computed exactly, with fractions of a mark retained, and
  rounded once at the end of each levy. See rule A7 of the pack.
- The facts of a case are complete. If the facts do not establish that a
  supplement, allowance, discount, rebate, saving or exemption applies, it
  does not apply. See rule A9.
- Where a case asks for a total in respect of more than one levy, compute and
  round each levy separately, then add. Where the pack instead charges a
  single levy on an aggregated landing, round once. See rule A8.
- The source pack is complete and self-contained. See rule A1.
"""


SOLVER_README = """# Consolidation Point - solver bundle

This directory is the complete public solver bundle for the Consolidation
Point benchmark. It contains no answers.

Contents:

- `solver_packet.md` - read this first. Task statement, answer format, ground
  rules and a fully worked example.
- `items_private_sample.jsonl` - the graded cases, one JSON object per line.
- `assets/statute_pack.md` - the legislative source pack referenced by every
  item.
- `SOLVER_MANIFEST.json` - machine-readable description of this bundle.

Produce a JSONL file with one object per line containing exactly the keys
`id` and `answer`, one line per item id, where `answer` is the levy in marks
written as digits only.
"""


def load_corpus():
    """Load the authored source corpus."""
    items_path = os.path.join(CORPUS_DIR, "items.json")
    pack_path = os.path.join(CORPUS_DIR, "statute_pack.md")
    for path in (items_path, pack_path):
        if not os.path.isfile(path):
            sys.stderr.write("ERROR: missing source file: " + path + "\n")
            raise SystemExit(2)
    with open(items_path, "r", encoding="utf-8") as handle:
        corpus = json.load(handle)
    with open(pack_path, "r", encoding="utf-8") as handle:
        pack_text = handle.read()
    return corpus, pack_text


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path, rows):
    lines = []
    for row in rows:
        lines.append(json.dumps(row, ensure_ascii=False))
    write_text(path, "\n".join(lines) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate the Consolidation Point sample.")
    parser.add_argument("--sample-count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260516)
    parser.add_argument("--out-dir", default=".")
    args = parser.parse_args(argv)

    if args.sample_count < 1:
        sys.stderr.write("ERROR: --sample-count must be at least 1\n")
        return 2

    corpus, pack_text = load_corpus()
    bank = sorted(corpus["items"], key=lambda row: row["id"])
    if args.sample_count > len(bank):
        sys.stderr.write(
            "ERROR: --sample-count %d exceeds the authored bank size %d\n"
            % (args.sample_count, len(bank))
        )
        return 2
    selected = bank[: args.sample_count]

    answer_format = corpus["answer_format"]
    asset_ref = "assets/statute_pack.md"

    out_dir = os.path.abspath(args.out_dir)
    bundle_dir = os.path.join(out_dir, "solver_bundle")
    assets_dir = os.path.join(bundle_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    gold_rows = []
    item_rows = []
    for row in selected:
        gold_rows.append({"id": row["id"], "answer": str(row["answer"])})
        item_rows.append(
            {
                "id": row["id"],
                "case_ref": row["case_ref"],
                "assets": [asset_ref],
                "question": row["question"],
                "answer_format": answer_format,
            }
        )

    gold_path = os.path.join(out_dir, "gold_private_sample.jsonl")
    items_path = os.path.join(bundle_dir, "items_private_sample.jsonl")

    write_jsonl(gold_path, gold_rows)
    write_jsonl(items_path, item_rows)
    write_text(os.path.join(assets_dir, "statute_pack.md"), pack_text)
    write_text(os.path.join(bundle_dir, "solver_packet.md"), SOLVER_PACKET)
    write_text(os.path.join(bundle_dir, "README.md"), SOLVER_README)

    manifest = {
        "schema_version": 2,
        "benchmark": BENCHMARK_NAME,
        "benchmark_id": corpus["benchmark_id"],
        "version": BENCHMARK_VERSION,
        "task": (
            "Reconstruct a fictional statute as it stood for a given landing and a "
            "given assessment date, from a base enactment plus a chronological stack "
            "of amending instruments, then apply it to the stated facts and report "
            "the levy."
        ),
        "item_count": len(item_rows),
        "item_ids": [row["id"] for row in item_rows],
        "items_file": "items_private_sample.jsonl",
        "packet_file": "solver_packet.md",
        "assets": [asset_ref],
        "item_fields": ["id", "case_ref", "assets", "question", "answer_format"],
        "answer_type": "integer",
        "answer_format": answer_format,
        "prediction_fields": ["id", "answer"],
        "prediction_file_format": "jsonl",
        "grading": "exact match on the normalised integer; one point per item",
        "selection": "fixed authored bank, ordered by item id, first --sample-count emitted",
        "generator_seed": args.seed,
        "seed_semantics": "recorded for provenance only; does not alter selection or content",
        "external_resources_required": False,
    }
    write_text(
        os.path.join(bundle_dir, "SOLVER_MANIFEST.json"),
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )

    sys.stdout.write(
        "Wrote %d items.\n  gold:   %s\n  bundle: %s\n"
        % (len(item_rows), gold_path, bundle_dir)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
