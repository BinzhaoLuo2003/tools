#!/usr/bin/env python3
"""Helpers for scanning arbitrary analysis folders into an artifact catalog."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


IGNORED_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
}

IGNORED_FILE_NAMES = {
    ".DS_Store",
}

TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cfg",
    ".cpp",
    ".csv",
    ".html",
    ".ini",
    ".ipynb",
    ".java",
    ".jl",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".pdf",
    ".py",
    ".r",
    ".rst",
    ".sh",
    ".tex",
    ".toml",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

SNIFF_BYTES = 8192
MAX_TEXT_PREVIEW_CHARS = 600
MAX_REASON_COUNT = 4
MAX_CATEGORY_CANDIDATES = 6

CATEGORY_ORDER = [
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

CATEGORY_HINTS = {
    "task_spec": {
        "path": {"task", "tasks", "prompt", "brief", "spec", "contract", "instruction", "question"},
        "content": {"objective", "reference", "evaluation", "criteria", "rubric", "constraints"},
    },
    "execution_summary": {
        "path": {"execution", "summary", "overview", "session", "run", "stats", "metadata"},
        "content": {"turns", "tool_calls_count", "final_response_preview", "agent_type", "system_type"},
    },
    "tool_trace": {
        "path": {"tool", "tools", "trace", "calls", "actions", "journal", "transcript", "logs"},
        "content": {"exec_command", "write_stdin", "tool call", "apply_patch", "command"},
    },
    "reconstructed_code": {
        "path": {"reconstructed", "code", "notebook", "script", "logic", "pipeline"},
        "content": {"def ", "class ", "import ", "function", "notebook"},
    },
    "reviewer_context": {
        "path": {"review", "reviewer", "judge", "context", "findings", "comments"},
        "content": {"reviewer", "judge", "context", "evidence", "turning point"},
    },
    "final_response": {
        "path": {"final", "response", "answer", "submission", "deliverable", "result", "memo"},
        "content": {"final response", "final answer", "submission"},
    },
    "grade_report": {
        "path": {"grade", "grading", "grader", "rubric", "score", "evaluation"},
        "content": {"rubric_evaluation", "letter_grade", "score"},
    },
    "technical_analysis": {
        "path": {"technical", "analysis", "audit", "diagnostic", "forensics", "debug"},
        "content": {"technical analysis", "root cause", "failure mode"},
    },
    "trajectory": {
        "path": {"trajectory", "trace", "messages", "conversation", "turns", "history"},
        "content": {"role", "assistant", "user", "messages", "trajectory"},
    },
}


def maybe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def tokenize(value: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def read_text_preview(path: Path) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    try:
        data = path.read_bytes()[:SNIFF_BYTES]
    except OSError:
        return None, None

    if not data:
        return "", {"encoding": "empty", "preview": ""}

    try:
        text = data.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="ignore")
        encoding = "utf-8-ignore"

    printable = sum(1 for char in text if char.isprintable() or char in "\n\r\t")
    ratio = printable / max(len(text), 1)
    if ratio < 0.75 and path.suffix.lower() not in TEXT_EXTENSIONS:
        return None, None

    preview = text[:MAX_TEXT_PREVIEW_CHARS]
    metadata: Dict[str, Any] = {
        "encoding": encoding,
        "preview": preview,
        "preview_headings": [
            line.strip().lstrip("#").strip()
            for line in preview.splitlines()
            if line.strip().startswith("#")
        ][:5],
    }
    return preview, metadata


def read_json_metadata(path: Path) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    try:
        parsed = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, None

    metadata: Dict[str, Any] = {"json_type": type(parsed).__name__}
    if isinstance(parsed, dict):
        metadata["json_keys"] = sorted(parsed.keys())[:25]
    elif isinstance(parsed, list):
        metadata["json_length"] = len(parsed)
        if parsed and isinstance(parsed[0], dict):
            metadata["json_keys"] = sorted(parsed[0].keys())[:25]
    return parsed, metadata


def infer_file_family(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".json", ".jsonl"}:
        return "json"
    if suffix in {".md", ".rst", ".txt", ".log", ".tex"}:
        return "text"
    if suffix in {".py", ".sh", ".c", ".cc", ".cpp", ".java", ".r", ".jl"}:
        return "code"
    if suffix in {".csv", ".tsv"}:
        return "table"
    if suffix in {".yml", ".yaml", ".toml", ".ini", ".cfg"}:
        return "config"
    return "other"


def score_category(
    label: str,
    path_tokens: Sequence[str],
    content_tokens: Sequence[str],
    metadata: Dict[str, Any],
    preview: Optional[str],
    suffix: str,
) -> Tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []
    hints = CATEGORY_HINTS[label]

    path_hits = sorted(set(path_tokens) & hints["path"])
    if path_hits:
        score += min(len(path_hits) * 2, 6)
        reasons.append("path tokens: " + ", ".join(path_hits[:3]))

    content_hits = sorted(set(content_tokens) & hints["content"])
    if content_hits:
        score += min(len(content_hits) * 2, 6)
        reasons.append("content tokens: " + ", ".join(content_hits[:3]))

    json_keys = set(metadata.get("json_keys", []))
    if label == "task_spec":
        if {"prompt", "goal", "prompt_title", "title"} & json_keys:
            score += 5
            reasons.append("task-like json keys")
        if {"evaluation_criteria", "reference_answer", "answer"} & json_keys:
            score += 3
            reasons.append("rubric/reference fields")
    elif label == "execution_summary":
        if {"turns", "tool_calls_count", "tool_calls_by_category"} & json_keys:
            score += 5
            reasons.append("execution summary counters")
        if {"model", "system_name", "agent_type", "system_type"} & json_keys:
            score += 3
            reasons.append("system identity fields")
    elif label == "grade_report":
        if {"score", "rubric_evaluation"} <= json_keys or {"score", "rubric_evaluation"} & json_keys:
            score += 6
            reasons.append("grading json keys")
        if {"letter_grade", "common_mistakes_found"} & json_keys:
            score += 2
            reasons.append("grade detail fields")
    elif label == "trajectory":
        if {"messages", "trajectory", "events", "turns"} & json_keys:
            score += 5
            reasons.append("trajectory json keys")
    elif label == "tool_trace":
        if preview and any(token in preview.lower() for token in ("exec_command", "write_stdin", "apply_patch")):
            score += 4
            reasons.append("tool invocation preview")
    elif label == "final_response":
        if preview and any(token in preview.lower() for token in ("final response", "final answer", "submission")):
            score += 4
            reasons.append("final-response heading")
    elif label == "reviewer_context":
        if preview and any(token in preview.lower() for token in ("reviewer context", "judge context")):
            score += 4
            reasons.append("reviewer heading")
    elif label == "technical_analysis":
        if preview and "technical analysis" in preview.lower():
            score += 4
            reasons.append("technical-analysis heading")

    if label == "reconstructed_code" and suffix in {".py", ".ipynb"}:
        score += 1
        reasons.append("code artifact extension")
    if label == "trajectory" and suffix in {".json", ".jsonl", ".md"}:
        score += 1
        reasons.append("trace-friendly extension")

    return score, reasons[:MAX_REASON_COUNT]


def classify_file(
    path_tokens: Sequence[str],
    content_tokens: Sequence[str],
    metadata: Dict[str, Any],
    preview: Optional[str],
    suffix: str,
) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    for label in CATEGORY_ORDER:
        score, reasons = score_category(label, path_tokens, content_tokens, metadata, preview, suffix)
        if score > 0:
            scored.append({"label": label, "score": score, "reasons": reasons})
    scored.sort(key=lambda item: (-item["score"], item["label"]))
    return scored[:MAX_CATEGORY_CANDIDATES]


def build_file_record(path: Path, source_root: Path, repo_root: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    preview: Optional[str] = None
    metadata: Dict[str, Any] = {}

    json_payload = None
    if suffix == ".json":
        json_payload, json_metadata = read_json_metadata(path)
        if json_metadata:
            metadata.update(json_metadata)

    if suffix in TEXT_EXTENSIONS or not metadata:
        text_preview, text_metadata = read_text_preview(path)
        if text_metadata:
            preview = text_preview
            metadata.update(text_metadata)

    path_tokens = tokenize(str(path.relative_to(source_root)))
    content_tokens: List[str] = []
    if preview:
        content_tokens.extend(tokenize(preview))
    for key in metadata.get("json_keys", []):
        content_tokens.extend(tokenize(key))

    record = {
        "path": maybe_rel(path, repo_root),
        "absolute_path": str(path),
        "source_root": maybe_rel(source_root, repo_root),
        "relative_to_source_root": maybe_rel(path, source_root),
        "directory": maybe_rel(path.parent, repo_root),
        "filename": path.name,
        "stem": path.stem,
        "suffix": suffix,
        "size_bytes": path.stat().st_size,
        "file_family": infer_file_family(path),
        "metadata": metadata,
        "category_candidates": classify_file(path_tokens, content_tokens, metadata, preview, suffix),
    }
    if isinstance(json_payload, dict):
        record["metadata"]["json_key_count"] = len(json_payload)
    return record


def iter_regular_files(root: Path) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in IGNORED_DIR_NAMES
        ]
        current_path = Path(current_root)
        for filename in filenames:
            if filename in IGNORED_FILE_NAMES:
                continue
            path = current_path / filename
            if path.is_file():
                yield path


def accumulate_directory_stats(
    records: Sequence[Dict[str, Any]],
    source_root: Path,
    repo_root: Path,
) -> List[Dict[str, Any]]:
    stats: Dict[str, Dict[str, Any]] = {}

    for record in records:
        file_path = Path(record["absolute_path"])
        category_candidates = record.get("category_candidates", [])
        if not category_candidates:
            continue

        current = file_path.parent
        while True:
            if current == source_root.parent or not str(current).startswith(str(source_root)):
                break

            key = str(current)
            entry = stats.setdefault(
                key,
                {
                    "path": maybe_rel(current, repo_root),
                    "absolute_path": str(current),
                    "source_root": maybe_rel(source_root, repo_root),
                    "descendant_file_count": 0,
                    "distinct_categories": set(),
                    "category_best": {},
                    "distance_sum": 0,
                    "distance_count": 0,
                },
            )
            entry["descendant_file_count"] += 1
            distance = len(file_path.relative_to(current).parts) - 1
            entry["distance_sum"] += max(distance, 0)
            entry["distance_count"] += 1

            for candidate in category_candidates:
                label = candidate["label"]
                entry["distinct_categories"].add(label)
                best = entry["category_best"].get(label)
                if best is None or candidate["score"] > best["score"]:
                    entry["category_best"][label] = {
                        "score": candidate["score"],
                        "path": record["path"],
                        "reasons": candidate["reasons"],
                    }

            if current == source_root:
                break
            current = current.parent

    candidates: List[Dict[str, Any]] = []
    for entry in stats.values():
        if not entry["category_best"]:
            continue
        distinct_count = len(entry["distinct_categories"])
        total_score = sum(item["score"] for item in entry["category_best"].values())
        avg_distance = entry["distance_sum"] / max(entry["distance_count"], 1)
        normalized = (total_score + distinct_count) / (
            1 + 0.45 * avg_distance + 0.12 * entry["descendant_file_count"]
        )
        candidates.append(
            {
                "path": entry["path"],
                "absolute_path": entry["absolute_path"],
                "source_root": entry["source_root"],
                "score": round(normalized, 3),
                "descendant_file_count": entry["descendant_file_count"],
                "distinct_categories": sorted(entry["distinct_categories"]),
                "artifact_support": [
                    {
                        "label": label,
                        "score": details["score"],
                        "path": details["path"],
                        "reasons": details["reasons"],
                    }
                    for label, details in sorted(
                        entry["category_best"].items(),
                        key=lambda item: (-item[1]["score"], item[0]),
                    )
                ],
            }
        )

    candidates.sort(
        key=lambda item: (
            -item["score"],
            -len(item["distinct_categories"]),
            item["descendant_file_count"],
            item["path"],
        )
    )
    return candidates


def discover_artifacts(
    input_dirs: Sequence[Path],
    repo_root: Path,
) -> Dict[str, Any]:
    file_records: List[Dict[str, Any]] = []
    directory_candidates: List[Dict[str, Any]] = []

    for input_dir in input_dirs:
        input_dir = input_dir.resolve()
        source_records = [build_file_record(path, input_dir, repo_root) for path in iter_regular_files(input_dir)]
        file_records.extend(source_records)
        directory_candidates.extend(accumulate_directory_stats(source_records, input_dir, repo_root))

    deduped_dirs: Dict[str, Dict[str, Any]] = {}
    for candidate in directory_candidates:
        current = deduped_dirs.get(candidate["absolute_path"])
        if current is None or candidate["score"] > current["score"]:
            deduped_dirs[candidate["absolute_path"]] = candidate

    sorted_dirs = sorted(
        deduped_dirs.values(),
        key=lambda item: (
            -item["score"],
            -len(item["distinct_categories"]),
            item["descendant_file_count"],
            item["path"],
        ),
    )

    return {
        "schema_version": 1,
        "repo_root": str(repo_root),
        "scanned_roots": [maybe_rel(path.resolve(), repo_root) for path in input_dirs],
        "file_count": len(file_records),
        "files": sorted(file_records, key=lambda item: item["path"]),
        "directory_candidates": sorted_dirs,
    }


def load_catalog(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def save_catalog(catalog: Dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog, indent=2))


def resolve_directory_entry(catalog: Dict[str, Any], requested_dir: Optional[str]) -> Optional[Dict[str, Any]]:
    if not catalog.get("directory_candidates"):
        directory_candidates: List[Dict[str, Any]] = []
    else:
        directory_candidates = catalog["directory_candidates"]
    if requested_dir is None:
        return directory_candidates[0] if directory_candidates else None

    requested_path = Path(requested_dir).resolve()
    for entry in directory_candidates:
        absolute = Path(entry["absolute_path"]).resolve()
        if absolute == requested_path:
            return entry
        if entry["path"] == requested_dir:
            return entry

    if requested_path.is_dir():
        repo_root = Path(catalog.get("repo_root", Path.cwd())).resolve()
        return {
            "path": maybe_rel(requested_path, repo_root),
            "absolute_path": str(requested_path),
            "source_root": None,
            "score": 0.0,
            "descendant_file_count": 0,
            "distinct_categories": [],
            "artifact_support": [],
        }
    return None


def _is_descendant(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def select_artifacts_for_directory(
    catalog: Dict[str, Any],
    directory_entry: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    directory_root = Path(directory_entry["absolute_path"]).resolve()
    best_by_label: Dict[str, Dict[str, Any]] = {}
    candidates_by_label: Dict[str, List[Dict[str, Any]]] = {}

    for file_record in catalog.get("files", []):
        file_path = Path(file_record["absolute_path"]).resolve()
        if not _is_descendant(file_path, directory_root):
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


def build_case_id(directory_entry: Optional[Dict[str, Any]], fallback: str = "pattern-analysis-case") -> str:
    if not directory_entry:
        return fallback
    return Path(directory_entry["absolute_path"]).name or fallback
