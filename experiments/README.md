# Experiments

Raw run folders are immutable historical evidence. They do not establish a
current benchmark leader. The authoritative interpretation lives in
[`registry.v1.json`](registry.v1.json), and the generated current view is
[`canonical/README.md`](canonical/README.md).

## Current State

There is no validated incumbent. Reimbursement Forensics is nevertheless the
#1 corrected historical candidate and a comparative win over the challengers.

Four material findings prevent promotion:

- Experiment 004's Reimbursement Forensics gold fails Decimal half-up
  semantics, so the original run remains invalid. An independent correction
  and rescore of the retained predictions gives `12, 16, 11, 13, 11, 11` out
  of 30. That is still the only complete six-solver low-nonzero row and counts
  as a historical win over the later challengers; no model was rerun.
- Experiment 007's Service Credit Forensics public evidence gives a corrected
  timeline precedence over monitoring states, while historical gold used the
  lower-precedence states.
- Experiment 008's Fable sweep has a GPT-5.2 provider error and Claude Opus
  timeout. These are typed infrastructure states, never numeric zero scores.
- Experiment 009 produced two mechanically invalid candidates, then
  Antigravity failed before inference with zero usage telemetry. No solver
  cells ran, Cursor was not called, and every score is `NA`.
- Experiment 010 recovery gave Gemini three valid `30/30` solver results.
  Every completed cell is `30/30`; Opus did not complete two cells, and Gemini
  produced no mechanically valid candidate.

## Registry Contract

`registry.v1.json` is versioned and digest-backs the evidence files used for
adjudication. A canonical build rejects a candidate marked eligible unless its
outcome is `validated`. A complete fresh solver panel is required after a
generator, verifier, public evidence, scorer, or execution-state repair.

The source run folders remain available for provenance:

| experiment | role in current registry |
|---|---|
| 001–003, 005–006 | historical noncanonical provenance |
| 004 | invalid original run; #1 corrected historical candidate and win over challengers |
| 007 | invalid: public/gold precedence conflict |
| 008 | infrastructure incomplete: provider error and timeout |
| 009 | infrastructure incomplete: invalid candidates, Antigravity provider error, no solver cells |
| 010 | infrastructure incomplete: every completed cell is 30/30; two Opus cells did not complete; Gemini produced no valid candidate |

## Generated Artifacts

Run `python scripts/build_6x6_result_artifacts.py` to rebuild the canonical
Markdown, JSON status payload, and status figure deterministically from
the registry. The raw experiment folders are not rewritten by that command.
