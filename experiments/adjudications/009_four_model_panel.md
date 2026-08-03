# Adjudication: Four-Model Panel (Experiment 009)

Outcome: **infrastructure incomplete; no benchmark result**.

The exact four-model non-inference preflight passed before the live run. The
declared creator and solver identities were Codex GPT-5.6 Sol at high, Codex
GPT-5.6 Terra at extra high, Antigravity `gemini-3.6-flash-high` at high, and
Cursor `claude-opus-5-thinking-high` at high. The live controller used a
500,000 reported-token ceiling and the explicit unmetered-cost acknowledgement.

The run root is
`experiments/009_four_model_panel_20260801_103006`. Its manifest digest is
`788d1b827915e4778944464a1b3085e8f67e448596537b665d6f9711015b94fb`.

## Calls

| phase | requested provider/model | effort | return code | reported tokens | state |
|---|---|---:|---:|---:|---|
| creator | Codex `gpt-5.6-sol` | high | 0 | 123,107 | candidate invalid |
| repair | Codex `gpt-5.6-sol` | high | 0 | 93,391 | candidate invalid |
| creator | Codex `gpt-5.6-terra` | xhigh | 0 | 72,858 | candidate invalid |
| repair | Codex `gpt-5.6-terra` | xhigh | 0 | 69,926 | candidate invalid |
| creator | Antigravity `gemini-3.6-flash-high` | high | 1 | 0 | provider error |

Total reported usage is **359,282 tokens**. The providers supplied no
controller-normalized dollar cost or cache-read/cache-write totals, so those
fields remain unreported rather than zero. No call started after zero token
telemetry appeared.

## Candidate gates

Counterfeit Clock v1 passed required files, external-solvability evidence,
generation, verification, deterministic regeneration, frozen-package matching,
and the leakage scan. Its creator and repair nevertheless emitted scorer JSON
with `exact_score`, not the controller-required `correct` field. Gold and
shifted-wrong controls remained unparseable, so the final mechanical validation
state is `valid: false`.

Patchwork Access Logic initially failed because its generator did not recreate
`solver_bundle/SOLVER_MANIFEST.json`. The repair fixed that: the final package
passed deterministic regeneration, verification, frozen-package matching,
external-solvability evidence, and the leakage scan. Its scorer emitted
`strict_score` and `strict_score_out_of`, not `correct` and `total`, so both
controller controls remained unparseable and the final mechanical validation
state is `valid: false`.

Neither invalid candidate was handed to a solver. Every solver cell is `NA`,
there are no numeric scores, and there is no winner.

## Infrastructure failure

Antigravity failed before inference while creating disposable local state. The
outer boundary denied writes to the whole disposable
`.gemini/antigravity-cli` directory, so the CLI could not create
`installation_id` or its crash directory. It returned code 1 with empty usage;
`antigravity_actual_label` is null. The fail-closed telemetry rule then stopped
the run before the Cursor creator call.

The boundary has since been narrowed to deny recreation of only the one-shot
`antigravity-oauth-token` pathname while allowing disposable provider state.
The creator and repair prompts now state the normalized score-report contract
explicitly. These repairs do not change Experiment 009's immutable evidence or
make its incomplete panel a result.
