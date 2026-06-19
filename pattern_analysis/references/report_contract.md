# Report Contract

Use this as the minimum structure for a polished, evidence-backed report.

## Single-case study

### 1. Task Snapshot

Include:

- case ID
- system / agent
- score or outcome
- turns
- tool-call count
- task type
- one-sentence task goal
- one-sentence outcome

### 2. Task Classification

State:

- execution-heavy / analysis-heavy / mixed / constraint audit
- dominant rubric gate
- where the run most obviously failed: execution, reasoning, evidence integration, recovery, tool contract, or environment

### 3. Minimum Successful Loop

Write the shortest causal chain that would satisfy the task. Keep it tight.

### 4. Actual Execution Loop

Reconstruct the run with concrete turning points. Avoid vague summaries.

### 5. Critical Failure Nodes

Use a table:

| Node | Evidence | Why it matters | Downstream effect |
|---|---|---|---|

### 6. Observable Failure Pattern

Separate:

- static signals
- dynamic propagation chain

This is where the report becomes reusable.

### 7. Counterfactual Attribution

Write the smallest plausible fix and what it would change. Distinguish:

- what becomes reachable
- what still remains missing

### 8. Ablation Plan

At least one falsifiable ablation table is required.

### 9. Transferable Bottleneck

Compress the case into one portable pattern statement.

### 10. Actionable Interventions

Group by layer:

- model or policy-training
- agent policy
- tool or interface
- evaluation or product

## Cohort audit

Required sections:

1. scope
2. sampling rule
3. pattern taxonomy
4. representative cases
5. confounders
6. ablations
7. interventions

## Non-negotiable quality checks

- Every major claim has an artifact-backed evidence trail.
- The primary failure node is earlier than the final wrong answer.
- The report includes at least one falsifiable ablation.
- The report does not depend on comparison runs unless it says so explicitly.
- The language is direct and free of filler.
