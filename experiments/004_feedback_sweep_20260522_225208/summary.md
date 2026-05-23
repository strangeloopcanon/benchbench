# Broad BenchBench Sweep

This run used the broad creator prompt plus a prior-run failure report: creators saw benchmark landscape notes, prior pilot outcomes, and feedback on how the previous candidates broke.

Run root: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/004_feedback_sweep_20260522_225208`
Creator models: `gpt-5.2, gpt-5.4, gpt-5.5, gemini-3.1-pro, gemini-3.5-flash-high`
Solver models: `gpt-5.2, gpt-5.4, gpt-5.5, gemini-3.1-pro, gemini-3.5-flash-high`
Creator effort: `low`
Solver effort: `low`
Creator feedback context: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/003_five_model_sweep_20260522_195526/feedback_for_next_sweep.md`
Solvability audit: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/004_feedback_sweep_20260522_225208/solvability_audit.md`

Antigravity rows use the current selected `agy` model and are checked against the selected-model label in the CLI log when a specific Gemini label is requested.

## Candidates

### gpt-5.2: Reimbursement Forensics (ReiFor)

- Candidate: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/004_feedback_sweep_20260522_225208/run/candidate_created_by_gpt_5_2`
- Validated: `True`
- Bundle files: `65`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Leak scan matches: `1`

### gpt-5.4: release_packet_arbitration

- Candidate: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/004_feedback_sweep_20260522_225208/run/candidate_created_by_gpt_5_4`
- Validated: `True`
- Bundle files: `184`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Leak scan matches: `0`

### gpt-5.5: Cross-Document Obligation Resolution

- Candidate: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/004_feedback_sweep_20260522_225208/run/candidate_created_by_gpt_5_5`
- Validated: `True`
- Bundle files: `33`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Leak scan matches: `7`

### Gemini 3.1 Pro (High): Corrupted LZ77 Recovery

- Candidate: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/004_feedback_sweep_20260522_225208/run/candidate_created_by_gemini_3_1_pro`
- Validated: `True`
- Bundle files: `34`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Leak scan matches: `0`

### Gemini 3.5 Flash (High): MFN-Cascade

- Candidate: `/Users/rohit/Documents/Workspace/Coding/benchbench/experiments/004_feedback_sweep_20260522_225208/run/candidate_created_by_gemini_3_5_flash_high`
- Validated: `True`
- Bundle files: `12`
- Gold control: `{"accuracy": 1.0, "correct": 30, "total": 30}`
- Shifted-wrong control: `{"accuracy": 0.0, "correct": 0, "total": 30}`
- Leak scan matches: `0`

## Solver Grid

| creator | benchmark | solver gpt-5.2 | solver gpt-5.4 | solver gpt-5.5 | solver Gemini 3.1 Pro (High) | solver Gemini 3.5 Flash (High) | max score | status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| gpt-5.2 | Reimbursement Forensics (ReiFor) | 10/30 | 14/30 | 11/30 | 12/30 | 11/30 | 14/30 | accept |
| gpt-5.4 | release_packet_arbitration | 27/30 | 25/30 | 27/30 | 0/30 | 27/30 | 27/30 | reject |
| gpt-5.5 | Cross-Document Obligation Resolution | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 | scoring_contract_failure |
| Gemini 3.1 Pro (High) | Corrupted LZ77 Recovery | 0/30 | 22/30 | 17/30 | 0/30 | 0/30 | 22/30 | reject |
| Gemini 3.5 Flash (High) | MFN-Cascade | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 | reject |

Post-run audit: GPT-5.5's all-zero row is not evidence of an
externally-unsolvable task. Every solver recovered all 30 notification dates,
but the scorer required exact private labels for `evidence_codes` and related
categorical values that the public packet did not enumerate. Gemini 3.1 Pro's
Corrupted LZ77 Recovery is not unsolvable because GPT-5.4 recovered 22/30 and
GPT-5.5 recovered 17/30; its weak cells are mostly blank outputs, no parsed
rows, or timeout behavior.

## Calls

| phase | creator | solver/model | rows | score | tokens | returncode |
|---|---|---:|---:|---:|---:|---:|
| solver | gpt-5.2 | gpt-5.2 | 30 | 10/30 | 34842 | 0 |
| solver | gpt-5.2 | gpt-5.4 | 30 | 14/30 | 94547 | 0 |
| solver | gpt-5.2 | gpt-5.5 | 30 | 11/30 | 61724 | 0 |
| solver | gpt-5.2 | Gemini 3.1 Pro (High) | 30 | 12/30 | 0 | 0 |
| solver | gpt-5.2 | Gemini 3.5 Flash (High) | 30 | 11/30 | 0 | 0 |
| solver | gpt-5.5 | gpt-5.2 | 30 | 0/30 | 32132 | 0 |
| solver | gpt-5.5 | gpt-5.4 | 30 | 0/30 | 100939 | 0 |
| solver | gpt-5.5 | gpt-5.5 | 30 | 0/30 | 81319 | 0 |
| solver | gpt-5.5 | Gemini 3.1 Pro (High) | 30 | 0/30 | 0 | 0 |
| solver | gpt-5.5 | Gemini 3.5 Flash (High) | 30 | 0/30 | 0 | 0 |
| solver | gemini-3.1-pro | gpt-5.2 | 30 | 0/30 | 46357 | 0 |
| solver | gemini-3.1-pro | gpt-5.4 | 30 | 22/30 | 173447 | 0 |
| solver | gemini-3.1-pro | gpt-5.5 | 30 | 17/30 | 137792 | 0 |
| solver | gemini-3.1-pro | Gemini 3.1 Pro (High) | 0 | 0/30 | 0 | 0 |
| solver | gemini-3.1-pro | Gemini 3.5 Flash (High) | 0 | 0/30 | 0 | -124 |
| solver | gpt-5.4 | gpt-5.2 | 30 | 27/30 | 57994 | 0 |
| solver | gpt-5.4 | gpt-5.4 | 30 | 25/30 | 150167 | 0 |
| solver | gpt-5.4 | gpt-5.5 | 30 | 27/30 | 53275 | 0 |
| solver | gpt-5.4 | Gemini 3.1 Pro (High) | 30 | 0/30 | 0 | 0 |
| solver | gpt-5.4 | Gemini 3.5 Flash (High) | 30 | 27/30 | 0 | 0 |
| solver | gemini-3.5-flash-high | gpt-5.2 | 30 | 30/30 | 50261 | 0 |
| solver | gemini-3.5-flash-high | gpt-5.4 | 30 | 30/30 | 63939 | 0 |
| solver | gemini-3.5-flash-high | gpt-5.5 | 30 | 30/30 | 85696 | 0 |
| solver | gemini-3.5-flash-high | Gemini 3.1 Pro (High) | 30 | 30/30 | 0 | 0 |
| solver | gemini-3.5-flash-high | Gemini 3.5 Flash (High) | 30 | 30/30 | 0 | 0 |

Total reported tokens: `1224431`
