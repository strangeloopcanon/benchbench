# Experiments

This folder keeps the BenchBench run history at three levels.

## Canonical Runs

### `001_three_model_grid_pilot`

The first complete 3-model grid. It is worth keeping because it showed the
visual/topology attractor in early prompts.

Headline:

| creator | benchmark | result |
|---|---|---|
| GPT-5.2 | Folded Strip Order | too easy |
| GPT-5.4 | Occluded Tile Provenance | difficulty pass in this pilot |
| GPT-5.5 | Shadow Weave Topology | too easy |

### `002_broad_sweep_20260515_220653`

The first broad prompt 3-model sweep. It is worth keeping because it produced
three qualitatively different benchmark families without explicit domain
steering.

Headline:

| creator | benchmark | result |
|---|---|---|
| GPT-5.2 | IgnoreSense | hard under tested solvers; novelty not established |
| GPT-5.4 | Spectrum Assembly | too easy |
| GPT-5.5 | Protocol Archaeology | hard under tested solvers; solvability/identifiability unresolved |

## Development Archive

`000_development_archive` keeps notes from earlier prompt iterations. Generated
run payloads from that phase are not canonical.

## Cleanup Policy

For canonical runs, keep:

- summary and assessment markdown;
- manifests;
- creator prompts and outputs;
- candidate benchmark packages;
- score JSONs and solver predictions.

Generated isolated solver working directories may be deleted after the
corresponding predictions and score files are preserved.
