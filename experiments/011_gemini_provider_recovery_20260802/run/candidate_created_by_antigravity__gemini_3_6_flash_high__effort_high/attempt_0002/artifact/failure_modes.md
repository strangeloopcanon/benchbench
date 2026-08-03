# Failure Modes Documentation

This document outlines common failure modes exhibited by Large Language Models when attempting the `state_machine_trace` benchmark.

## 1. Register State Drift (Memory Loss in Multi-Step Chains)
- **Symptom**: As the sequence length increases (> 6 steps), the model loses track of intermediate register values modified in earlier steps.
- **Root Cause**: Attention degradation across sequential register updates when tracking multiple named variables simultaneously.

## 2. Off-By-One & Execution Order Errors
- **Symptom**: The model applies Step `N+1` using the pre-step values rather than the newly updated register values from Step `N`.
- **Root Cause**: Failure to enforce strict sequential dependency when evaluating state transitions.

## 3. Conditional Precedence & Branch Evaluation Mistakes
- **Symptom**: Incorrect branch selection in `IF R_i > R_j THEN ... ELSE ...` instructions due to stale register value evaluation in the comparison.
- **Root Cause**: Evaluating conditional guards against initial register values instead of current step register values.

## 4. Output Formatting & JSON Normalization Failures
- **Symptom**: Returning natural language explanations ("The final value of R0 is 5...") instead of strict JSON objects (`{"R0": 5, "R1": 10, ...}`).
- **Root Cause**: Prompt instruction following failures under reasoning pressure.
