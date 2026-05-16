# Solver Bundle

This bundle contains only the public inputs needed by a solver.

## Contents

- `items_private_sample.jsonl`: one row per item with `id`, `image`, and `prompt`.
- `images/`: ASCII PPM images referenced from the items file.
- `SOLVER_MANIFEST.json`: bundle metadata.

## Task

For each item, inspect the image and answer which badge label owns the visible surface exactly under the red crosshair. Valid answers are `A`, `B`, `C`, or `D`.

## Output contract

Return predictions as JSON Lines with exactly:

```json
{"id":"tile_provenance_000","answer":"A"}
```

Do not add extra keys.
