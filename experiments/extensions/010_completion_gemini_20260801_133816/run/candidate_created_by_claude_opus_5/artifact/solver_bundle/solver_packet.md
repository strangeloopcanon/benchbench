# Consolidation Point - Solver Packet

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
