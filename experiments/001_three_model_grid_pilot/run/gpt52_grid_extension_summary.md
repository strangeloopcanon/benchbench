# GPT-5.2 Grid Extension

Run root: `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811`

## GPT-5.2 Creator

- Candidate: `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811/candidate_created_by_gpt_5_2`
- Validated: `True`
- Bundle files: `33`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Leak scan matches: `0`

## 3x3 Solver Grid

| creator | solver gpt-5.2 | solver gpt-5.4 | solver gpt-5.5 |
|---|---:|---:|---:|
| gpt-5.2 | 16/30 | 14/30 | 19/30 |
| gpt-5.4 | 7/30 | 4/30 | 5/30 |
| gpt-5.5 | 15/30 | 24/30 | 26/30 |

## New Solver Calls

| creator | solver | rows | correct | total | accuracy | tokens | returncode |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.2 | gpt-5.2 | 30 | 16 | 30 | 0.5333333333333333 | 185006 | 0 |
| gpt-5.2 | gpt-5.4 | 30 | 14 | 30 | 0.4666666666666667 | 161499 | 0 |
| gpt-5.2 | gpt-5.5 | 30 | 19 | 30 | 0.6333333333333333 | 154150 | 0 |

Solver effort for added cells: `low`
Total new solver tokens: `500655`

