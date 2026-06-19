# Pattern Analysis Skill

This folder contains a reusable, tool-oriented skill package for evidence-backed pattern analysis of complex task runs.

It is designed for:

- single-case studies
- cross-run or cross-system comparison
- cohort-level failure taxonomy work
- root-cause and counterfactual analysis
- ablation planning for policy, tooling, or evaluation changes

## Package layout

- `SKILL.md`: the reusable skill instructions
- `references/`: workflow, artifact map, report contract, and ablation playbook
- `scripts/collect_case_inputs.py`: build a structured manifest from a task spec and one or more run folders
- `scripts/scaffold_case_report.py`: generate a report skeleton from a manifest

## Recommended usage

1. Read `SKILL.md`.
2. Run `scripts/collect_case_inputs.py` on the target case.
3. Read the task spec and run artifacts in the recommended order.
4. Draft the report against `references/report_contract.md`.
5. If the root cause still feels underspecified, use `references/ablation_playbook.md` before finalizing.

## Example manifest command

```bash
python docs/analysis/pattern_analysis_skill/scripts/collect_case_inputs.py \
  --case-id my-case \
  --task-spec /path/to/task_spec.json \
  --run-dir /path/to/target_run \
  --compare-run-dir /path/to/comparison_run \
  --output /tmp/case_manifest.json
```

## Example scaffold command

```bash
python docs/analysis/pattern_analysis_skill/scripts/scaffold_case_report.py \
  --manifest /tmp/case_manifest.json \
  --output /tmp/case_study_outline.md
```
