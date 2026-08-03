# Benchmark Bank

## Stable Bank

Empty. There is no validated incumbent or reusable benchmark in the current
registry.

The historical comparison does have a clear leader: Reimbursement Forensics
is #1 after correcting the gold and rescoring the retained predictions. It
counts as a win over the challengers, but the invalid original gold keeps it
out of the stable bank.

## Historical Candidates Excluded From the Bank

| rank | benchmark | source | outcome | historical read | why it is excluded |
|---:|---|---|---|---|---|
| 1 | Reimbursement Forensics | Experiment 004 | invalid | Corrected retained-prediction scores are 12, 16, 11, 13, 11, 11; best historical candidate and a win over challengers. | Original emitted gold was wrong; a canonical version still requires regeneration and a fresh panel. |
| — | Service Credit Forensics | Experiment 007 | invalid | No valid comparative difficulty claim. | Gold uses a lower-precedence timeline than the public policy exposes. |
| — | Rosetta Fieldwork | Experiment 008 | infrastructure incomplete | Later successful cells reach 27/30. | GPT-5.2 was a provider error and Claude Opus timed out; the panel has no valid aggregate score. |
| — | Counterfeit Clock v1 | Experiment 009 | invalid | No solver cells ran. | The scorer omitted the controller-required `correct` field, so mechanical validation failed. |
| — | Patchwork Access Logic | Experiment 009 | invalid | No solver cells ran. | The scorer used custom strict-score fields, so mechanical validation failed. |
| — | Experiment 010 candidates | Experiment 010 | infrastructure incomplete | Every completed solver cell is 30/30. | Opus did not complete two cells, Gemini produced no valid candidate, and the scored candidates are too easy. |

Other past rows remain useful design provenance, but none has an explicit
`validated` registry entry. Historical scores do not substitute for that gate.

## Promotion Rule

A candidate enters this bank only after a new version has digest-backed public
evidence, matching gold and verifier semantics, deterministic scoring, no
private leakage, and a complete successful declared solver panel. The exact
machine-readable state is [`registry.v1.json`](registry.v1.json).
