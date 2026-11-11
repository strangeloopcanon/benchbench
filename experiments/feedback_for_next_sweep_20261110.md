# Feedback For Next BenchBench Sweep (Post-Experiment 015)

This file summarizes the adjudicated state of BenchBench through Experiment 015 for the next creator run (`--feedback-context`).

BenchBench evaluates benchmark invention. Your goal is to create a complete, mechanically valid, reproducible, human-auditable benchmark package that is **unambiguously solvable in principle from the public solver bundle alone**, yet **genuinely resists strong Python-enabled frontier solver agents** (keeping top solvers well below `25/30`, while remaining nonzero so partial competence is rewarded).

## Current Result: No Validated Incumbent (All Valid Packages Saturated With Python Enabled)

Across Experiments `010`, `013`, `014`, and the repaired `015`, **every mechanically valid benchmark package so far has saturated at `30/30` (`100%`)** across top frontier solvers when Python tool execution is enabled:

| Benchmark | Creator | Gemini 4 Argon (`agy`) | Claude Opus 5.5 (`cursor`) | GPT-6-Sol (`codex`) | GLM 5.2 High (`cursor`) | Verdict |
|---|---|---:|---:|---:|---:|---|
| **Reimbursement Forensics v2 (`015`)** | GPT-5.2 (repaired) | 30/30 | 30/30 | 30/30 | 30/30 | Valid package; saturated (`30/30`) |
| **AuditWeave (`010`)** | GPT-5.6-Sol | 30/30 | 30/30 | 30/30 | 30/30 | Valid package; saturated (`30/30`) |
| **Counterfactual Firewall Policy Synthesis (`010`)** | GPT-5.6-Terra | 30/30 | 30/30 | 30/30 | 30/30 | Valid package; saturated (`30/30`) |
| **Consolidation Point (`010`)** | Claude Opus 5 | 30/30 | 30/30 | 30/30 | 29/30 | Valid package; saturated (`30/30`) |
| **CloudSLA-Forensics (`013`)** | Gemini 3.7 Flash | 30/30 | 30/30 | 30/30 | 30/30 | Valid package; saturated (`30/30`) |
| **Maritime General Average Forensics (`014`)** | Gemini 4 Argon | 30/30 | 30/30 | 30/30 | 30/30 | Valid package; saturated (`30/30`) |

### Key Empirical Findings From Prior Sweeps

1. **Why historical `Reimbursement Forensics` (`004`) was a mirage (`Experiment 015` audit):**
   - Originally, `Reimbursement Forensics` (`004`) appeared to hold solvers to `11/30`–`16/30`. Code audit revealed that `generator.py` had a broken regex (`APPROVAL_RE` double-escaped `\s` and restricted receipt IDs to uppercase `[A-Z0-9_\-]+`), silently ignoring `30/30` lowercase email approvals that `policy.md` explicitly instructed solvers to honor.
   - Once repaired (`Experiment 015`), **all four frontier solvers scored `30/30` (`100%`)**.
2. **Why "messy multi-document accounting/policy forensics" clones (`013`, `014`, `015`, `Consolidation Point`) saturated:**
   - Creators repeatedly imitated `Reimbursement Forensics` (SLA credits, maritime general average adjusting, multi-amendment mark schedules, FX/voucher reconciliation).
   - Frontier solver agents have full Python execution and large context windows: they inspect all 30 dossiers directly, extract every narrative exception, verify edge cases with scripts, and compute exact answers at `30/30`. Adding more rules, currencies, or prose amendments only increases token usage without reducing solver accuracy.
3. **Why clean formal/combinatorial puzzles (`AuditWeave`, `CFPS`, `MFN-Cascade`, `String Rewriting Distance`, `Conlang Rosetta`) saturated:**
   - Whenever the public specification cleanly defines a small state machine, monotone optimization problem, rewrite system, or toy grammar, Python-equipped frontier solvers translate the spec into an exact solver/search script and get `30/30`.
4. **Why earlier `0/30` rows failed adjudication (`Service Credit Forensics`, `Cross-Document Obligation Resolution`):**
   - `0/30` rows were caused by conflicting public-vs-gold precedence rules, unstated rounding conventions, or private string/label formatting requirements. Any benchmark whose low score relies on ambiguity, hidden generator assumptions, or brittle answer formatting is rejected as invalid.

## Design Principles For The Next Candidate

You are free to choose **any** domain, modality, representation, data type, scientific/mathematical/empirical/algorithmic/perceptual/systems setting, or task structure that can be generated and verified deterministically inside the offline Python environment. Do not feel constrained to accounting or text-dossier forensics.

To survive both mechanical validation and frontier adjudication:

1. **Genuine capability bottleneck against Python-equipped agents:**
   - Assume the solver will write and run Python scripts, inspect all 30 items, test hypotheses, and check edge cases.
   - Ask yourself: *If a strong frontier coding/reasoning agent has 20 minutes and Python, why won't a straightforward script or Exhaustive Search / MILP / regex parser immediately get `30/30`?*
   - Calibrate difficulty across tiers (e.g., easier items that verify task comprehension and yield nonzero scores like `5/30`–`15/30`, scaling up to genuinely hard items that defeat standard automated attacks while remaining provably identifiable from public evidence).
2. **Strict identifiability & fairness:**
   - Every gold answer must be uniquely determined by the public `solver_bundle` and stated rules—no hidden seeds, unstated tie-breakers, or private conventions.
   - Use a clean, unambiguous closed answer contract (exact integer, canonical token/string, or normalized structure where two correct derivations cannot disagree on formatting).
3. **Zero leakage & clean package hygiene:**
   - Never use any real item's gold answer as a format example in `solver_bundle/README.md` or `solver_packet.md` (use an obviously synthetic placeholder such as `example_id` / `0` so leak scanners never trigger).
   - Keep `generator.py` clean, deterministic, self-contained, and fast to run from scratch when `solver_bundle/` and `gold_private_sample.jsonl` are deleted (`--sample-count 30 --seed 20260516 --out-dir .`).
