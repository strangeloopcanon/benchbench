# Expected failure modes

## Common wrong shortcut: 2D adjacency
- Models often treat the strip as a 2D path and order labels by left-to-right reading order, nearest Euclidean neighbors, or “looks connected” in the image plane.
- This is intentionally unreliable: folds and crossings cause distant points along the strip to appear adjacent, and occluders hide joints.

## Texture continuity is brittle for current vision models
- The correct cue is continuity of the strip texture at the ends of visible segments.
- Small mismatches, partial occlusion, and high-frequency patterns are error-prone for model perception.

## Over-weighting markers
- START/END rings are salient; models may anchor on them and then “walk” using 2D geometry rather than strip texture continuity.

## Confusing label boxes with cut points
- Labels are drawn on top of the strip; they are *not* guaranteed to coincide with fold boundaries.
- Solvers sometimes infer that each label is a separate strip piece.

## Failure under crossings
- Where the strip crosses itself, the apparent layering and occluders make it easy to flip the traversal direction or swap local order.

