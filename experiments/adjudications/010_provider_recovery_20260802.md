# Experiment 010 provider recovery — 2026-08-02

The original Experiment 010 artifacts were not changed. All retries and
diagnostics were written to new roots.

## Recovery run only

| model | creator result | solver result against Experiment 010 candidates | recovery verdict |
|---|---|---|---|
| Gemini 3.6 Flash (High) | No valid candidate. Experiment 011's initial creator call still hit the known permission denial; its repair completed but produced invalid `state_machine_trace`. Both Experiment 012 calls completed without permission denial but produced invalid `RADN-Sim`. | AuditWeave 30/30; CFPS 30/30; Consolidation Point 30/30 | Provider fixed; solver completed 3/3; completed creator/repair work produced 0 valid candidates. |
| Claude Opus 5 Thinking (High) | No new creator run. Existing valid candidate: Consolidation Point. | No retry: live Cursor is disabled because a credential-safe shell boundary is not available. | Did not complete 2/3 original solver cells. Do not treat those timeouts as scores. |

## Recovery-aware combined grid

| creator | candidate | Sol high | Terra extra high | Gemini 3.6 Flash high | Claude Opus 5 high |
|---|---|---:|---:|---:|---:|
| Sol | AuditWeave | 30/30 | 30/30 | 30/30 (recovery) | did not complete |
| Terra | Counterfactual Firewall Policy Synthesis | 30/30 | 30/30 | 30/30 (recovery) | did not complete |
| Gemini | no valid candidate | NA | NA | NA | NA |
| Opus | Consolidation Point | 30/30 | 30/30 | 30/30 (recovery) | 30/30 |

The Gemini solver recovery overlay is
`experiments/extensions/010_gemini_permission_recovery_20260802`. The two
creator recovery roots are `experiments/011_gemini_provider_recovery_20260802`
and `experiments/012_gemini_creator_recovery_20260802`.

## Interpretation

Gemini's original empty outputs were infrastructure failures. That problem is
fixed. The recovered model solved every available valid candidate perfectly,
so it supplies no evidence that those candidates are difficult. Experiment
011's initial creator call still retained the old permission denial; its repair
completed and failed mechanically. Experiment 012 then completed both creator
and repair calls without permission denial and failed mechanically.

Opus created a valid candidate and solved one of three candidates 30/30, but
timed out on the other two. The safe statement is **did not complete 2/3**.
Cursor's nested shell sandbox remains incompatible with the outer macOS
Seatbelt boundary; disabling it made shell tools work but exposed the Cursor
access token to those tools. Live Cursor execution is now disabled before any
credential is loaded, so no Opus retry was launched. The retained Experiment
010 Opus artifacts prove the requested CLI model ID, not response-level runtime
attestation; treat their provider identity as requested/unverified.

## Recovery token accounting

The Gemini solver overlay reported 241,080 tokens. Experiment 011 reported
215,678 and Experiment 012 reported 557,113, for **1,013,871 recovery tokens**.
Added to the original 7,036,873 reported tokens, the recovery-aware reported
total is **8,050,744**. The original 10,000,000-token reservation for the two
zero-telemetry Opus timeouts remains separate controller accounting, not
provider-reported consumption.

Reimbursement Forensics remains the historical #1 with its corrected retained
profile `12/30, 16/30, 11/30, 13/30, 11/30, 11/30`. The recovery results make
that comparison stronger: every completed Experiment 010 solver cell is now
30/30.
