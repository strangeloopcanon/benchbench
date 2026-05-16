# Folded Strip Order (FSO) v1 — Solver Packet

## Task
Each item is a PNG image in `items/`. The image shows a single folded paper strip with:
- A **START** marker (green ring)
- An **END** marker (red ring)
- Several labeled visible segments on the strip (letters in white rounded boxes)

Your job: infer the **true order** of the labeled segments encountered when traversing the strip from START to END.

## Output format
Write `predictions.jsonl` with one JSON object per line:
```json
{"id":"<item id>","answer":"<label string>"}
```
Where `answer` is the labels as a single string with no separators (e.g. `ABCDE`).

## Important notes
- The 2D left-to-right or nearest-neighbor adjacency in the image is *not* reliable: folds, crossings, and occluders are intentional.
- The strip texture is continuous along the strip and provides the auditable cue for adjacency across folds.
