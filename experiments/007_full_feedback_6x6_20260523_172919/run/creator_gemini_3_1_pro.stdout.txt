I have completed the design and implementation of the new benchmark, **Commercial Lease CAM Reconciliation**.

### Benchmark Summary
The benchmark tasks solvers with calculating the final Commercial Area Maintenance (CAM) charges for multiple tenants across a single year (2025). The difficulty emerges from combining precise temporal math with unstructured text overrides.

To succeed, a solver must:
1. **Extract variables across documents:** Read building dimensions from `property_data.json` and occupancy timelines from `rent_roll.csv`.
2. **Apply explicit numerical rules:** Use a strict definition for CapEx vs OpEx (e.g. `amount < 500000` is OpEx; `amount >= 500000` is CapEx) to filter expenses in `expenses_ledger.csv`, and execute floor division logic outlined in `lease_manual.md`.
3. **Parse unstructured overrides:** Read `communications.txt` emails that override default rules. These emails randomize phrasing and describe mid-year tenant expansions, direct charge fault assignments, capital improvement reclassifications, and individualized CAM caps.
4. **Execute temporal math:** Compute exact square-foot-days based on standard overlapping day counting to derive accurate pro-rata shares.

### Completion of Required Steps
- **Generator, Verifier, and Scorer:** Created all required Python scripts adhering precisely to the data contracts. The generator seeds deterministic, mathematically sound items where all integer arithmetic resolves uniquely.
- **Verification and Baselines:** Generated 30 items. Verified the package successfully. The gold self-score confirmed a perfect `30.00/30.0`. A baseline testing all `0` predictions confirmed a minimum score of `0.00/30.0`.
- **Reports:** Created `validation_report.md` proving the task is fully identified in the public bundle and entirely verifiable without guessing. Wrote `failure_modes.md` outlining traps intentionally placed for naive rule-based scripts and zero-shot LLM solvers. Added `benchmark_spec.json` and `README.md`.
- **Solver Bundle Isolation:** Confirmed the `solver_bundle/` is clean of any leakage, holding only the public `SOLVER_MANIFEST.json`, `README.md`, `items_private_sample.jsonl`, and the generated item directories.

The benchmark package is fully functional and ready in your target directory! Let me know if you need any adjustments to the difficulty tuning or data distributions.
