# Anticipated Failure Modes

## Why naive shortcuts fail

1. Local texture classification fails because every piece body uses the same fill and outline treatment.
2. Nearest-badge heuristics fail because the probe is often far from the owning badge and spatially closer to another piece's badge.
3. Largest-visible-region heuristics fail because the owning piece can be mostly hidden yet still own the queried patch.
4. Connected-component tracing on the final visible raster fails because one physical piece can appear as multiple disconnected visible islands after occlusion.

## Expected solver breakdowns

1. Solvers that crop around the crosshair and classify from local evidence will guess.
2. Solvers that rely on OCR plus nearest geometry will overfit to badge proximity.
3. Solvers that segment visible components without amodal completion will confuse ownership after pieces are split by overlaps.
4. Solvers that assume a single continuous visible path from badge to probe will fail on deliberately fragmented pieces.

## Why this is distinct from prior benchmarks

This benchmark is not a line-following or endpoint-connection task. The object of reasoning is region provenance under occlusion: which hidden same-texture tile owns a visible patch. The solver must infer latent object continuity from partial region geometry rather than follow a single visible cord or read rich document text.
