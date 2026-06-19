---
name: pattern-analysis
description: Analyze complex task runs into evidence-backed case studies, failure-pattern reports, cross-run comparisons, and ablation plans. Use this whenever the user asks for a case study, trace analysis, root-cause report, model or agent comparison, failure taxonomy, process diagnosis, or ablation design over artifacts such as a task spec, run summary, tool trace, reconstructed code, final response, or grader report.
---

# Pattern Analysis

Use this skill when the user needs a reusable, evidence-heavy analysis of complex task runs rather than a one-off narrative summary.

The goal is not to restate the final answer. The goal is to reconstruct what the system needed to do, what it actually did, where the path diverged, how the error propagated, and which interventions are most likely to change the outcome.

## Supported modes

Route the request before writing anything:

1. **Single-case study**
   Use when the user cares about one task or one run and wants root cause, report quality, or remediation.

2. **Comparison-first analysis**
   Use when the user wants to know why one run, model, or agent beat another on the same task.

3. **Cohort pattern audit**
   Use when the user wants repeated failure modes across many tasks, runs, or systems.

4. **Ablation design**
   Use when the user wants to know which intervention to test and how to falsify a root-cause claim.

If the user does not specify a mode, infer it from the artifact set and deliverable. Do not block on missing comparison runs; a single-case study is still valid if the task contract and run artifacts are available.

## Core principles

- Work from artifacts, not from the system's self-description.
- Prefer the lowest-level evidence that proves a claim.
- Separate **task difficulty**, **system behavior**, **policy choice**, **tool contract**, and **environment instability**.
- Do not call something a root cause unless fixing it would plausibly change the outcome or the grade.
- Comparison runs are useful, but they are optional. The skill must still work without them.
- Always design at least one falsifiable ablation before claiming a stable pattern.

## Required artifact order

For single-case analysis, read these in order unless the user explicitly asks for something else:

1. task spec or equivalent contract document
2. execution summary
3. tool trace or action log
4. reconstructed code or executed logic summary
5. compressed judge or reviewer context
6. final response or final report
7. grader report or rubric delta
8. technical analysis, if present
9. raw trajectory or notebook only when the above leave ambiguity

This order matters:

- the task spec defines the contract
- the execution summary tells you whether the run ever got traction
- the tool trace shows exploration quality and pivot behavior
- the reconstructed code shows whether the system formed a valid experiment chain
- the reviewer context compresses turning points and decision-relevant evidence
- the final response is only a claim surface, not proof
- the grader report shows what was rewarded or penalized

## Tool-oriented workflow

When the user has structured artifacts on disk, start with the helper scripts:

### Case manifest

```bash
python skills/pattern_analysis/scripts/collect_case_inputs.py \
  --case-id <CASE_ID> \
  --task-spec <TASK_SPEC_PATH> \
  --run-dir <RUN_DIR> \
  --compare-run-dir <RUN_DIR_2> \
  --output <MANIFEST_JSON>
```

### Report scaffold

```bash
python skills/pattern_analysis/scripts/scaffold_case_report.py \
  --manifest <MANIFEST_JSON> \
  --output <OUTLINE_MD>
```

These scripts do not replace reasoning. They compress repetitive file discovery and make later analysis more deterministic.

## Full-cycle workflow

### Phase 0: Scope and intent classification

Classify:

- case mode: single-case, comparison-first, cohort, or ablation
- task shape: execution-heavy, analysis-heavy, mixed execution + analysis, or constraint audit
- dominant failure surface: execution, reasoning, state management, evidence integration, tool contract, or environment

State these classifications early. They control the rest of the report.

### Phase 1: Contract extraction

Extract from the task spec:

- final task goal
- required intermediate operations
- explicit rubric gates
- disallowed shortcuts or constraints
- reference answer, if present

Reduce this into a **minimum successful loop**. Keep it short and causal.

### Phase 2: Actual loop reconstruction

Rebuild the run in temporal order:

