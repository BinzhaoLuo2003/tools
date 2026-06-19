# Pattern Analysis Skill

This folder contains a reusable, tool-oriented skill package for evidence-backed pattern analysis of complex benchmark task runs.

It is designed for:

- single-case studies
- cross-run or cross-system comparison
- cohort-level failure taxonomy work
- root-cause and counterfactual analysis
- ablation planning for policy, tooling, or evaluation changes

## Package layout

- `SKILL.md`: the reusable skill instructions
- `references/`: workflow, artifact map, report contract, and ablation playbook
- `scripts/discover_case_artifacts.py`: scan arbitrary analysis folders and produce an artifact catalog
- `scripts/artifact_catalog.py`: shared discovery and catalog-selection helpers
- `scripts/collect_case_inputs.py`: build a structured manifest from a discovered catalog
- `scripts/scaffold_case_report.py`: generate a report skeleton from a manifest

## Quickstart

1. Read `SKILL.md`.
2. Run `scripts/discover_case_artifacts.py` across the full folder set you might analyze.
3. Inspect the discovered candidate directories and choose the case scope.
4. Run `scripts/collect_case_inputs.py` on the chosen directory or directories from the catalog.
5. Read the task spec and run artifacts in the recommended order.
6. Draft the report against `references/report_contract.md`.
7. If the root cause still feels underspecified, use `references/ablation_playbook.md` before finalizing.

## Example discovery command

```bash
CATALOG_PATH="./pattern-analysis.catalog.json"

python skills/pattern_analysis/scripts/discover_case_artifacts.py \
  --input-dir /path/to/analysis_root \
  --input-dir /path/to/more_artifacts \
  --output "$CATALOG_PATH"
```

## Example manifest command

```bash
python skills/pattern_analysis/scripts/collect_case_inputs.py \
  --catalog "$CATALOG_PATH" \
  --case-id my-case \
  --case-dir /path/to/analysis_root/case_alpha \
  --case-dir /path/to/response_root/case_alpha \
  --compare-case-dir /path/to/analysis_root/case_beta \
  --output ./pattern-analysis.manifest.json \
  --cleanup-catalog
```

Repeat `--case-dir` when one case spans multiple directory trees.

## Example scaffold command

```bash
python skills/pattern_analysis/scripts/scaffold_case_report.py \
  --manifest ./pattern-analysis.manifest.json \
  --output ./pattern-analysis.report.md
```
