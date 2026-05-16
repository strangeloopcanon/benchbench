# Broad BenchBench Sweep

This run used the broad creator prompt: creators saw benchmark landscape notes and prior pilot outcomes, but were not directed toward any specific domain or modality.

Run root: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653`
Creator models: `gpt-5.2, gpt-5.4, gpt-5.5`
Solver models: `gpt-5.2, gpt-5.4, gpt-5.5`
Creator effort: `low`
Solver effort: `low`

## Candidates

### gpt-5.2: IgnoreSense

- Candidate: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_2`
- Validated: `True`
- Bundle files: `3`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Leak scan matches: `0`

### gpt-5.4: Spectrum Assembly with Side Constraints

- Candidate: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_4`
- Validated: `True`
- Bundle files: `3`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Leak scan matches: `0`

### gpt-5.5: Protocol Archaeology

- Candidate: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/002_broad_sweep_20260515_220653/run/candidate_created_by_gpt_5_5`
- Validated: `True`
- Bundle files: `3`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Leak scan matches: `5`

## Solver Grid

| creator | benchmark | solver GPT-5.2 | solver GPT-5.4 | solver GPT-5.5 | max score | status |
|---|---|---:|---:|---:|---:|---|
| gpt-5.2 | IgnoreSense | 4/30 | 7/30 | 7/30 | 7/30 | hardness pass; novelty unmeasured |
| gpt-5.4 | Spectrum Assembly with Side Constraints | 30/30 | 30/30 | 30/30 | 30/30 | too easy |
| gpt-5.5 | Protocol Archaeology | 0/30 | 0/30 | 0/30 | 0/30 | hardness pass; solvability unresolved |

## Calls

| phase | creator | solver/model | rows | score | tokens | returncode |
|---|---|---:|---:|---:|---:|---:|
| creator | gpt-5.2 | gpt-5.2 |  | NA | 61345 | 0 |
| creator | gpt-5.4 | gpt-5.4 |  | NA | 125106 | 0 |
| creator | gpt-5.5 | gpt-5.5 |  | NA | 56855 | 0 |
| solver | gpt-5.2 | gpt-5.2 | 30 | 4/30 | 28947 | 0 |
| solver | gpt-5.2 | gpt-5.4 | 30 | 7/30 | 44915 | 0 |
| solver | gpt-5.2 | gpt-5.5 | 30 | 7/30 | 40481 | 0 |
| solver | gpt-5.4 | gpt-5.2 | 30 | 30/30 | 32305 | 0 |
| solver | gpt-5.4 | gpt-5.4 | 30 | 30/30 | 44526 | 0 |
| solver | gpt-5.4 | gpt-5.5 | 30 | 30/30 | 71656 | 0 |
| solver | gpt-5.5 | gpt-5.2 | 30 | 0/30 | 45922 | 0 |
| solver | gpt-5.5 | gpt-5.4 | 30 | 0/30 | 82324 | 0 |
| solver | gpt-5.5 | gpt-5.5 | 30 | 0/30 | 65331 | 0 |

Total reported tokens: `699713`