- opening exploration
- first experiment or analysis attempt
- first hard error or first strategic mistake
- adaptation or non-adaptation after failure
- final evidence set actually available
- final claim surface

Do not compress distinct failures into one vague paragraph. A long run usually needs a chain.

### Phase 3: Failure-node identification

Find the earliest node that explains most downstream damage.

Good root-cause categories:

- wrong task decomposition
- wrong environment model
- wrong abstraction choice
- wrong tool-call semantics
- state loss after partial progress
- evidence extraction bottleneck
- evidence integration bottleneck
- recovery failure after first error

Secondary failures can be listed later, but only after the primary node is defended with evidence.

### Phase 4: Observable pattern extraction

Translate the failure node into symptoms that another analyst could spot in a different run.

For each pattern, write:

- **Condition**
- **Observable signal**
- **Why it happens**
- **What damage it causes**
- **How to detect it early**

Distinguish:

- **static symptoms**: visible from file contents or metadata
- **dynamic propagation**: how one early mistake corrupts later state transitions

### Phase 5: Comparison and counterfactual

If stronger runs exist on the same task:

- compare where they first diverged from the failing run
- compare abstraction choices, not just final answers
- compare whether they used a higher-level primitive, a shorter loop, or a stronger evidence filter

If no stronger runs exist:

- compare the failing run against the minimum successful loop from the task contract

Then write a counterfactual:

- If only the claimed root cause were fixed, what would likely change?
- Which missing rubric items would become reachable?
- Which failures would still remain?

If the counterfactual sounds too broad or magical, it is not a good root-cause claim yet.

### Phase 6: Ablation design

Every serious report needs at least one falsifiable ablation.

Use `references/ablation_playbook.md` and build a compact table with:

- hypothesis
- manipulated factor
- held-constant factors
- expected change
- evaluation metric
- falsifier

Examples:

- remove comparison runs and see whether the same root cause still emerges
- hide the reviewer analysis and force reconstruction from lower-level artifacts
- replace the failing run's abstraction choice with the stronger run's abstraction choice while holding the task fixed
- reduce or extend time budget to distinguish planning failure from raw runtime exhaustion

### Phase 7: Bottleneck generalization

Only after the case is proven, generalize it into a reusable pattern.

The pattern statement should fit this structure:

`In tasks with <condition>, the system tends to <behavior>, which produces <observable symptom> and causes <downstream consequence>.`

Then attach interventions at the right layer:

- model or policy-training layer
- agent-policy layer
- tool-interface layer
- evaluation or product layer

## Output contract

Use `references/report_contract.md` as the default shape.

### For single-case studies

Required sections:

1. Task Snapshot
2. Task Classification
3. Minimum Successful Loop
4. Actual Execution Loop
5. Critical Failure Nodes
6. Observable Failure Pattern
7. Counterfactual Attribution
8. Ablation Plan
9. Transferable Bottleneck
10. Actionable Interventions

### For cohort audits

Required sections:

1. Scope and sampling rules
2. Cohort summary table
3. Pattern taxonomy
4. Representative cases
5. Competing hypotheses
6. Proposed ablations
7. Actionable interventions

## Style rules

- Write in plain English.
- Be direct. Remove warm-up prose and meta-commentary.
- Use tables when comparing evidence, not long mixed paragraphs.
- A figure or loop diagram should show a causal chain, not just chronology.
- If you mention an artifact, tie it to the specific claim it proves.
- If the report will be rendered as PDF, keep diagrams compact and readable.

## Quality gate before finishing

Check the draft against `references/report_contract.md`:

- Did you prove the task contract before diagnosing the run?
- Is the expected loop shorter than the actual loop and causally crisp?
- Is the primary failure node earlier than the final wrong answer?
- Did you separate environment failure from system failure?
- Did you include at least one falsifiable ablation?
- Could another analyst reproduce your diagnosis from the cited artifacts?

If any answer is no, revise before presenting the report as complete.
