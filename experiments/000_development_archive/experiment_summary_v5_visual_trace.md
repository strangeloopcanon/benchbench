# BenchBench V5: Visual Trace Cords

## Result

This run produced a benchmark that GPT-5.5+Codex did not solve.

- Benchmark: `Visual Trace Cords`
- Creator model: GPT-5.5 via `codex exec`
- Blind solver model: GPT-5.5 via `codex exec`
- Creator token use: 164,905
- Blind solver token use: 562,149
- Blind solver score: 0/30, accuracy 0.0
- BenchBench threshold: passed for this local Codex track, because the tested frontier solver scored below 50%.

## What Changed From Earlier Attempts

Earlier candidates were valid but reducible to text parsing, OCR, web lookup,
or deterministic program synthesis. V4 in particular built a richer document
packet task, but GPT-5.5+Codex still solved it 30/30 by turning the packet into
machine-readable evidence.

V5 used that failure evidence directly and changed the residual capability. It
asks for visual topology reconstruction from raster-only images:

- each item is a PNG board, not a text or vector artifact;
- the solver sees only `README.md`, `SOLVER_MANIFEST.json`, JSONL item rows, and 30 PNG images;
- the hidden generator, coordinates, topology traces, seed, verifier, scorer, and gold answers are outside the solver bundle;
- the task is to start at a green ring and follow the same physical black cord through over-under crossings, pale occluders, jitter, and decoy fragments to a right-edge exit label.

## Benchmark Package

Candidate root:

`/Users/rohit/Documents/Codex/2026-05-14/can-we-also-make-a-benchbench/runs/gpt55_benchbench_v5_visual_trace_20260515_1220/candidate_visual_trace`

Key files:

- `README.md`
- `benchmark_spec.json`
- `generator.py`
- `verifier.py`
- `scorer.py`
- `gold_private_sample.jsonl`
- `private_audit_trace_sample.jsonl`
- `solver_bundle/`
- `validation_report.md`
- `failure_modes.md`
- `adversarial_selection_report.md`
- `predictions_solver.jsonl`
- `score_solver.json`

The solver bundle contains exactly 33 files:

- 1 README
- 1 manifest JSON
- 1 item JSONL file
- 30 PNG assets

## Validation

The creator validation passed. I reran the verifier locally with `python`
because this shell's `python3` did not have Pillow available.

Verifier stats:

- items: 30
- PNG assets: 30
- full-board crossing count: 38 to 52
- target-cord crossing count: 17 to 32
- answer distribution balanced: no label appears more than 3 times

Controls and weak baselines:

- gold control: 30/30
- wrong control: 0/30
- constant `EXIT:A2`: 3/30
- deterministic random-label baseline: 1/30
- item-id hash baseline: 5/30
- private ignore-crossings shortcut baseline: 0/30

The independent leakage scan reported no solver-bundle matches for private
source names, coordinate fields, seeds, topology traces, solution terms, or
concrete gold answer strings.

## Blind Solver Behavior

The blind GPT-5.5+Codex solver spent 562,149 tokens and attempted a serious
computer-vision solution:

- read the visible bundle only;
- used local image libraries and OCR;
- built label crops and heuristics;
- skeletonized black strokes;
- tried to repair crossing gaps and trace through occluders;
- manually parameter-swept several uncertain items.

The final predictions scored:

```json
{
  "accuracy": 0.0,
  "correct": 0,
  "total": 30
}
```

The zero was not a JSONL or id mismatch: 30 final rows were extracted and scored
against matching gold ids. The solver's predictions matched the private
ignore-crossings shortcut on 27/30 items, which explains the failure. It mostly
followed visually continuous/skeletonized paths where the actual task required
respecting over-under topology.

## Interpretation

This is the first run in the sequence that actually satisfies the desired
BenchBench evidence target for GPT-5.5+Codex in the local terminal setting. The
key move was not simply making the task harder; it was making the obvious
automation path anticorrelated with the true answer.

The caveat is important: this tests GPT-5.5 as a Codex terminal agent over local
raster files, not a native high-resolution multimodal model shown the images
directly. A proper next step would run the same solver bundle through a native
vision-capable model, but for the stated Codex benchmark-creator loop, this is a
clean break.

## Prompt Lesson

The creator prompt should explicitly ask models to:

- use previous failed BenchBench runs as negative evidence;
- avoid tasks reducible to text, OCR, public lookup, regexes, source inspection, or deterministic program synthesis;
- construct solver-visible artifacts without hidden structured source;
- adversarially test cheap baselines and select examples where the cheap
  shortcut is wrong;
- prefer residual capabilities that current evals under-cover, especially ones
  where mechanizable approximations are anticorrelated with the target behavior;
- keep a private audit trail so the benchmark remains verifiable even when the
  public solver bundle is raster-only or otherwise lossy.

