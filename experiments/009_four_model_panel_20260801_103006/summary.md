# Broad BenchBench Sweep

This run used the broad creator prompt: creators saw benchmark landscape notes and prior pilot outcomes, but were not directed toward any specific domain or modality.

Run root: `./experiments/009_four_model_panel_20260801_103006`
Creator models: `gpt-5.6-sol, gpt-5.6-terra, gemini-3.6-flash-high, claude-opus-5`
Solver models: `gpt-5.6-sol, gpt-5.6-terra, gemini-3.6-flash-high, claude-opus-5`
Creator effort: `high`
Solver effort: `high`

Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.

## Benchmark Cards

### gpt-5.6-sol: counterfeit_clock_v1

- What it asks: Counterfeit Clock measures joint discrete model reconstruction and forensic outlier repair. A solver must align two naming systems for five stations, recover a bijection of modular clock rates and five offsets, match anonymous packets within repeated routes,....
- Intended capability: Reliably reconstruct coupled finite latent mappings and repair a single corrupted observation under modular arithmetic constraints.
- Creator-anticipated failure modes: bijection. also satisfies every public rule. repaired residue.
- Validation: `False`; bundle files: `3`; leak scan matches: `0`

### gpt-5.6-terra: Patchwork Access Logic (PAL)

- What it asks: For each JSON item, evaluate all ten requests against the base policy and the policy after the ordered patches. Return the exact canonical answer string specified in the solver packet.
- Intended capability: Faithfully execute a newly specified, non-monotonic policy semantics across a sequential counterfactual patch, including hierarchical scope, time/device-gated transitive membership, ordered precedence, and winning-rule provenance.
- Closest existing benchmarks: {"families": ["software/configuration reasoning", "formal rule execution", "tool-agent reliability"], "not_a_duplicate_because": "PAL is not a coding-completion or API-navigation task: the solver must infer no unstated policy intent and instead execute a compact, explicitly supplied operational semantics twice, preserve rule provenance, and account for an o...
- Validation: `False`; bundle files: `3`; leak scan matches: `0`

### Gemini 3.6 Flash: artifact

- Validation: `False`; bundle files: `0`; leak scan matches: `0`

## Solver Grid

| creator | benchmark | solver gpt-5.6-sol | solver gpt-5.6-terra | solver Gemini 3.6 Flash | solver Claude Opus 5 Thinking (High) | max score | status |
|---|---|---:|---:|---:|---:|---:|---|
| gpt-5.6-sol | counterfeit_clock_v1 | NA | NA | NA | NA | NA | incomplete_panel |
| gpt-5.6-terra | Patchwork Access Logic (PAL) | NA | NA | NA | NA | NA | incomplete_panel |
| Gemini 3.6 Flash | artifact | NA | NA | NA | NA | NA | incomplete_panel |

## Calls

| phase | creator | solver/model | rows | score | tokens | cost | cache read | cache write | returncode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| creator | gpt-5.6-sol | gpt-5.6-sol |  | NA | 123107 |  |  |  | 0 |
| repair | gpt-5.6-sol | gpt-5.6-sol |  | NA | 93391 |  |  |  | 0 |
| creator | gpt-5.6-terra | gpt-5.6-terra |  | NA | 72858 |  |  |  | 0 |
| repair | gpt-5.6-terra | gpt-5.6-terra |  | NA | 69926 |  |  |  | 0 |
| creator | gemini-3.6-flash-high | Gemini 3.6 Flash |  | NA | 0 |  |  |  | 1 |

Total reported tokens: `359282`
