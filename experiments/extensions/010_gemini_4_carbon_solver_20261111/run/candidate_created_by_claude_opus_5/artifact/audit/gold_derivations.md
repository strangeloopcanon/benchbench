# Private audit trace: derivation of every gold answer

This file is not part of the solver bundle. It exists so that a human auditor
can check every gold value against the source pack in a few minutes.

## Step 1 - the consolidated parameter timeline

Derived from `corpus/statute_pack.md`. Unless a row says otherwise, the
governing date is the date of the landing (principal Act s.12, rule A3).

| parameter | value | applies to |
|---|---|---|
| base rate (s.6) | 40 | landings before 1 Jul 2014 |
| base rate | 48 | landings on/after 1 Jul 2014 (C1 s.2 + s.4) |
| base rate | 55 | landings on/after 1 Apr 2020 (C5) |
| base rate | 62 | landings on/after 1 Feb 2023 (C10) |
| base rate | *58 never applies* | C7 was to bite on landings from 1 Jan 2022 but C8 revoked it from 31 Dec 2021, before its effect date (rule A6) |
| free allowance (s.7) | 2 t | landings before 1 Oct 2016 |
| free allowance | 1 t | landings on/after 1 Oct 2016 (C2 s.2, commenced by C3) |
| berth surcharge (s.8) | 150 powered / 60 other | landings before 1 Jul 2022 |
| berth surcharge | nil | landings 1 Mar 2021 to 28 Feb 2022 inclusive (C6) |
| berth surcharge | 180 powered / 75 other | landings on/after 1 Jul 2022 (C9 s.3 + s.5) |
| night supplement (s.8A) | not law | landings before 1 Oct 2016 |
| night supplement | 90 | landings on/after 1 Oct 2016 (C2 s.3, commenced by C3) |
| night supplement | 120 | landings on/after 1 Jul 2022 (C9 s.4) |
| night supplement trigger | commences at/after 22:00 or before 05:00 | exactly 05:00 does not qualify |
| cold-chain rebate (s.8B) | **never in force** | C2 s.4 was never appointed a day by C3; rule A1 |
| small operator allowance (s.9) | 20% of base amount | landings before 1 Jan 2015 |
| small operator allowance | 25% of base amount | landings 1 Jan 2015 to 31 Dec 2018 (C1 s.3) |
| small operator allowance | repealed | landings on/after 1 Jan 2019 (C4 s.2) |
| small operator allowance | saved at 25% | landings before 1 Jan 2022 by an operator holding a Class C licence on 31 Dec 2018 (C4 s.3) |
| small operator test | prior calendar year gross landed weight <= 50 t | s.9(3); "did not exceed" so exactly 50.0 t qualifies |
| community quay discount (s.9A) | not law | landings before 1 Jan 2019 |
| community quay discount | 15% of (base amount + berth surcharge) | landings on/after 1 Jan 2019 (C4 s.4) |
| community quay discount | additionally requires operator is not a body corporate | landings on/after 1 Jan 2024 (C11 s.3) |
| 24-hour aggregation (s.7A) | not law | landings before 1 Jan 2024 |
| 24-hour aggregation | applies | landings on/after 1 Jan 2024 (C11 s.2) |
| rounding (s.11) | nearest 5, midway **up** | **assessments** issued before 1 Jul 2022 |
| rounding | nearest 10, midway **down** | **assessments** issued on/after 1 Jul 2022, whenever the landing occurred (C9 s.2 + s.5) |

Notation used below:

- `T` = gross landed weight rounded up to a whole tonne (a whole number is not
  increased, s.7(2)).
- `CT` = chargeable tonnage = max(0, T - free allowance).
- `BASE` = rate x CT. `SUR` = berth surcharge. `NIGHT` = night supplement.
- `SOA` = small operator allowance. `CQD` = community quay discount.
- `RAW` = BASE + SUR + NIGHT - SOA - CQD, computed exactly (rule A7).

## Step 2 - per-item derivations

**sc-001** landing 14 Mar 2013 09:20, assessment 2 Apr 2013.
Rate 40, FA 2 t. T = ceil(7.4) = 8, CT = 6, BASE = 240. Powered berth: SUR = 150.
No night supplement in 2013. 210 t in 2012, not a small operator.
RAW = 390. Round nearest 5 (assessment pre-2022): **390**.

