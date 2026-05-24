# Commercial Lease CAM Reconciliation Benchmark

## Overview
This benchmark tasks solvers with calculating the final Commercial Area Maintenance (CAM) charges for tenants in a commercial building across a one-year period (2025). The solver must synthesize a base set of lease math rules with structural data (property layout), tabular data (rent roll, expense ledger), and unstructured text (emails specifying reclassifications, direct charges, expansions, and CAM caps).

## Context in the Benchmark Landscape
This benchmark is closest in shape to **Reimbursement Forensics** and **Cross-Document Obligation Resolution**.
It is not merely a duplicate because it introduces temporal math (calculating exact Square-Foot-Days), conditionally applied expense thresholds (e.g. strict CapEx cutoff rules), and unstructured textual overrides that explicitly break or modify the default structured parsing rules. Rather than a flat summation or standard decision tree, the solver must trace each expense, adjust the pool based on emails, calculate a property management fee on the adjusted base pool, compute precise pro-rata shares based on potentially shifting occupancies, and apply individualized caps.

## Structure
- `generator.py`: Generates the benchmark items procedurally, avoiding data leakage.
- `verifier.py`: Ensures all generated assets exist and the gold format matches expectations.
- `scorer.py`: Calculates score based on exactly matched integer cent values for every tenant's final charge.
- `solver_bundle/`: Contains the generated items, manifests, and instructions for solvers.

## Difficulty
The task is deterministic and solvable in principle by a CPA or a careful solver agent, as integer arithmetic is used throughout. It is designed to be hard for strong models because a naive script will miss the unstructured email overrides, while a pure LLM zero-shot prompt will likely fail the precise arithmetic required over 20+ expenses and 365-day pro-rata calculations.
