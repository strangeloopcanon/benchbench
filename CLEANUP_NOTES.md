# Cleanup Notes

Cleanup date: 2026-05-16

## Preserved

- Both 3-model result runs:
  - `experiments/001_three_model_grid_pilot`
  - `experiments/002_broad_sweep_20260515_220653`
- Candidate benchmark packages for those runs.
- Score JSONs, solver predictions, prompts, summaries, and manifests.
- `benchmark_landscape`, including eval catalog and score matrices.
- Legacy scripts and development summary notes.

## Removed

- Duplicate `isolated_solver_*` working directories from canonical runs.
- Old generated run payloads under `experiments/000_development_archive/runs`.
- Empty top-level `runs` folder.

The removed folders were generated execution workspaces or superseded
exploratory payloads, not the canonical notes or candidate packages.