**sc-002** landing 3 Sep 2014 11:05, assessment 20 Sep 2014.
Landing on/after 1 Jul 2014 so rate 48. FA 2 t. T = 5, CT = 3, BASE = 144.
Non-powered: SUR = 60. Small operator (38 t in 2013). The 25% rate bites only
on landings on/after 1 Jan 2015, so SOA = 20% x 144 = 28.8.
RAW = 175.2. Nearest 5: 175 is 0.2 away, 180 is 4.8 away. **175**.

**sc-003** landing 8 Feb 2015 07:40, assessment 1 Mar 2015.
Rate 48, FA 2 t. T = ceil(9.2) = 10, CT = 8, BASE = 384. Powered: SUR = 150.
Small operator (44 t in 2014), now at 25%: SOA = 96.
RAW = 438. Nearest 5: 440 is 2 away, 435 is 3 away. **440**.

**sc-004** landing 5 Nov 2016 23:30, assessment 20 Nov 2016.
Rate 48. FA is 1 t (C2 s.2 commenced 1 Oct 2016). T = ceil(4.1) = 5, CT = 4,
BASE = 192. Non-powered: SUR = 60. Discharge at 23:30 is a night landing:
NIGHT = 90. The produce was chilled, but s.8B was never commenced (C3 appointed
a day only for ss.2 and 3), so there is no 200 mark rebate. Not a small
operator (300 t).
RAW = 342. Nearest 5: 340 is 2 away, 345 is 3 away. **340**.

**sc-005** landing 28 Sep 2016 23:10, assessment 10 Oct 2016.
Three days before the appointed day, so FA is still 2 t and s.8A is not yet
law. Rate 48. T = ceil(3.6) = 4, CT = 2, BASE = 96. Powered: SUR = 150. No
night supplement. Not small (640 t).
RAW = 246. Nearest 5: 245 is 1 away. **245**.

**sc-006** landing 12 Apr 2019 10:00, assessment 3 May 2019.
Rate 48, FA 1 t. T = 12, CT = 11, BASE = 528. Non-powered: SUR = 60. Day
landing. The operator would be small (30 t in 2018) but s.9 is repealed for
landings on/after 1 Jan 2019 and the savings need a Class C licence; this
operator held Class A. Community quay, sole trader, landing before 2024:
CQD = 15% x (528 + 60) = 88.2.
RAW = 499.8. Nearest 5: **500**.

**sc-007** landing 15 Jun 2019 13:20, assessment 1 Jul 2019.
Rate 48, FA 1 t. T = 7, CT = 6, BASE = 288. Powered: SUR = 150. Class C licence
on 31 Dec 2018 and landing before 1 Jan 2022, so the savings in C4 s.3 keep
s.9 alive as it stood immediately before 2019, i.e. at 25%. Small (41 t).
SOA = 72. Not a community quay.
RAW = 366. Nearest 5: 365 is 1 away. **365**.

**sc-008** landing 10 Jan 2022 15:45, assessment 25 Jan 2022.
Rate 55 - the 58 mark order was revoked before it could bite. FA 1 t. T = 7,
CT = 6, BASE = 330. The landing falls inside the emergency period, so
SUR = 0. Day landing. The savings expired for landings on/after 1 Jan 2022, so
no allowance despite the Class C licence and the 20 t prior year.
RAW = 330. Assessment before 1 Jul 2022, nearest 5: **330**.

**sc-009** landing 4 Dec 2021 02:15, assessment 20 Dec 2021.
Rate 55, FA 1 t. T = ceil(9.9) = 10, CT = 9, BASE = 495. Emergency period:
SUR = 0. Night landing at 02:15, supplement still 90. Not small (480 t).
RAW = 585. Nearest 5: **585**.

**sc-010** landing 15 Mar 2022 08:30, assessment 30 Mar 2022.
The emergency Act expired at the end of 28 Feb 2022, so s.8 applies again, at
its pre-July-2022 figures. Rate 55, FA 1 t. T = 5, CT = 4, BASE = 220.
Non-powered: SUR = 60.
RAW = 280. Nearest 5: **280**.

**sc-011** landing 20 May 2022 12:00, assessment 4 Aug 2022.
Landing before 1 Jul 2022, so rate 55 and powered surcharge 150. FA 1 t.
T = ceil(3.3) = 4, CT = 3, BASE = 165. RAW = 315.
The assessment issued on 4 Aug 2022, and C9 s.5 applies the replacement
rounding rule by assessment date whenever the landing occurred. Nearest 10,
and 315 is exactly midway between 310 and 320, so round down. **310**.

