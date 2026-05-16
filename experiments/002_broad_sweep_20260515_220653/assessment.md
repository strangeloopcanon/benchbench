# Experiment 002 Assessment: Broad BenchBench Sweep

## What Changed

This run removed the visual/topology nudge from Experiment 001.

Creators saw:

- the benchmark landscape notes;
- the previous pilot result;
- package validity requirements.

Creators did not get a list of suggested benchmark domains or modalities.

That worked. The three models did not all make visual puzzles:

| creator | benchmark | broad type |
|---|---|---|
| GPT-5.2 | IgnoreSense | self-contained software spec / `.gitignore` semantics |
| GPT-5.4 | Spectrum Assembly with Side Constraints | combinatorial constrained reconstruction |
| GPT-5.5 | Protocol Archaeology | trace-based reverse engineering / program induction |

## Solver Results

Main low-effort grid:

| creator | benchmark | solver GPT-5.2 | solver GPT-5.4 | solver GPT-5.5 | verdict |
|---|---|---:|---:|---:|---|
| GPT-5.2 | IgnoreSense | 4/30 | 7/30 | 7/30 | passes difficulty |
| GPT-5.4 | Spectrum Assembly | 30/30 | 30/30 | 30/30 | too easy |
| GPT-5.5 | Protocol Archaeology | 0/30 | 0/30 | 0/30 | passes difficulty; solvability unresolved |

GPT-5.5 `xhigh` sanity checks on the two surviving candidates:

| creator | benchmark | GPT-5.5 xhigh score |
|---|---|---:|
| GPT-5.2 | IgnoreSense | 7/30 |
| GPT-5.5 | Protocol Archaeology | 0/30 |

## Plain-English Finding

The broad prompt produced a better BenchBench experiment.

The models stopped clustering around visual puzzles and instead explored
software-spec correctness, combinatorial reconstruction, and black-box protocol
inference. That is much closer to the actual BenchBench idea: model-generated
benchmark R&D, not model-generated visual puzzles.

Two candidates survived the first solver attack, but that is not the same as
final acceptance:

- `IgnoreSense` looks like a useful generated benchmark candidate.
- `Protocol Archaeology` is the most frontier-resistant under this solver grid,
  but may be under-specified or too hard unless a separate audit shows that the
  public packet identifies the answer.

`Spectrum Assembly` failed because all solvers solved it perfectly. It looked
formal and difficult, but the constraints were explicit enough that agents could
write the right search.

## Qualitative Assessment By Creator

### GPT-5.2: IgnoreSense

This is a `.gitignore`-style semantics benchmark. Each item gives rules and
paths; the solver must classify which paths are ignored.

Closest existing evals:

- LiveCodeBench and SWE-bench, because success requires implementing a precise
  software behavior.
- Parser/spec-following tasks, because the difficulty is in edge-case semantics.

Why it is interesting:

- It is not visual.
- It is not factual recall.
- It tests a real engineering failure mode: models often understand a spec
  locally but mishandle precedence, negation, anchoring, escaping, and glob
  edge cases.
- It stayed hard even for GPT-5.5 at `xhigh`.

Main concern:

- It may correlate strongly with coding/spec-implementation benchmarks. That
  is not bad, but it means novelty has to be measured, not assumed.

Assessment:

`IgnoreSense` is a practical candidate from the broad run, but it still needs
broader solver coverage and novelty analysis before any larger claim.

### GPT-5.4: Spectrum Assembly With Side Constraints

This is a generated reconstruction puzzle: recover a hidden string from
overlapping k-grams and global constraints.

Closest existing evals:

- Algorithmic reasoning and constraint-solving tasks.
- Competitive-programming-style search problems.
- Formal puzzle benchmarks.

Why it failed:

- The problem statement exposes the right abstraction.
- Once the solver frames it as search/constraint satisfaction, it is fully
  mechanizable.
- All three solvers got 30/30.

Assessment:

Valid but not BenchBench-useful. It demonstrates an important failure mode for
benchmark creators: formal-looking does not mean hard if the exact solver is
obvious.

### GPT-5.5: Protocol Archaeology

This is a trace-based reverse-engineering benchmark. Each item gives observed
input/output byte-packet examples and asks for the response to a new packet.

Closest existing evals:

- Program induction / rule induction tasks.
- Reverse engineering and debugging tasks.
- SWE-bench/LiveCodeBench only distantly, because no source code or natural
  language algorithm is given.

Why it is interesting:

- It is not visual.
- It is not ordinary coding.
- It asks for inference from traces, a real-world agentic skill.
- All solvers, including GPT-5.5 at `xhigh`, scored 0/30.

Main concern:

- A 0/30 wall may mean the task is too underdetermined or too hard to be a good
  leaderboard benchmark.
- It needs a human or specialist baseline. If qualified engineers can solve it
  with the same visible traces, it is very interesting. If they cannot, it is
  just a hard wall.

Assessment:

`Protocol Archaeology` is the most ambitious candidate, but it needs a separate
solvability and identifiability audit before being called good.

Later note: a public-bundle-only specialist expression-search sanity check also
scored 0/30. That does not settle the benchmark's status, but it strengthens the
concern that the current public packet may not specify enough structure. See
`protocol_archaeology_audit_note.md`.

## Similarity / Novelty Assessment

Qualitatively:

- `IgnoreSense` is adjacent to coding/spec benchmarks, but narrower and more
  semantically adversarial.
- `Spectrum Assembly` is close to algorithmic puzzle/search tasks and appears
  redundant for strong tool-using agents.
- `Protocol Archaeology` is closest to program induction and black-box reverse
  engineering, which is less represented in mainstream LLM eval baskets than
  code repair, math, OCR, or static QA.

But qualitative similarity is not enough. The proper measurement remains the
predictor test:

```text
new_benchmark_score(model)
  ~ existing_eval_scores(model)
```

Then:

```text
predictive_novelty = 1 - cross_validated_R2
```

What we need next:

1. Run more solver points, not just GPT-5.2/5.4/5.5.
2. Include smaller models, non-Codex chat/vision models where relevant, and
   simple specialist baselines.
3. Collect existing benchmark scores or proxy mini-evals for those same solvers.
4. Test whether `IgnoreSense` or `Protocol Archaeology` scores are predictable
   from coding, reasoning, tool-use, and agent benchmarks.

Interpretation:

- If `IgnoreSense` is mostly predicted by coding benchmarks, it is a useful
  coding/spec sub-benchmark but not a new axis.
- If it is poorly predicted, it may measure a real residual skill:
  edge-case formal semantics under tool use.
- If `Protocol Archaeology` remains 0 for everyone, it is not analyzable as a
  leaderboard yet.
- If humans or specialist baselines solve it while general agents fail, it may
  be the stronger new axis.

## What This Means For BenchBench

The broad creator prompt is better than the visual-attractor prompt.

The core acceptance logic should be:

1. Let the creator search freely.
2. Validate package correctness and leakage.
3. Let solvers use tools aggressively.
4. Reject benchmarks that are solved too easily.
5. Flag benchmarks that no one can solve as "needs solvability baseline", not
   automatic wins.
6. Measure novelty by predictability from existing eval scores.

Experiment 002 gives two unresolved benchmark candidates:

- `IgnoreSense`: practical and hard under the tested solvers, with novelty still
  unmeasured.
- `Protocol Archaeology`: potentially deeper, but requires a separate
  human/specialist solvability and identifiability audit.
