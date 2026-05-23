# Experiment 004 Solvability Audit

This note checks the two rows that needed explanation after the feedback-driven
five-model sweep: GPT-5.5's all-zero Cross-Document Obligation Resolution
benchmark and Gemini 3.1 Pro's mixed Corrupted LZ77 Recovery benchmark.

## GPT-5.5: Cross-Document Obligation Resolution

Verdict: not a clean unsolvable benchmark. It is a scoring-contract failure.

The public dossiers contain the facts and procedural rules needed to compute
the notification date, board review posture, remediation, and hold. The solver
outputs confirm this: every solver recovered all 30 notification dates.

The exact scorer still gave 0/30 because the public packet did not enumerate
the exact accepted strings for `evidence_codes` and some categorical values.
For example, solvers used natural aliases such as `COUNT_GE_100`,
`affected_count_ge_100`, or `affected_count_100`, while the private gold used
`volume>=100`. Solvers also used variants such as `required` versus
`conditional_required` and `no_hold` versus `none`.

Relaxed audit against the saved predictions:

| solver | exact scorer | notify date | date + remediation | core fields, exact labels, no evidence_codes | core fields, normalized labels, no evidence_codes | core action semantics, no evidence_codes |
|---|---:|---:|---:|---:|---:|---:|
| GPT-5.2 | 0/30 | 30/30 | 28/30 | 20/30 | 20/30 | 25/30 |
| GPT-5.4 | 0/30 | 30/30 | 28/30 | 20/30 | 23/30 | 28/30 |
| GPT-5.5 | 0/30 | 30/30 | 28/30 | 20/30 | 23/30 | 28/30 |
| Gemini 3.1 Pro | 0/30 | 30/30 | 28/30 | 0/30 | 20/30 | 25/30 |
| Gemini 3.5 Flash | 0/30 | 30/30 | 28/30 | 20/30 | 23/30 | 28/30 |

Interpretation: this benchmark is externally solvable in substance, but the
submitted package is not a valid all-zero keeper. To use it, the creator would
need to publish a closed answer vocabulary or remove/free-normalize
`evidence_codes`.

## Gemini 3.1 Pro: Corrupted LZ77 Recovery

Verdict: not unsolvable.

The task gives the corrupted binaries, decompression code, CRC rule, and target
uncompressed size. GPT-5.4 recovered 22/30 hashes and GPT-5.5 recovered 17/30.
That is enough evidence that the public bundle is solvable in principle.

The weak cells mean different things:

- GPT-5.2 returned 30 blank answers.
- Gemini 3.1 Pro returned no parsed prediction rows.
- Gemini 3.5 Flash timed out and produced no usable predictions.

Interpretation: this is a real technical search/recovery task, not an
unknowable one. It still needs a promotion audit because the generated package
uses a very synthetic payload family, several solvers failed operationally, and
the benchmark may be more about writing a specialized recovery algorithm than
about a broad reasoning axis.
