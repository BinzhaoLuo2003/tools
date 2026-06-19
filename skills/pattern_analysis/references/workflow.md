# Full-Cycle Workflow

This file expands the skill into a repeatable workflow that can be followed manually or with helper scripts.

## 1. Intake

Collect:

- target case ID or analysis roots
- whether the user wants a single-case report, cohort audit, comparison, or ablation plan
- whether stronger comparison runs exist
- whether the final deliverable should be markdown, LaTeX/PDF, or both

## 2. Artifact discovery

First scan the full directory trees that may contain relevant evidence. Do not assume a single `run_dir/summary/` layout.

Preferred artifact set:

- task spec or contract document
- extracted run summary:
  - execution summary
  - tool trace
  - reconstructed code or logic summary
  - compressed judge or reviewer context
  - final response
  - grader report
- optional:
  - technical analysis
  - raw trajectory
  - executed notebook
  - comparison runs for the same task

Common filenames include `task.json`, `execution_summary.json`, `tool_calls.md`, `reconstructed_code.md`, `judge_context.md`, `final_response.md`, and `grade_report.json`, but the method is not tied to those exact names.

Recommended helper flow:

1. Run `scripts/discover_case_artifacts.py` across every relevant analysis root.
2. Review the discovered candidate directories and choose the primary case scope plus any comparison scopes.
3. If one logical case spans multiple roots, keep all matching directories and pass them as repeated `--case-dir` arguments.
4. Run `scripts/collect_case_inputs.py` against the discovery catalog to build the case manifest.
5. Pass `--cleanup-catalog` unless the user explicitly wants to keep the intermediate catalog.
6. Use any convenient output paths for the catalog, manifest, and report. They are user workspace artifacts, not part of the skill package itself.

## 3. Task contract reduction

Write four items before touching the run:

1. final objective
2. required intermediate steps
3. non-negotiable rubric gates
4. minimum successful loop

If you cannot write the minimum successful loop from the task spec, you have not understood the task yet.

## 4. Run reconstruction

Use the summary artifacts in this order:

1. execution summary
2. tool trace
3. reconstructed code
4. reviewer context
5. final response
6. grader report

Capture:

- first action choice
- first irreversible mistake
- time or tool budget burn
- whether the system recovered
- what evidence it ended with
- whether the final claim matched the evidence

## 5. Root-cause test

Before naming a root cause, ask:

- Is this the earliest node that explains most downstream damage?
- If fixed, would the outcome likely improve by at least one major rubric gate?
- Is the evidence directly visible in artifacts, not inferred from tone?

If the answer is no, keep it as a symptom, not a root cause.

## 6. Pattern extraction

Turn case-specific details into a reusable pattern:

- condition
- observable signal
- propagation chain
- likely consequence
- early detector

This is the part that makes the report general instead of anecdotal.

## 7. Comparison and counterfactual

If stronger runs exist:

- compare abstraction choices
- compare recovery behavior
- compare the first point at which they achieved task traction

Then write one counterfactual:

- what changes if the root cause is fixed
- what still remains missing

## 8. Ablation design

Build at least one experiment that could prove you wrong.

Good ablations:

- input visibility ablations
- abstraction-choice ablations
- timeout or budget ablations
- comparison-removal ablations
- reviewer-blind reconstructions

## 9. Final deliverable

A strong final artifact has:

- a compact task snapshot
- a crisp success loop
- a faithful actual loop
- evidence tables
- a defended root cause
- observable pattern statements
- at least one falsifiable ablation
- interventions at the correct layer
