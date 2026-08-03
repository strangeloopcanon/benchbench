# Counterfeit Clock v1

Counterfeit Clock measures joint discrete model reconstruction and forensic
outlier repair. A solver must align two naming systems for five stations,
recover a bijection of modular clock rates and five offsets, match anonymous
packets within repeated routes, then identify and repair the only falsified
counter reading. Every fact needed to solve the instances is in the isolated
solver bundle.

The benchmark has 30 deterministic JSONL items. Each answer is a log record ID
and corrected modular tick. Exact accuracy is the primary score; the scorer
also reports the two answer components as diagnostics.

## Files

- `solver_bundle/`: the complete public packet and no private labels or code
- `gold_private_sample.jsonl`: exact gold rows (`id`, `answer` only)
- `generator.py`: deterministic sample generator
- `reference_core.py`: exhaustive public-constraint enumerator used for audit
- `verifier.py`: schema, integrity, and identifiability verification
- `scorer.py`: deterministic exact/component scoring
- `baseline.py`: deliberately weak largest-jump shortcut
- `score_report.json`: 30/30 gold self-score
- `baseline_score_report.json`: weak-baseline report

## Required commands

Run from this directory:

```sh
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
<local-home>/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none/bin/python3.12 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```

The implementation is standard-library-only and compatible with Python 3.9+
(including the required Python 3.12 target). Generator output is canonicalized
JSON and deterministic for a given count and seed.

## Prediction format

One row per item, with exactly `id` and `answer`:

```json
{"id":"CC-001","answer":{"record_id":"A-01","corrected_tick":42}}
```

Duplicate or unknown IDs and extra outer keys are errors. Missing IDs score
zero. An answer object with missing or extra fields is invalid for that item.
JSONL parsing rejects blank lines, duplicate object keys, and non-standard
constants such as `NaN`; IDs and answer scalar values are type-checked so JSON
booleans cannot be accepted as integer ticks.

## Capability and novelty

The closest established families are MuSR-style multi-source reasoning, GAIA
tool reasoning, and program-synthesis/constraint tasks in BIG-Bench Hard. It is
not a duplicate of any of them: the target is a compact, fully specified
distributed-systems identification problem whose coupled latent bijections,
modular arithmetic, and single-error correction admit a finite exhaustive
certificate. It does not require web knowledge, prose judgment, or visual
interpretation, and is unlike prior BenchBench visual/topology candidates.

The principal intended difficulty is constructing a correct joint solver, not
guessing hidden generator behavior. A solver may use any tools available to it
but may inspect only the isolated bundle.
