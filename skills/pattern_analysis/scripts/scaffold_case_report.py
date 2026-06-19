#!/usr/bin/env python3
"""Generate a markdown scaffold for a generic case-study report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def bullet_list(items: List[str]) -> str:
    if not items:
        return "- None captured yet."
    return "\n".join(f"- {item}" for item in items)


def file_table(run: Dict[str, Any]) -> str:
    rows = ["| Artifact | Path |", "|---|---|"]
    for name, path in sorted(run.get("available_files", {}).items()):
        rows.append(f"| `{name}` | `{path}` |")
    return "\n".join(rows)


def render_report(manifest: Dict[str, Any]) -> str:
    primary = manifest["primary_run"]
    comparisons = manifest.get("comparison_runs", [])

    comparison_lines = []
    for run in comparisons:
        comparison_lines.append(
            f"- `{run.get('system_name')}`: score {run.get('score')}/{run.get('max_score')} "
            f"({run.get('letter_grade')}); {run.get('tool_calls_count')} tool calls; "
            f"{run.get('turns')} turns"
        )
    comparison_block = "\n".join(comparison_lines) if comparison_lines else "- No comparison runs attached."

    return f"""# {manifest['case_id']} Pattern Analysis Draft

## Task Snapshot

| Field | Value |
|---|---|
| Case ID | `{manifest['case_id']}` |
| Title | {manifest.get('task_title') or 'Unknown'} |
| Reference Answer | {manifest.get('reference_answer') or 'Unknown'} |
| Primary System | `{primary.get('system_name')}` |
| Score | {primary.get('score')}/{primary.get('max_score')} ({primary.get('letter_grade')}) |
| Turns | {primary.get('turns')} |
| Tool Calls | {primary.get('tool_calls_count')} |

## Artifact Inventory

### Primary Run

{file_table(primary)}

### Comparison Runs

{comparison_block}

## Task Classification

- Execution-heavy / analysis-heavy / mixed:
- Dominant rubric gate:
- Likely dominant failure surface:

## Minimum Successful Loop

1.
2.
3.
4.

## Actual Execution Loop

1.
2.
3.
4.

## Critical Failure Nodes

| Node | Evidence | Why it matters | Downstream effect |
|---|---|---|---|
| | | | |

## Observable Failure Pattern

### Static signals

{bullet_list(primary.get('rubric_key_elements_missing', []))}

### Dynamic propagation

1.
2.
3.

## Counterfactual Attribution

- Smallest plausible fix:
- What would likely improve:
- What would still remain missing:

## Ablation Plan

| Hypothesis | Manipulation | Held Constant | Expected Shift | Metric | Falsifier |
|---|---|---|---|---|---|
| | | | | | |

## Transferable Bottleneck

In tasks with ...

## Actionable Interventions

### Model or policy-training

- 

### Agent policy

- 

### Tool or interface

- 

### Evaluation or product

- 
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Manifest JSON")
    parser.add_argument("--output", required=True, type=Path, help="Output markdown path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = render_report(load_manifest(args.manifest))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report)
    print(args.output)


if __name__ == "__main__":
    main()
