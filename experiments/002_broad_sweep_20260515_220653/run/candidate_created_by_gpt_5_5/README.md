# Protocol Archaeology

Protocol Archaeology is a compact executable benchmark for black-box reverse
engineering from traces. Each item gives fourteen observed input/output pairs
from one deterministic byte-level firmware path, plus one new 8-byte query
packet. The solver must return the exact 4-byte response.

## Construct Claim

The benchmark measures whether an agent can infer an unfamiliar, stateful
symbolic transformation from limited examples, translate that inference into a
reliable computation, and resist plausible but wrong shortcuts. This matters for
software maintenance, protocol migration, data cleaning, incident response, and
agentic debugging, where the available evidence is often traces rather than a
clean specification.

Closest existing benchmarks are code/tool benchmarks such as SWE-bench and
LiveCodeBench, plus inductive reasoning tasks in BIG-bench. This package is not
a duplicate: it is not asking for code repair, contest programming, or static
puzzle answers. It evaluates trace-grounded program inference under a sealed
solver bundle, with deterministic generated items and exact scoring.

## Solver Task

Input: `solver_bundle/items_private_sample.jsonl`

Each item contains:

- `id`
- `protocol_note`
- `answer_format`
- `examples`: observed `packet` and `response` hex strings
- `query_packet`

Output predictions as JSONL with exactly:

```json
{"id":"pa-0000","answer":"0123abcd"}
```

The answer must be exactly 8 lowercase hex characters.

## Required Commands

Generate the private sample:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
```

Verify package integrity:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
```

Score predictions:

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

## Benchmark Boundary

Solvers may use arbitrary local computation and write their own analysis code,
but may inspect only files inside `solver_bundle`. They may not inspect
`generator.py`, `verifier.py`, `scorer.py`, `gold_private_sample.jsonl`,
`private_audit_traces.jsonl`, validation reports, hidden seeds, or any other
private package file.

## Human Baseline Plan

Qualified humans are software engineers comfortable with byte encodings,
checksums, and small search scripts. The intended protocol is 30 items in 90
minutes, with the same solver bundle and local computation allowed. The target
MVP solvability gate is at least 75% mean accuracy for qualified humans after a
short practice item, with item-level notes recorded for ambiguous traces.

## Quality Notes

The public generator creates reproducible samples from a seed, but generated
gold and audit traces are private for a run. The solver-visible bundle contains
no answers or source code. The verifier checks schema, id coverage, answer
format, duplicate packets, and obvious answer leakage through examples.

