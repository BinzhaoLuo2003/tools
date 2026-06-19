# Ablation Playbook

Pattern analysis is weak when it stops at naming a plausible cause. This file forces the report to include experiments that could confirm or reject the diagnosis.

## 1. Root-cause ablations

Use these when you think one early mistake drives most of the failure.

| Ablation | Manipulation | What it tests |
|---|---|---|
| Primitive swap | Replace the failing run's primitive with the stronger run's primitive while preserving task and goal | Whether the core issue was abstraction choice rather than reasoning depth |
| Recovery injection | Add a checkpoint or replan step immediately after the first hard error | Whether the failure was mainly lack of recovery logic |
| Evidence-filter upgrade | Add one missing analysis stage such as background subtraction or peak filtering | Whether the wrong conclusion came from evidence extraction, not acquisition |

## 2. Information-source ablations

Use these when your report depends heavily on one summary artifact.

| Ablation | Manipulation | What it tests |
|---|---|---|
| No comparison run | Remove other-model traces and redo the diagnosis | Whether the root cause still emerges from the target run plus task contract |
| No technical analysis | Hide `technical_analysis.md` and reconstruct from lower-level artifacts | Whether the report is robust to grader-side interpretations |
| No final response | Ignore the agent's summary and reason only from code and tool history | Whether the agent overclaimed or misreported its own behavior |

## 3. Budget and environment ablations

Use these when it is unclear whether the failure is model quality or infrastructure pressure.

| Ablation | Manipulation | What it tests |
|---|---|---|
| Time-budget sweep | Re-evaluate the run under shorter and longer time budgets | Whether the main issue is startup latency or incorrect strategy |
| Tool-contract clarification | Add clearer tool hints or templates | Whether the issue is interface ambiguity rather than model misunderstanding |
| Environment-clean rerun | Re-run in a stabilized environment | Whether the bottleneck was genuine model behavior or environment instability |

## 4. Counterfactual discipline

Each ablation row should answer:

1. What exact hypothesis am I testing?
2. What is manipulated?
3. What is held constant?
4. What result would support the hypothesis?
5. What result would falsify it?

If a proposed ablation cannot fail, it is not an ablation. It is wishful thinking.

## 5. Minimal ablation table format

Use this compact format in reports:

| Hypothesis | Manipulation | Held Constant | Expected Shift | Metric | Falsifier |
|---|---|---|---|---|---|
| Example: the main failure is wrong measurement abstraction | Replace pointwise sweep with full-map parameter on the same task | task, model family, answer rubric | bias coverage becomes complete before timeout | completed biases, score delta, analysis completeness | coverage stays poor or final conclusion remains wrong |
