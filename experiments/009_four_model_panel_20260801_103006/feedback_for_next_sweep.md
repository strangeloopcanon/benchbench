# Feedback For Next BenchBench Sweep

This file is generated from the current creator/solver sweep state. After the final solver finishes, give it to the next creator models with `--feedback-context`.

BenchBench is evaluating benchmark invention. The goal is a complete benchmark package that is valid, reproducible, externally solvable in principle, and still hard after strong tool-enabled solvers attack the public solver bundle.

## Result Grid

| creator | benchmark | solver gpt-5.6-sol | solver gpt-5.6-terra | solver Gemini 3.6 Flash | solver Claude Opus 5 Thinking (High) | max score | status |
|---|---|---:|---:|---:|---:|---:|---|
| gpt-5.6-sol | counterfeit_clock_v1 | NA | NA | NA | NA | NA | incomplete_panel |
| gpt-5.6-terra | Patchwork Access Logic (PAL) | NA | NA | NA | NA | NA | incomplete_panel |
| Gemini 3.6 Flash | artifact | NA | NA | NA | NA | NA | incomplete_panel |

## Benchmark Cards

These cards summarize what each prior benchmark actually asked, not just its name and score.

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

## Lessons For The Next Creator

- Do not make a clean puzzle where the public packet exposes one obvious parser, simulator, BFS, or brute-force strategy.
- Do not rely on type strictness, hidden labels, private vocabulary, malformed output expectations, or missing public evidence to create low scores.
- Treat all-zero rows as audit warnings, not as automatic benchmark wins.
- Prefer complete but messy public evidence, closed answer contracts, adversarial edge cases, cross-document consistency, and partial recoverability.
- A candidate should be rejected if any strong solver gets 30/30, or if all strong solvers get 0/30 and the public bundle cannot prove external solvability.