**sc-012** landing 3 Aug 2022 22:00, assessment 15 Aug 2022.
Rate 55 (62 starts 1 Feb 2023). FA 1 t. T = 8, CT = 7, BASE = 385. Powered
berth, landing on/after 1 Jul 2022: SUR = 180. 22:00 is within the night window
because the trigger is "at or after 22:00": NIGHT = 120.
RAW = 685, exactly midway between 680 and 690, round down. **680**.

**sc-013** landing 9 Sep 2022 05:00, assessment 1 Oct 2022.
Rate 55, FA 1 t. T = 6, CT = 5, BASE = 275. Non-powered, post-July-2022:
SUR = 75. 05:00 is not "before 05:00", so no night supplement.
RAW = 350, already a multiple of 10. **350**.

**sc-014** landing 20 Dec 2022 16:10, assessment 10 Jan 2023.
Rate 55 (the 2023 order bites from 1 Feb 2023; the 2021 order was revoked).
FA 1 t. T = ceil(11.5) = 12, CT = 11, BASE = 605. Powered: SUR = 180.
Community quay, sole trader, and the body corporate restriction only starts in
2024: CQD = 15% x 785 = 117.75.
RAW = 667.25. Nearest 10: 670 is 2.75 away, 660 is 7.25 away. **670**.

**sc-015** landing 14 Feb 2023 09:00, assessment 1 Mar 2023.
Rate 62. FA 1 t. Gross is exactly 2.0 t, and s.7(2) means it is not rounded up
to 3, so T = 2, CT = 1, BASE = 62. Non-powered: SUR = 75.
RAW = 137. Nearest 10: **140**.

**sc-016** landing 3 May 2023 11:30, assessment 20 May 2023.
T = ceil(0.8) = 1, CT = max(0, 1 - 1) = 0, BASE = 0. Powered: SUR = 180.
RAW = 180. **180**.

**sc-017** landing pair 8 Feb 2024 at 14:00 (3.0 t) and 20:00 (5.0 t),
assessment 1 Mar 2024.
Same operator, same harbour, six hours apart, and the landings are on/after
1 Jan 2024, so s.7A aggregates them for ss.6 and 7. Aggregated gross = 8.0 t,
T = 8, CT = 7, BASE = 62 x 7 = 434. Surcharge is charged per constituent
landing: SUR = 180 x 2 = 360. Neither landing is at night.
RAW = 794, a single levy rounded once. Nearest 10: 790 is 4 away. **790**.
(Computing the two levies separately would give 300 + 430 = 730.)

**sc-018** landing 20 Mar 2024 10:15, assessment 5 Apr 2024.
Rate 62, FA 1 t. T = 7, CT = 6, BASE = 372. Non-powered: SUR = 75. Community
quay, but from 1 Jan 2024 the discount is unavailable to a body corporate, and
this operator is a limited company. No CQD.
RAW = 447. Nearest 10: 450 is 3 away. **450**.

**sc-019** landing 21 Mar 2024 03:00, assessment 5 Apr 2024.
Same figures as sc-018 except the operator is an individual and the landing is
at night. BASE = 372, SUR = 75, NIGHT = 120.
CQD = 15% x (372 + 75) = 67.05.
RAW = 372 + 75 + 120 - 67.05 = 499.95. Nearest 10: **500**.

**sc-020** landing 10 Oct 2018 09:45, assessment 1 Nov 2018.
Rate 48, FA 1 t. T = 6, CT = 5, BASE = 240. Powered: SUR = 150. s.9A does not
exist until 1 Jan 2019, so the community quay is irrelevant. Not small (300 t).
RAW = 390. Nearest 5: **390**.

**sc-021** landing 4 Jul 2016 12:30, assessment 20 Jul 2016.
Before the appointed day, so FA 2 t. Rate 48. T = 10, CT = 8, BASE = 384.
Non-powered: SUR = 60. Prior year exactly 50.0 t, which "did not exceed 50
tonnes", so the operator is small; the 2015 rate of 25% applies. SOA = 96.
RAW = 348. Nearest 5: 350 is 2 away, 345 is 3 away. **350**.

**sc-022** landing 12 Aug 2016 12:30, assessment 26 Aug 2016.
Identical except the prior year is 50.4 t, which exceeds 50, so no allowance.
RAW = 384 + 60 = 444. Nearest 5: 445 is 1 away. **445**.

**sc-023** landing 1 Jul 2014 06:00, assessment 15 Jul 2014.
The new rate applies to landings "on or after 1 July 2014", and this is that
day. Rate 48, FA 2 t. T = 15, CT = 13, BASE = 624. Powered: SUR = 150.
RAW = 774. Nearest 5: 775 is 1 away. **775**.

