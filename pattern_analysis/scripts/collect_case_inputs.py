#!/usr/bin/env python3
"""Collect a structured manifest for a generic pattern-analysis case study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


COMMON_ARTIFACTS = [
    "execution_summary.json",
    "tool_calls.md",
    "reconstructed_code.md",
    "judge_context.md",
    "final_response.md",
    "grade_report.json",
    "technical_analysis.md",
    "trajectory.json",
]


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def maybe_rel(path: Optional[Path], root: Path) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def extract_task_fields(task_spec: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    task_spec = task_spec or {}
    return {
        "title": task_spec.get("title") or task_spec.get("prompt_title"),
        "goal": task_spec.get("goal") or task_spec.get("prompt"),
        "reference_answer": task_spec.get("reference_answer") or task_spec.get("answer"),
        "evaluation_criteria": task_spec.get("evaluation_criteria"),
        "notes": task_spec.get("notes") or task_spec.get("dataset_description"),
    }


def summarize_run(run_dir: Path, repo_root: Path) -> Dict[str, Any]:
    summary_dir = run_dir / "summary"
    files = {name: summary_dir / name for name in COMMON_ARTIFACTS}

    execution = load_json(files["execution_summary.json"]) or {}
    grade = load_json(files["grade_report.json"]) or {}

    score = grade.get("score") or {}
    rubric = grade.get("rubric_evaluation") or {}

    return {
        "run_dir": maybe_rel(run_dir, repo_root),
        "summary_dir": maybe_rel(summary_dir, repo_root),
        "available_files": {
            name: maybe_rel(path, repo_root) for name, path in files.items() if path.exists()
        },
        "system_type": execution.get("agent_type") or execution.get("system_type"),
        "system_name": execution.get("model") or execution.get("system_name"),
        "turns": execution.get("turns"),
        "tool_calls_count": execution.get("tool_calls_count"),
        "tool_calls_by_category": execution.get("tool_calls_by_category"),
        "score": score.get("value"),
        "max_score": score.get("max"),
        "letter_grade": score.get("letter_grade"),
        "grade_description": score.get("description"),
        "final_response_preview": execution.get("final_response_preview"),
        "rubric_key_elements_present": rubric.get("key_elements_present", []),
        "rubric_key_elements_missing": rubric.get("key_elements_missing", []),
        "rubric_common_mistakes_found": rubric.get("common_mistakes_found", []),
    }


def build_manifest(
    repo_root: Path,
    case_id: str,
    task_spec_path: Optional[Path],
    run_dir: Path,
    compare_run_dirs: List[Path],
) -> Dict[str, Any]:
    task_spec = load_json(task_spec_path) if task_spec_path else None
    task_fields = extract_task_fields(task_spec)

    primary_run = summarize_run(run_dir, repo_root)
    comparison_runs = [summarize_run(path, repo_root) for path in compare_run_dirs]

    return {
        "case_id": case_id,
        "task_spec_path": maybe_rel(task_spec_path, repo_root),
        "task_title": task_fields["title"],
        "task_goal": task_fields["goal"],
        "reference_answer": task_fields["reference_answer"],
        "evaluation_criteria": task_fields["evaluation_criteria"],
        "task_notes": task_fields["notes"],
        "primary_run": primary_run,
        "comparison_runs": comparison_runs,
        "analysis_targets": {
            "recommended_primary_artifacts": [
                "task spec",
                "execution summary",
                "tool trace",
                "reconstructed code",
                "reviewer context",
                "final response",
                "grader report",
            ],
            "optional_primary_artifacts": [
                "technical analysis",
                "raw trajectory",
            ],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True, help="Public case identifier such as sample-lab-automation-case")
    parser.add_argument("--task-spec", type=Path, help="Optional task spec JSON path")
    parser.add_argument("--run-dir", required=True, type=Path, help="Target run directory")
    parser.add_argument(
        "--compare-run-dir",
        action="append",
        default=[],
        type=Path,
        help="Optional comparison run directories",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Base path used for relative paths in the output manifest",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output manifest JSON path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_manifest(
        repo_root=args.repo_root.resolve(),
        case_id=args.case_id,
        task_spec_path=args.task_spec.resolve() if args.task_spec else None,
        run_dir=args.run_dir.resolve(),
        compare_run_dirs=[path.resolve() for path in args.compare_run_dir],
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2))
    print(args.output)


if __name__ == "__main__":
    main()
