# BenchBench Two-Model Sweep: GPT-5.4 and GPT-5.5

## Setup

Run root:

`/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811`

The sweep used Codex for both creator and solver phases.

- Creator models: `gpt-5.4`, `gpt-5.5`
- Creator effort: `low`
- Solver models: `gpt-5.4`, `gpt-5.5`
- Solver effort for the full 2x2 matrix: `low`
- Additional sanity cell: `gpt-5.5` at `xhigh` on the better candidate

I initially tried broader/higher-effort creator and solver settings. GPT-5.4
spent a long time in pre-action reasoning without writing artifacts, so I
restarted with narrower "build here now" creator prompts and low-effort solvers
to obtain a complete operational sweep. The extra `xhigh` GPT-5.5 sanity check
was run on the candidate that looked strongest.

## Candidate 1: GPT-5.4 Creator

Benchmark: `Occluded Tile Provenance`

Task: each item is a raster PPM image with four same-texture cardboard pieces
labelled A-D. A red crosshair marks a visible patch. The solver must identify
which labeled piece owns the surface under the crosshair.

Validation:

- Controller validation: passed
- Items: 30
- Solver bundle: 33 files
- Gold control: 30/30
- Shifted-wrong control: 0/30
- Note: the controller leak scan flagged words like `solution` and `seed` in
  `SOLVER_MANIFEST.json`, but inspection showed these were only in a
  `prohibited_contents` list, not leaked answers or seeds.

Low-effort solver matrix:

| solver | score |
|---|---:|
| GPT-5.4+Codex | 4/30 |
| GPT-5.5+Codex | 5/30 |

Extra stronger check:

| solver | effort | score | tokens |
|---|---:|---:|---:|
| GPT-5.5+Codex | xhigh | 10/30 | 598,030 |

This candidate passed the BenchBench difficulty threshold in every completed
solver condition, including the `xhigh` GPT-5.5 check.

## Candidate 2: GPT-5.5 Creator

Benchmark: `Shadow Weave Topology`

Task: each item is a raster PNG image with six labeled paper strips and four
probe rings. The solver must return the top visible strip at probes A-D as a
four-character label string.

Validation:

- Controller validation: passed
- Items: 30
- Solver bundle: 33 files
- Gold control: 30/30
- Shifted-wrong control: 0/30
- Controller leak scan: no matches

Low-effort solver matrix:

| solver | score |
|---|---:|
| GPT-5.4+Codex | 24/30 |
| GPT-5.5+Codex | 26/30 |

This candidate failed the BenchBench difficulty threshold because both solvers
beat 50% easily.

## Main Score Matrix

| creator | benchmark | solver | effort | score | accuracy |
|---|---|---:|---:|---:|---:|
| GPT-5.4+Codex | Occluded Tile Provenance | GPT-5.4+Codex | low | 4/30 | 0.133 |
| GPT-5.4+Codex | Occluded Tile Provenance | GPT-5.5+Codex | low | 5/30 | 0.167 |
| GPT-5.4+Codex | Occluded Tile Provenance | GPT-5.5+Codex | xhigh | 10/30 | 0.333 |
| GPT-5.5+Codex | Shadow Weave Topology | GPT-5.4+Codex | low | 24/30 | 0.800 |
| GPT-5.5+Codex | Shadow Weave Topology | GPT-5.5+Codex | low | 26/30 | 0.867 |

## Interpretation

The sweep produced one strong candidate and one too-easy candidate.

The GPT-5.4-created benchmark is the winner in this sweep. It appears to have
captured the same useful BenchBench principle as Visual Trace Cords: a visually
plausible shortcut can be systematically misleading. Even GPT-5.5+Codex at
`xhigh` only reached 10/30.

The GPT-5.5-created benchmark was valid and visually polished, but the task
mostly reduced to reading local top-layer evidence at probe points. That was too
tractable for the solver models.

The lesson is that "visual topology" alone is not enough. The benchmark needs an
anticorrelated shortcut. `Shadow Weave Topology` had visible local cues that the
solvers could exploit. `Occluded Tile Provenance` forced amodal object
ownership through occlusion, where local appearance and nearby labels were not
reliable.

## Caveats

- The full 2x2 matrix used low-effort solvers to finish the operational sweep.
- The stronger `xhigh` GPT-5.5 sanity check was run only on the stronger
  GPT-5.4-created candidate.
- These are Codex-agent/local-file results, not native multimodal chat results.
- Novelty versus existing evals has not yet been measured by the predictor
  method; this sweep only tests creator validity and solver difficulty.

## Artifacts

- GPT-5.4 candidate:
  `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811/candidate_created_by_gpt_5_4`
- GPT-5.5 candidate:
  `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811/candidate_created_by_gpt_5_5`
- Low-effort solver matrix:
  `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811/solver_sweep_high_summary.md`
- GPT-5.5 xhigh score on GPT-5.4 candidate:
  `/Users/rohit/Documents/Workspace/Coding/benchbench/runs/two_model_sweep_20260515_181811/candidate_created_by_gpt_5_4/score_solver_xhigh_gpt_5_5.json`

