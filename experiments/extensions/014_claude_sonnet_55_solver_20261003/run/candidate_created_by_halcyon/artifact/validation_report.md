# Validation & Verification Report — Maritime General Average & Salvage Forensics (MGAF)

**Benchmark Name:** `maritime_general_average_forensics`  
**Version:** `1.0.0`  
**Sample Count:** `30` (`mgaf_01` through `mgaf_30`)  
**Seed:** `20260516`  
**Frozen & Generated Payload SHA256 Digest:** `cf4c4dd0cad24ca358ec4038809ebde23055615c1a10b1116f63a5bc2c111771`  
**External Solvability Evidence:** Verified via independent fresh-context blind subagent ([Fresh-Context Blind Solver Subagent](conversation://7cc45569-929d-49f8-8d9c-8abb81ef69ac)) on `solver_bundle/` (`6/6 = 100.0%` on stratified 5-tier audit sample; `30/30 = 100.0%` full reference solver verification).

---

## 1. Deterministic Generation Verification

The generator (`generator.py`) implements the required CLI contract:

```bash
python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .
```

### 1.1 Reproducibility Across Independent Runs
Two independent executions of `generator.py` with `--sample-count 30 --seed 20260516` produce byte-for-byte identical outputs across all generated files:
- `gold_private_sample.jsonl` (`30` lines, `1,112` bytes)
- `solver_bundle/SOLVER_MANIFEST.json` (`634` bytes)
- `solver_bundle/README.md` (`2,354` bytes)
- `solver_bundle/solver_packet.md` (`759` bytes)
- `solver_bundle/items_private_sample.jsonl` (`30` lines, `17,094` bytes)
- `solver_bundle/assets/maritime_ga_rulebook.md` (`15,954` bytes)
- `solver_bundle/assets/fx_and_port_tariffs.csv` (`5,365` bytes)
- `solver_bundle/assets/dossiers_part1.md` (`25,825` bytes)
- `solver_bundle/assets/dossiers_part2.md` (`26,181` bytes)
- `solver_bundle/assets/dossiers_part3.md` (`27,359` bytes)

- **Attempt 1 Payload Digest:** `cf4c4dd0cad24ca358ec4038809ebde23055615c1a10b1116f63a5bc2c111771`
- **Attempt 2 Payload Digest:** `cf4c4dd0cad24ca358ec4038809ebde23055615c1a10b1116f63a5bc2c111771`
- **Frozen Artifact Payload Digest:** `cf4c4dd0cad24ca358ec4038809ebde23055615c1a10b1116f63a5bc2c111771`
- **Deterministic Match:** `True` (`attempt_1 == attempt_2 == frozen_digest`)

---

## 2. Verifier & Solver-Bundle Isolation Check

Running the dataset and leak-isolation verifier:

```bash
python3.12 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
```

Output:
```json
{
  "schema_version": 2,
  "status": "ok",
  "valid": true,
  "passed": true,
  "total": 30,
  "verified": 30,
  "correct": 30,
  "accuracy": 1.0,
  "leak_scan_matches": 0,
  "errors": []
}
```

### 2.1 Zero Answer Leakage Verification
- `solver_bundle/` contains strictly the 9 solver-visible files declared in `SOLVER_MANIFEST.json`.
- `gold_private_sample.jsonl`, `generator.py`, `verifier.py`, and `scorer.py` reside outside `solver_bundle/`.
- A regex boundary scan across all files inside `solver_bundle/` for all 30 gold USD-cent integer answers confirms **`leak_scan_matches: none` (`0` matches)**.

---

## 3. Controller Scorer Checks (`schema_version: 2`)

### 3.1 Gold Positive Control (`score_gold_controller`)
```bash
python3.12 scorer.py --gold gold_private_sample.jsonl --predictions gold_private_sample.jsonl --out score_gold.json
```
Result:
```json
{
  "schema_version": 2,
  "total": 30,
  "correct": 30,
  "accuracy": 1.0,
  "unanswered": 0
}
```

### 3.2 Shifted / Wrong Negative Control (`score_wrong_shifted_controller`)
When predictions are circularly shifted by 1 item (`mgaf_01` predicted as `mgaf_02`'s answer, etc.) or perturbed:
```bash
python3.12 scorer.py --gold gold_private_sample.jsonl --predictions wrong_shifted_predictions.jsonl --out score_wrong_shifted.json
```
Result (all 30 gold answers are strictly distinct integers, so circular shift yields `0/30`):
```json
{
  "schema_version": 2,
  "total": 30,
  "correct": 0,
  "accuracy": 0.0,
  "unanswered": 0
}
```

### 3.3 Naive Unadjusted Baseline (`score_naive_baseline`)
A naive baseline adjuster that sums `FINAL_PAID` general average port/tug/detention vouchers (excluding permanent hull/shaft repairs and normal post-refuge sea-transit wages), uses unamended B/L values and B/L-date FX rates, ignores Rule XVII `Made Good` add-backs, ignores Rule XIII age deductions, ignores Rule XIX misdeclaration penalties, ignores Collect Freight at Risk, and ignores Two-Stage Salvage cascades scores **`4/30` (`13.33%`)**:
```json
{
  "schema_version": 2,
  "total": 30,
  "correct": 4,
  "accuracy": 0.13333333333333333,
  "unanswered": 0
}
```
- Correctly solved by naive baseline (`4` items): `mgaf_01`, `mgaf_02`, `mgaf_14`, `mgaf_17`.
- Failed on `26/30` items due to multi-currency `TERMINATION_DATE` FX rules, `Made Good` denominator feedback, Rule I/III/V/XII sacrifice vs. Particular Average distinctions, Rule XIII `keel_laid_year` deductions, Rule XIX `2x` penalty assessments, Collect Freight at Risk, and Two-Stage Salvage cascades.

---

## 4. External Solvability Evidence (Fresh-Context Blind Subagent Audit)

- **external_solvability_evidence:** `verified`
- **Subagent Role:** `Fresh-Context Blind Solver` (`research` subagent via `invoke_subagent`)
- **Subagent Conversation Link:** [Fresh-Context Blind Solver Subagent](conversation://7cc45569-929d-49f8-8d9c-8abb81ef69ac)
- **Subagent Conversation ID:** `7cc45569-929d-49f8-8d9c-8abb81ef69ac`
- **Subagent Transcript URI:** `file://<temporary-root>/bbp-ysseiq9a/home/.gemini/antigravity-cli/brain/7cc45569-929d-49f8-8d9c-8abb81ef69ac/.system_generated/logs/transcript.jsonl`
- **Isolation Protocol:** The blind subagent was invoked in a fresh context and restricted exclusively to reading files inside `solver_bundle/` (`solver_bundle/README.md`, `solver_bundle/assets/maritime_ga_rulebook.md`, `solver_bundle/assets/fx_and_port_tariffs.csv`, and `solver_bundle/assets/dossiers_part1.md`–`dossiers_part3.md`), with zero access to `gold_private_sample.jsonl` or `generator.py`.

### 4.1 Stratified Blind Solver Verification Across All 5 Complexity Tiers
| Item ID | Tier | Key Rules Verified by Blind Solver | Blind Solver Prediction (USD Cents) | Gold Answer (USD Cents) | Match |
|---|---:|---|---:|---:|---|
| `mgaf_01` | Tier 1 | PA grounding repair filter + `Lot-A` Special Charge | `1324550` | `1324550` | Exact (`True`) |
| `mgaf_05` | Tier 1 | Under-deck jettison `Made Good` in both GA Pool and $V_{\text{Lot-B}}$ | `3500000` | `3500000` | Exact (`True`) |
| `mgaf_13` | Tier 3 | Rule XIII `keel_laid_year=2006` (`1/3` machinery, `0` anchor, `1/6` chain) | `5692050` | `5692050` | Exact (`True`) |
| `mgaf_20` | Tier 4 | `COLLECT_AT_DESTINATION` Net Freight (`$80/t`) + `Freight Made Good` | `5645025` | `5645025` | Exact (`True`) |
| `mgaf_24` | Tier 5 | Two-Stage Salvage (`$200k`) -> GA Cascade with pre-salvage jettison | `9700000` | `9700000` | Exact (`True`) |
| `mgaf_30` | Tier 5 | Full cascade (`GBP` FX + Collect Freight + Rule III + Rule XIII + Salvage + Bigham Cap) | `12848050` | `12848050` | Exact (`True`) |

- **Blind Subagent Stratified Sample Accuracy:** `6 / 6` (`100.0%`)
- **Full 30-Item Reference Verification Accuracy:** `30 / 30` (`100.0%`)
