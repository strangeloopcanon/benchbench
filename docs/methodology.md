# Methodology

BenchBench evaluates benchmark invention. A creator model proposes a complete
benchmark package. Solver models receive only its public bundle. Low solver
scores matter only after the package, execution record, and public-to-private
answer contract have passed review.

## Evidence Model

Raw experiment folders are immutable evidence. Corrections are recorded as new
adjudications or new benchmark versions; they do not rewrite the original run.
The authoritative interpretation is `experiments/registry.v1.json`.

BenchBench keeps three questions separate:

1. **Mechanical validity:** does the package generate deterministically, obey
   its data contracts, keep gold private, and score its controls correctly?
2. **Cell validity:** did an attributable provider/model call return a complete
   prediction set that a valid scorer processed successfully?
3. **Adjudication:** is the task fair, externally solvable, correctly keyed,
   useful, and eligible for canonical comparison?

A package can pass mechanical checks and still fail adjudication. A low score
can be retained as historical evidence without becoming a benchmark claim.

## Candidate Contract

Each creator produces these private-root files:

- `README.md`
- `benchmark_spec.json`
- `generator.py`
- `verifier.py`
- `scorer.py`
- `gold_private_sample.jsonl`
- `validation_report.md`
- `failure_modes.md`

The public `solver_bundle/` contains:

- `SOLVER_MANIFEST.json`
- `items_private_sample.jsonl`
- `README.md` or `solver_packet.md`
- every solver-visible asset required by the stated rules

Gold and predictions use exact JSONL rows:

```json
{"id":"...","answer":"..."}
```

IDs must be unique and identical across public items, gold, and a complete
prediction panel.

## Mechanical Validation

Generated code never runs against the canonical candidate directory. The
controller copies the candidate into clean scratch workspaces and runs it in a
fail-closed OS sandbox with the user home and network unavailable. It:

- removes expected generated outputs before each run, preventing stale files or
  no-op generators from passing;
- runs the same seed twice and compares output-tree digests;
- verifies exact file and JSONL contracts;
- runs the verifier;
- requires the gold self-score to be exactly `30/30`;
- requires the shifted-wrong control to be exactly `0/30`;
- rejects prohibited private files and per-ID answer leakage in the public
  bundle;
- requires a substantive external-solvability explanation.

These are mechanical gates, not a fairness verdict. Promotion still requires a
digest-backed adjudication with outcome `validated`.

## Solver Isolation

Every solver receives a fresh temporary copy of `solver_bundle/` outside the
repository. One outer macOS sandbox denies reads from the repository, including
candidate gold and source code, and exposes a randomized empty provider home.
No persistent credential file enters that boundary. The trusted Codex parent receives only
the current bearer token and account ID in two dedicated environment variables;
a command-backed provider reads the bearer directly from its parent environment.
Model-created shells inherit no provider environment and cannot inspect the
parent process table; the legacy `KERN_PROCARGS` and current `KERN_PROCARGS2`
sysctl environment channels are also denied explicitly. Refresh tokens,
histories, memories, configuration, hooks, plugins, and sessions never enter
the boundary. Nested Codex Seatbelt profiles are not viable on macOS, so Codex
uses the outer profile as its OS boundary.

Antigravity retains its provider-native file permissions inside the outer
profile. It reads its OAuth session once from a FIFO in the
disposable home; the path is then removed and explicitly write-denied, so a
refreshed credential cannot appear for model tools to read.
If credential brokering or containment cannot be established, the cell is
unavailable; the harness does not fall back to an unrestricted host call. Live
execution is limited to the audited Codex and Antigravity paths. Cursor is
preflight-only because its native authentication token reaches model-created
terminal tools; the harness rejects live Cursor calls before loading it.

Provider-qualified identities are part of every new artifact name. For
example, Codex `gpt-5.2` and Cursor `gpt-5.2` are different identities and
cannot share a prediction or score path.

## Score And Cell States

The normalized score schema requires integral `total` and `correct` counts,
`0 <= correct <= total`, and an accuracy consistent with `correct / total`.
Legacy scorer shapes remain readable only through the compatibility parser;
new normalized reports use schema version 2.

A numeric score exists only for a complete successful cell. Other outcomes are
states, including:

- provider unavailable or provider error;
- timeout or model mismatch;
- no predictions, partial predictions, or parse failure;
- scorer failure or invalid score schema;
- invalid benchmark or cell not run.

None of those states is `0/30`. Candidate acceptance requires every declared
solver cell to complete successfully. A true all-zero successful row goes to a
solvability audit; it is not a win by default. A candidate is too easy when any
declared strong solver reaches the rejection threshold.

## Run Safety

The harness preflights every unique provider/model before the first creator
call. Preflight is read-only and never submits an inference prompt. It verifies
the CLI, requests each provider's model catalog where supported, and verifies
Codex effort availability for the exact requested model. A live run cannot
begin when a listed model or requested Codex effort is unavailable.

New run roots are append-only evidence. The harness refuses a non-empty root
instead of silently reusing creator files or stale scores. Scorers write to a
unique temporary output; the controller validates it and atomically publishes
only an allowlisted normalized record after a successful exit. Creator-authored
scorer output and scorer stdout/stderr are never published. Repairs create a
new candidate snapshot rather than mutating the failed creator snapshot.

Raw provider prompts, stdout, stderr, and provider logs are local diagnostic
material, not public benchmark evidence. They may contain account metadata,
machine paths, or provider internals. Public experiment bundles retain the
portable manifests, validation records, packages, predictions, and scores;
raw transcript paths are replaced with an explicit
`private_raw_evidence_not_published` marker and public digests are rebound.

## Canonical Promotion

`scripts/build_6x6_result_artifacts.py` derives the current presentation from
the registry. A candidate enters the canonical comparison only when its entry:

- has outcome `validated`;
- is explicitly `canonical_eligible`;
- carries digest-backed evidence;
- binds its mechanical record to the frozen benchmark-package digest;
- binds its declared model panel to a digest-verified run state and manifest;
- stores every score and prediction at the exact controller-owned
  `solver_results` path outside the creator package;
- has one unique successful manifest cell per declared model, with matching
  invocation, package, gold, and prediction digests.

Invalid and incomplete runs remain visible as history, with non-score states
rendered separately from numeric results. The current registry has no validated
incumbent. Separately, the corrected historical comparison ranks Reimbursement
Forensics #1 and treats it as a win over the challengers: its retained
predictions remain low and nonzero across all six solvers after Decimal
correction. That historical rank does not override the invalid original gold
or the promotion gate. The review queue is in
[`experiments/review_queue.md`](../experiments/review_queue.md).

## Similarity And Limits

Novelty is estimated only after enough models overlap the candidate and public
benchmark matrix. The regression path produces leave-one-out predictions and
computes one global out-of-fold R2; a one-row fold is never assigned its own R2.

BenchBench does not yet show that one model is generally the best benchmark
designer. It does show that Reimbursement Forensics is the strongest corrected
historical result within these runs, while keeping its invalid original run
outside the canonical leaderboard. It records which candidate packages
survived the current validity, execution, and review gates.
