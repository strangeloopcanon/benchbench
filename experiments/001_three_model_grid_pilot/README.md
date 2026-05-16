# Experiment 001: Three-Model Grid Pilot

This folder preserves the first complete BenchBench pilot grid.

## What It Tested

- Creator models: GPT-5.2, GPT-5.4, GPT-5.5 through Codex.
- Solver models: GPT-5.2, GPT-5.4, GPT-5.5 through Codex.
- Creator prompt style: influenced by the prior Visual Trace success, which
  pulled candidates toward visual/topology benchmarks.

## Main Result

Only the GPT-5.4-created benchmark passed the difficulty gate.

| creator | benchmark | solver GPT-5.2 | solver GPT-5.4 | solver GPT-5.5 | status |
|---|---|---:|---:|---:|---|
| GPT-5.2 | Folded Strip Order | 16/30 | 14/30 | 19/30 | too easy |
| GPT-5.4 | Occluded Tile Provenance | 7/30 | 4/30 | 5/30 | passed |
| GPT-5.5 | Shadow Weave Topology | 15/30 | 24/30 | 26/30 | too easy |

Extra sanity check: GPT-5.5 at `xhigh` scored 10/30 on GPT-5.4's candidate.

## Files

- `experiment_summary_three_model_grid_20260515.md`: final interpretation.
- `experiment_summary_two_model_sweep_20260515.md`: earlier two-model sweep.
- `run/`: full run artifacts, candidates, solver outputs, score JSONs, and logs.

## Caveat

This pilot was useful, but the prompt had a visual/topology attractor. The next
experiment should ask for the best possible benchmark in the broadest terms,
provide only benchmark landscape context and prior results, and avoid nudging
toward any specific domain or modality.

