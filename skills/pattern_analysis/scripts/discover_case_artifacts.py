#!/usr/bin/env python3
"""Scan arbitrary analysis directories and emit an artifact catalog."""

from __future__ import annotations

import argparse
from pathlib import Path

from artifact_catalog import discover_artifacts, save_catalog


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        action="append",
        required=True,
        type=Path,
        help="Directory to scan. Repeat to scan multiple trees.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Base path used for relative paths in the output catalog.",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output catalog JSON path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalog = discover_artifacts(args.input_dir, args.repo_root.resolve())
    save_catalog(catalog, args.output.resolve())
    print(args.output.resolve())


if __name__ == "__main__":
    main()
