# BenchBench Three-Model Grid: GPT-5.2, GPT-5.4, GPT-5.5

## Setup

Run root:

`/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811`

This extends the prior GPT-5.4/GPT-5.5 sweep by adding GPT-5.2 as both a
creator and solver.

- Creator models: `gpt-5.2`, `gpt-5.4`, `gpt-5.5`
- Solver models: `gpt-5.2`, `gpt-5.4`, `gpt-5.5`
- Creator effort for GPT-5.2: `low`
- Solver effort for the 3x3 grid: `low`
- Extra prior sanity cell: GPT-5.5 `xhigh` on GPT-5.4's candidate

## Candidates

### GPT-5.2 Creator: Folded Strip Order

GPT-5.2 created `Folded Strip Order`, a raster-only benchmark where each image
shows a folded paper strip with START/END markers and visible labeled segments.
The answer is the true order of labels along the underlying strip.

Validation:

- Controller validation: passed after normalizing scorer output keys
- Items: 30
- Solver bundle: 33 files
- Gold control: 30/30
- Shifted-wrong control: 0/30
- Leak scan: clean

Solver scores:

- GPT-5.2: 16/30
- GPT-5.4: 14/30
- GPT-5.5: 19/30

This candidate is valid, but it fails the BenchBench difficulty threshold
because GPT-5.2 and GPT-5.5 both scored at or above 50%.

### GPT-5.4 Creator: Occluded Tile Provenance

GPT-5.4 created `Occluded Tile Provenance`, where solvers must identify which
same-texture object owns the visible patch under a crosshair.

Solver scores:

- GPT-5.2: 7/30
- GPT-5.4: 4/30
- GPT-5.5: 5/30
- GPT-5.5 xhigh sanity check: 10/30

This remains the strongest candidate. It stayed below the 50% threshold for all
three low-effort solvers and also for the extra GPT-5.5 `xhigh` check.

### GPT-5.5 Creator: Shadow Weave Topology

GPT-5.5 created `Shadow Weave Topology`, where solvers identify the top visible
strip at several probe rings.

Solver scores:

- GPT-5.2: 15/30
- GPT-5.4: 24/30
- GPT-5.5: 26/30

This candidate is valid but too easy. GPT-5.4 and GPT-5.5 solved it well above
the threshold.

## 3x3 Score Grid

Scores are correct answers out of 30.

| creator | solver GPT-5.2 | solver GPT-5.4 | solver GPT-5.5 | max solver score | BenchBench status |
|---|---:|---:|---:|---:|---|
| GPT-5.2 | 16/30 | 14/30 | 19/30 | 19/30 | reject: too easy |
| GPT-5.4 | 7/30 | 4/30 | 5/30 | 7/30 | accept in low-effort grid |
| GPT-5.5 | 15/30 | 24/30 | 26/30 | 26/30 | reject: too easy |

Extra robustness check:

| creator | solver | effort | score |
|---|---:|---:|---:|
| GPT-5.4 | GPT-5.5 | xhigh | 10/30 |

## What This Adds

GPT-5.2 successfully created a valid benchmark package, but not a strong enough
one. Its benchmark was plausible and visual, but the solvers could often recover
the strip order.

Adding GPT-5.2 makes the creator result clearer:

- GPT-5.2: valid creator, but benchmark too easy.
- GPT-5.4: valid creator, benchmark remains hard.
- GPT-5.5: valid creator, but benchmark too easy.

In this small grid, GPT-5.4 is the only creator whose benchmark survives the
BenchBench difficulty gate.

## Interpretation

The result is not "weaker models are better." The result is narrower:

The winning benchmark is the one where the solver's usual visual strategy points
at the wrong answer. GPT-5.4 found that with object ownership under occlusion.
GPT-5.2 and GPT-5.5 made visual/topological tasks, but they left enough local
visible evidence for solvers to do reasonably well.

So the current BenchBench criterion seems to be selecting for a specific creator
skill:

> Can the model design a valid task where plausible automation is misleading,
> not merely a task that looks visually complicated?

## Caveats

- The 3x3 grid used low-effort solver runs for comparability and cost control.
- The strongest extra check was only run for GPT-5.4's candidate: GPT-5.5 at
  `xhigh` still scored only 10/30.
- These are Codex-agent/local-file results, not native multimodal chat results.
- Novelty against existing evals still needs the predictor-style test discussed
  earlier.

## Artifacts

- GPT-5.2 extension summary:
  `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811/gpt52_grid_extension_summary.md`
- GPT-5.2 candidate:
  `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811/candidate_created_by_gpt_5_2`
- GPT-5.4 candidate:
  `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811/candidate_created_by_gpt_5_4`
- GPT-5.5 candidate:
  `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811/candidate_created_by_gpt_5_5`

