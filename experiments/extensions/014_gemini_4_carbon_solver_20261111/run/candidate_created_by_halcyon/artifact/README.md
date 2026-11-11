# Maritime General Average & Salvage Forensics (MGAF)

**Benchmark Name:** `maritime_general_average_forensics`  
**Version:** `1.0.0`  
**Sample Count:** `30` (`mgaf_01` through `mgaf_30`)  
**Default Seed:** `20260516`  
**Answer Format:** Exact integer in USD cents (`$1.00 = 100` cents) representing the Final Total Assessment ($\text{Salvage}_{\text{Lot-A}} + \text{GA}_{\text{Lot-A}} + \text{SpecialCharges}_{\text{Lot-A}}$) payable by Cargo Interest `Lot-A` at the termination of the maritime adventure.

---

## 1. Capability Claim & Benchmark Design

**Maritime General Average & Salvage Forensics (MGAF)** measures whether tool-enabled frontier models can perform multi-hop forensic accounting and cross-document contradiction resolution over realistic maritime casualty adjustment dossiers governed by a self-contained York-Antwerp Charter Rulebook (`solver_bundle/assets/maritime_ga_rulebook.md`).

Unlike flat ledger-reconciliation benchmarks where a single linear filter solves every item, MGAF introduces **endogenous mathematical coupling**:
1. **Numerator + Denominator Feedback (Rule XVII `Made Good`):** Classifying a physical loss as a General Average Sacrifice (`Made Good`) vs. Particular Average (`PA`) simultaneously alters **both** the numerator ($\text{GA}_{\text{pool}}$) and the denominator ($\sum_j V_j$, because every allowable sacrifice must be added back to the sacrificed interest's Stage 2 Contributory Value $V_i$).
2. **Cross-Document Forensic Contradictions:** Each dossier (`assets/dossiers_part1.md`, `assets/dossiers_part2.md`, `assets/dossiers_part3.md`) must be reconciled against `assets/fx_and_port_tariffs.csv` and contemporaneous surveyor/customs/agent telexes (e.g., `keel_laid_year` vs narrative `reflagged_year` for Rule XIII age-tiered deductions; `termination_date` FX vs `bol_date` FX; Rule I cellular container deck vs timber well-deck / unauthorized flat-rack jettison; Rule III extinguishing water on unburnt packages vs smoke/active-fire char; Rule XIX willful under-declaration `2x` penalty vs pre-sailing clerical booking amendments).
3. **Two-Stage Casualty Cascades & Bigham Caps:** In Tier 5 (`mgaf_24`–`mgaf_30`), independent Article 13 Salvage Awards must be apportioned in Stage 1 over actual physical Salved Values ($S_i$, at `1x` without `Made Good` add-back or Rule XIX doubling), deducted as a prior lien before computing Stage 2 General Average Contributory Values ($V_i$), and combined with Non-Separation Agreement Bigham Clause caps that bind strictly on Stage 2 $\text{GA}_{\text{Lot-A}}$.

---

## 2. Package Layout & Solver-Bundle Isolation

```text
.
├── README.md                                 # Benchmark package documentation
├── benchmark_spec.json                       # Machine-readable benchmark specification & CLI contract
├── generator.py                              # Deterministic dataset generator & reference adjuster
├── verifier.py                               # Schema, reference-solution, and leak-isolation verifier
├── scorer.py                                 # Exact-match USD-cents scorer (schema_version: 2)
├── gold_private_sample.jsonl                 # Private 30-item gold answer key (controller-only)
├── validation_report.md                      # Full verification, baseline, & external solvability report
├── failure_modes.md                          # Diagnostic taxonomy & 30-item failure mode matrix
└── solver_bundle/                            # Isolated solver-visible directory (0 answer leaks)
    ├── SOLVER_MANIFEST.json                  # Solver bundle manifest
    ├── README.md                             # Solver-facing instructions
    ├── solver_packet.md                      # Concise solver prompt packet
    ├── items_private_sample.jsonl            # 30 solver-visible item records (mgaf_01 .. mgaf_30)
    └── assets/
        ├── maritime_ga_rulebook.md           # Consolidated York-Antwerp Adjusting Manual
        ├── fx_and_port_tariffs.csv           # Vessel keel_laid_year, FX schedules, & freight tariffs
        ├── dossiers_part1.md                 # Forensic dossiers mgaf_01 .. mgaf_10
        ├── dossiers_part2.md                 # Forensic dossiers mgaf_11 .. mgaf_20
        └── dossiers_part3.md                 # Forensic dossiers mgaf_21 .. mgaf_30
```

---

## 3. CLI Contracts

### 3.1 Deterministic Generation
```bash
python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir .
```
- Deterministically generates `solver_bundle/` and `gold_private_sample.jsonl` with frozen payload SHA256 digest `cf4c4dd0cad24ca358ec4038809ebde23055615c1a10b1116f63a5bc2c111771`.

### 3.2 Package & Reference Solution Verification
```bash
python3.12 verifier.py --items solver_bundle/items_private_sample.jsonl --gold gold_private_sample.jsonl
```
- Verifies all 30 items, asset references, `SOLVER_MANIFEST.json`, exact agreement with the reference two-stage adjuster (`30/30`), and zero answer leakage (`leak_scan_matches: 0`) across `solver_bundle/`.

### 3.3 Deterministic Scoring (`schema_version: 2`)
```bash
python3.12 scorer.py --gold gold_private_sample.jsonl --predictions predictions.jsonl --out score_report.json
```
- Outputs JSON containing `"schema_version": 2`, integer `"total"`, integer `"correct"`, numeric `"accuracy"` (`correct / total`), `"unanswered"`, and `"per_item"` breakdown.

---

## 4. Validation & External Solvability Summary

- **Determinism:** Two independent runs of `python3.12 generator.py --sample-count 30 --seed 20260516 --out-dir ...` produce identical payload digest `cf4c4dd0cad24ca358ec4038809ebde23055615c1a10b1116f63a5bc2c111771`, matching the frozen artifact directory.
- **Gold Positive Control (`score_gold_controller`):** `total: 30, correct: 30, accuracy: 1.0`.
- **Shifted/Wrong Negative Control (`score_wrong_shifted_controller`):** `total: 30, correct: 0, accuracy: 0.0`.
- **Naive Unadjusted Baseline:** `total: 30, correct: 4, accuracy: 0.13333333333333333` (`mgaf_01`, `mgaf_02`, `mgaf_14`, `mgaf_17`).
- **External Solvability Evidence:** Verified via independent fresh-context blind subagent ([Fresh-Context Blind Solver Subagent](conversation://7cc45569-929d-49f8-8d9c-8abb81ef69ac)) operating strictly inside `solver_bundle/` without access to `gold_private_sample.jsonl` or `generator.py`, achieving `6/6` (`100.0%`) across all 5 complexity tiers (`mgaf_01`, `mgaf_05`, `mgaf_13`, `mgaf_20`, `mgaf_24`, `mgaf_30`), alongside `30/30` (`100.0%`) full-sample verification. See `validation_report.md` for full details.
