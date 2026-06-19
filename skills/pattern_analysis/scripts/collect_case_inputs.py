#!/usr/bin/env python3
"""Build a case manifest from a discovered artifact catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from artifact_catalog import build_case_id, load_catalog, resolve_directory_entry

CANONICAL_ARTIFACT_LABELS = [
    "task_spec",
    "execution_summary",
    "tool_trace",
    "reconstructed_code",
    "reviewer_context",
    "final_response",
    "grade_report",
    "technical_analysis",
    "trajectory",
]


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict):
        return payload
    return None


def extract_task_fields(task_spec: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    task_spec = task_spec or {}
    return {
        "title": task_spec.get("title") or task_spec.get("prompt_title"),
        "goal": task_spec.get("goal") or task_spec.get("prompt"),
        "reference_answer": task_spec.get("reference_answer") or task_spec.get("answer"),
        "evaluation_criteria": task_spec.get("evaluation_criteria"),
        "notes": task_spec.get("notes") or task_spec.get("dataset_description"),
    }


def is_descendant(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def select_artifacts_for_scope(
    catalog: Dict[str, Any],
    directory_entries: Sequence[Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    roots = [Path(entry["absolute_path"]).resolve() for entry in directory_entries]
    best_by_label: Dict[str, Dict[str, Any]] = {}
    candidates_by_label: Dict[str, List[Dict[str, Any]]] = {}

    for file_record in catalog.get("files", []):
        file_path = Path(file_record["absolute_path"]).resolve()
        if not any(is_descendant(file_path, root) for root in roots):
            continue

        for candidate in file_record.get("category_candidates", []):
            label = candidate["label"]
            candidate_record = {
                "path": file_record["path"],
                "absolute_path": file_record["absolute_path"],
                "score": candidate["score"],
                "reasons": candidate["reasons"],
                "file_family": file_record["file_family"],
            }
            candidates_by_label.setdefault(label, []).append(candidate_record)
            current = best_by_label.get(label)
            if current is None or candidate_record["score"] > current["score"]:
                best_by_label[label] = candidate_record

    for label in candidates_by_label:
        candidates_by_label[label].sort(key=lambda item: (-item["score"], item["path"]))

    return best_by_label, candidates_by_label


def summarize_case_from_catalog(
    catalog: Dict[str, Any],
    directory_entries: Sequence[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    best_by_label, candidates_by_label = select_artifacts_for_scope(catalog, directory_entries)

    execution = load_json(Path(best_by_label["execution_summary"]["absolute_path"])) if "execution_summary" in best_by_label else {}
    grade = load_json(Path(best_by_label["grade_report"]["absolute_path"])) if "grade_report" in best_by_label else {}
    task_spec = load_json(Path(best_by_label["task_spec"]["absolute_path"])) if "task_spec" in best_by_label else {}

    score = (grade or {}).get("score") or {}
    rubric = (grade or {}).get("rubric_evaluation") or {}

    scope_paths = [entry["path"] for entry in directory_entries]
    scope_scores = [entry["score"] for entry in directory_entries]
    distinct_categories = sorted(
        {
            category
            for entry in directory_entries
            for category in entry.get("distinct_categories", [])
        }
    )

    run_summary = {
        "run_dir": scope_paths[0] if len(scope_paths) == 1 else "; ".join(scope_paths),
        "summary_dir": scope_paths[0] if len(scope_paths) == 1 else "; ".join(scope_paths),
        "scope_dirs": scope_paths,
        "available_files": {
            label: details["path"]
            for label, details in best_by_label.items()
            if label in CANONICAL_ARTIFACT_LABELS and label != "task_spec"
        },
        "artifact_candidates": {
            label: candidates[:5]
            for label, candidates in candidates_by_label.items()
            if label in CANONICAL_ARTIFACT_LABELS
        },
        "system_type": (execution or {}).get("agent_type") or (execution or {}).get("system_type"),
        "system_name": (execution or {}).get("model") or (execution or {}).get("system_name"),
        "turns": (execution or {}).get("turns"),
        "tool_calls_count": (execution or {}).get("tool_calls_count"),
        "tool_calls_by_category": (execution or {}).get("tool_calls_by_category"),
        "score": score.get("value") if isinstance(score, dict) else score,
        "max_score": score.get("max") if isinstance(score, dict) else None,
        "letter_grade": score.get("letter_grade") if isinstance(score, dict) else None,
        "grade_description": score.get("description") if isinstance(score, dict) else None,
        "final_response_preview": (execution or {}).get("final_response_preview"),
        "rubric_key_elements_present": rubric.get("key_elements_present", []),
        "rubric_key_elements_missing": rubric.get("key_elements_missing", []),
        "rubric_common_mistakes_found": rubric.get("common_mistakes_found", []),
        "selected_scope": {
            "directories": scope_paths,
            "scores": scope_scores,
            "distinct_categories": distinct_categories,
        },
    }

    task_fields = extract_task_fields(task_spec)
    task_metadata = {
        "task_spec_path": best_by_label.get("task_spec", {}).get("path"),
        "task_title": task_fields["title"],
        "task_goal": task_fields["goal"],
        "reference_answer": task_fields["reference_answer"],
        "evaluation_criteria": task_fields["evaluation_criteria"],
        "task_notes": task_fields["notes"],
    }
    return run_summary, task_metadata


def build_manifest_from_catalog(
    catalog: Dict[str, Any],
    case_id: Optional[str],
    case_dirs: Sequence[str],
    compare_case_dirs: Sequence[str],
) -> Dict[str, Any]:
    if case_dirs:
        primary_entries = []
        for requested_dir in case_dirs:
            entry = resolve_directory_entry(catalog, requested_dir)
            if entry is None:
                raise ValueError(f"Could not resolve primary directory: {requested_dir}")
            primary_entries.append(entry)
    else:
        primary_entry = resolve_directory_entry(catalog, None)
        if primary_entry is None:
            raise ValueError("Could not resolve a primary case directory from the catalog.")
        primary_entries = [primary_entry]

    primary_run, task_metadata = summarize_case_from_catalog(catalog, primary_entries)

    comparison_runs = []
    for requested_dir in compare_case_dirs:
        entry = resolve_directory_entry(catalog, requested_dir)
        if entry is None:
            raise ValueError(f"Could not resolve comparison directory: {requested_dir}")
        comparison_summary, _ = summarize_case_from_catalog(catalog, [entry])
        comparison_runs.append(comparison_summary)

    return {
        "case_id": case_id or build_case_id(primary_entries[0]),
        "task_spec_path": task_metadata["task_spec_path"],
        "task_title": task_metadata["task_title"],
        "task_goal": task_metadata["task_goal"],
        "reference_answer": task_metadata["reference_answer"],
        "evaluation_criteria": task_metadata["evaluation_criteria"],
        "task_notes": task_metadata["task_notes"],
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
            "discovery_catalog_roots": catalog.get("scanned_roots", []),
        },
    }


def write_manifest(manifest: Dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        required=True,
        type=Path,
        help="Artifact catalog JSON generated by discover_case_artifacts.py",
    )
    parser.add_argument("--case-id", help="Public case identifier such as sample-lab-automation-case")
    parser.add_argument("--output", required=True, type=Path, help="Output manifest JSON path")
    parser.add_argument(
        "--case-dir",
        action="append",
        default=[],
        help="Directory selected from the catalog as part of the primary case scope. Repeat to merge multiple directories.",
    )
    parser.add_argument(
        "--compare-case-dir",
        action="append",
        default=[],
        help="Optional comparison directories selected from the catalog",
    )
    parser.add_argument(
        "--cleanup-catalog",
        action="store_true",
        help="Delete the catalog file after writing the manifest",
    )
    return parser.parse_args()


def maybe_cleanup_catalog(catalog_path: Optional[Path], cleanup: bool) -> None:
    if cleanup and catalog_path and catalog_path.exists():
        catalog_path.unlink()


def main() -> None:
    args = parse_args()
    catalog = load_catalog(args.catalog.resolve())
    manifest = build_manifest_from_catalog(
        catalog=catalog,
        case_id=args.case_id,
        case_dirs=args.case_dir,
        compare_case_dirs=args.compare_case_dir,
    )
    write_manifest(manifest, args.output.resolve())
    maybe_cleanup_catalog(args.catalog.resolve(), args.cleanup_catalog)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
