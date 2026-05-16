# Occluded Tile Provenance

`Occluded Tile Provenance` is a 30-item visual reasoning benchmark. Each item shows four same-texture cardboard pieces with badge labels `A` to `D`. A red crosshair marks a visible surface patch. The solver must identify which labeled piece owns the surface exactly under the crosshair.

The intended difficulty comes from amodal completion under occlusion:

- All piece bodies share the same surface texture.
- Identity is only exposed through small colored badges near tabs.
- Visible regions of one piece are often split into multiple disconnected islands.
- Cheap local extraction is unreliable because the correct answer depends on topology, not local appearance.

## Files

- `generator.py`: deterministic benchmark generator.
- `verifier.py`: structure and leakage checks for the solver bundle against gold.
- `scorer.py`: exact-match scorer.
- `gold_private_sample.jsonl`: private answers for the required 30-item sample.
- `solver_bundle/`: public-facing solver package with images and item prompts.
- `validation_report.md`: generation, verification, scoring, baseline, and leakage notes.
- `failure_modes.md`: why the benchmark should remain difficult.

## Required commands

```bash
/Users/rohit/.pyenv/versions/global_env/bin/python generator.py --sample-count 30 --seed 20260516 --out-dir .
/Users/rohit/.pyenv/versions/global_env/bin/python verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
/Users/rohit/.pyenv/versions/global_env/bin/python scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

## Answer format

Prediction rows must be JSON Lines with exactly:

```json
{"id":"tile_provenance_000","answer":"A"}
```
