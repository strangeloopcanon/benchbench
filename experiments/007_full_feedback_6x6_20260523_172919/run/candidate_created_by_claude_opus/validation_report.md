# Validation Report

## Benchmark: Construction Progress Payment Certification (CPPC)

### 1. Determinism

The generator is fully deterministic given a seed. Running `python generator.py
--sample-count 30 --seed 20260516 --out-dir .` produces identical items and
gold answers on every invocation. Verified by the verifier which recomputes all
30 answers from item data and confirms exact match.

### 2. Scorer Correctness

- **Gold self-score**: 30/30 ✓
- **Type handling**: The scorer normalizes string representations of integers,
  handles comma-separated numbers, and strips `$` prefixes.
- **No type strictness trap**: Unlike prior benchmarks that failed because of
  JSON string-vs-integer mismatches, this scorer accepts both `123` and `"123"`
  and even `"$1,234"` → 1234.

### 3. External Solvability

**Claim**: A qualified external solver (human construction accountant or model
with tool access) can determine the correct answer for every item using only
the public solver bundle.

**Evidence**:

For each answer field, here is what public evidence identifies it:

| Data needed | Where in solver bundle |
|---|---|
| Computation sequence | `general_conditions.md` Article 13 (15 steps, fully specified) |
| Retention rate logic | `general_conditions.md` §7.2 (10% below 50%, 5% at/above 50%) |
| CO billing rates | `general_conditions.md` §8.3 (approved=100%, pending=50%, disputed=25%, rejected=0%) |
| Stored material conditions | `general_conditions.md` §7.4 (all three must be true) |
| LD formula | `general_conditions.md` §9.1 (days × rate, capped, excusable = $0) |
| Insurance deduction | `general_conditions.md` §10.2 (prorated overlap on work earned only) |
| Tax rules | `general_conditions.md` §11.1, §11.2 (materials only, exempt = $0) |
| Rounding convention | `general_conditions.md` §13.1 (banker's rounding, per-line) |
| All item data | `items_private_sample.jsonl` (complete structured data per item) |

**How an external solver could verify answers**:
1. Read General Conditions Article 13 for the exact computation sequence
2. For any item, manually follow the 15 steps using the item's JSON data
3. Each step involves either a lookup (retention rate from cumulative %), a
   conditional (excusable delay?), or arithmetic (multiplication, subtraction)
4. The entire computation is reproducible by hand calculator in ~10 minutes per item

**No hidden information**: The solver bundle contains all rules and all data.
There are no private keys, hidden seeds, generator tricks, or undocumented
rules. The `difficulty` tag is stripped from solver items (it was only used for
calibration during generation).

### 4. Answer Contract

- **Format**: Integer (cents). Example: `1234567` means $12,345.67.
- **Normalization**: Scorer accepts int, float (if .0), or string representation.
- **No private labels**: The answer is a single number derived entirely from
  public rules and public data.
- **No ambiguity**: Each item has exactly one correct answer given the stated
  rules and rounding convention.

### 5. Difficulty Calibration

| Solver profile | Expected score | Evidence |
|---|---|---|
| Perfect implementation | 30/30 | Gold self-score |
| Misses retention only | 16/30 | baseline_almost.py result |
| Misses 5 major rules | 6/30 | baseline_naive.py result |
| Random integers | ~0/30 | Answer space is ~10^7, chance match negligible |

The benchmark targets the 10–20/30 range for strong tool-enabled models. Items
at "easy" difficulty have fewer active edge cases and are solvable with an
approximate implementation. Items at "hard" difficulty require all rules to be
correct simultaneously.

### 6. Leakage Check

The solver bundle does NOT contain:
- ✓ No gold answers
- ✓ No generator/verifier/scorer source code
- ✓ No difficulty tags
- ✓ No validation report or failure modes
- ✓ No private audit traces
- ✓ No hidden seeds or answer keys

The solver bundle DOES contain:
- ✓ Complete rules document (general_conditions.md)
- ✓ Task instructions (solver_packet.md)
- ✓ All 30 items with full data (items_private_sample.jsonl)
- ✓ Manifest (SOLVER_MANIFEST.json)

### 7. Edge Case Coverage

Across 30 items:
- 14 items trigger the 5% retention rate (cumulative ≥ 50%)
- 10 items have pending COs (50% billing)
- 8 items have disputed COs (25% billing)
- 3 items have rejected COs ($0 billing)
- 11 items have stored materials that fail ≥1 condition
- 4 items have excusable delays (LDs waived)
- 5 items have insurance lapses
- 22 items have taxable materials (non-exempt, non-zero rate)
- 12 items have material-flagged COs (tax interaction)

No single rule dominates; items typically have 2–4 active edge cases creating
compound difficulty.

### 8. Fairness Assessment

- The rules are clearly written in plain English in the solver-visible document.
- The computation sequence is explicitly enumerated (Article 13, steps 1–15).
- All data fields are documented in the solver packet with explanations.
- A "Key Edge Cases" section in the solver packet highlights important rules.
- The task does NOT require domain expertise beyond careful rule-following and arithmetic.
- Both humans and models should find this solvable through systematic implementation.

### 9. Non-Duplication Argument

This benchmark is NOT a duplicate of existing evaluations:
- Unlike **MATH/AIME**: No mathematical insight required; this is rule-application arithmetic.
- Unlike **HumanEval/MBPP**: Not a coding benchmark; the task is computation, not code generation.
- Unlike **GAIA**: Domain-specific with deterministic rules, not general knowledge retrieval.
- Unlike **Reimbursement Forensics**: Different domain mechanics (AIA G702 cumulative method,
  per-line rounding, multi-tier retention, change order status hierarchy).
- Unlike **MFN-Cascade**: No recursive fixed-point computation; straightforward sequential steps.