**sc-024** landing 30 Jun 2014 06:00, assessment 15 Jul 2014.
One day earlier, so rate 40 even though the assessment issued after
commencement. CT = 13, BASE = 520, SUR = 150.
RAW = 670. **670**.

**sc-025** landing 31 Mar 2020 08:00, assessment 20 Apr 2020.
The 55 mark order bites on landings on/after 1 Apr 2020, so the rate here is
still 48. FA 1 t. T = ceil(6.6) = 7, CT = 6, BASE = 288. Powered: SUR = 150.
Community quay, individual: CQD = 15% x 438 = 65.7.
RAW = 372.3. Nearest 5: 370 is 2.3 away, 375 is 2.7 away. **370**.

**sc-026** landing 1 Apr 2020 08:00, assessment 20 Apr 2020.
One day later, so rate 55. CT = 6, BASE = 330, SUR = 150,
CQD = 15% x 480 = 72.
RAW = 408. Nearest 5: 410 is 2 away, 405 is 3 away. **410**.

**sc-027** landing 2 Jun 2013 10:00, assessment 9 Sep 2022.
The landing is governed by 2013 law: rate 40, FA 2 t, powered/non-powered
150/60. T = ceil(4.5) = 5, CT = 3, BASE = 120. Non-powered: SUR = 60. Small
operator (12 t in 2012) at the original 20%: SOA = 24. RAW = 156.
The assessment issued on 9 Sep 2022, so the replacement rounding rule applies:
nearest 10. 160 is 4 away, 150 is 6 away. **160**.

**sc-028** landing pair 11 Jun 2024 23:30 (2.0 t) and 12 Jun 2024 04:00
(4.0 t), assessment 1 Jul 2024.
Four and a half hours apart, same operator and harbour, so s.7A aggregates.
Aggregated gross 6.0 t, T = 6, CT = 5, BASE = 62 x 5 = 310. Surcharge per
constituent landing: 180 x 2 = 360. Both constituent landings are night
landings (23:30 is at or after 22:00; 04:00 is before 05:00), and s.7A(3)
charges the supplement per constituent landing: 120 x 2 = 240.
RAW = 910. **910**.

**sc-029** landing pair 5 Mar 2023 08:00 (3.0 t) and 18:00 (5.0 t),
assessment 20 Mar 2023.
s.7A does not exist for landings before 1 Jan 2024, so these are two separate
levies, each rounded separately under rule A8.
First: T = 3, CT = 2, BASE = 124, SUR = 180, RAW = 304, nearest 10 gives 300.
Second: T = 5, CT = 4, BASE = 248, SUR = 180, RAW = 428, nearest 10 gives 430.
Total **730**.

**sc-030** landing 15 Sep 2021 01:00, assessment 2 Oct 2021.
Rate 55, FA 1 t. T = ceil(8.4) = 9, CT = 8, BASE = 440. Emergency period, so
SUR = 0. Night landing at 01:00, supplement 90. Class C licence on 31 Dec 2018
and landing before 1 Jan 2022, prior year 47 t, so the saved s.9 applies at
25%: SOA = 110. Community quay, individual:
CQD = 15% x (440 + 0) = 66.
RAW = 440 + 0 + 90 - 110 - 66 = 354. Assessment before 1 Jul 2022, nearest 5:
355 is 1 away, 350 is 4 away. **355**.

## Step 3 - trap coverage

| trap | items |
|---|---|
| amendment commences but applies from a later date | sc-002 |
| provision never brought into operation | sc-004 |
| appointed-day boundary (day before / day of) | sc-005, sc-004 |
| rate-change boundary (day before / day of) | sc-023, sc-024, sc-025, sc-026 |
| subordinate order revoked before its effect date | sc-008, sc-014 |
| temporary suspension inside its window | sc-008, sc-009, sc-030 |
| temporary suspension after expiry | sc-010 |
| repeal with a conditional saving | sc-006, sc-007 |
| saving that has itself expired | sc-008 |
| application keyed to assessment date, not landing date | sc-011, sc-027 |
| midway rounding, and the direction flip | sc-011, sc-012 |
| inclusive/exclusive time boundary | sc-012, sc-013 |
| threshold "did not exceed" at and just over the line | sc-021, sc-022 |
| whole-tonne weights not rounded up | sc-015, sc-017, sc-023, sc-028, sc-029 |
| chargeable tonnage floored at nil | sc-016 |
| aggregation rule applied and correctly not applied | sc-017, sc-028, sc-029 |
| eligibility condition added by later amendment | sc-018, sc-019 |
| relief that did not yet exist | sc-020 |
