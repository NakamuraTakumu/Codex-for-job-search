#!/usr/bin/env python3
"""
Usage:
  python3 tool/check_company_analysis_yaml.py path/to/file.yaml [path/to/file2.yaml ...]

What it does:
  - Checks child-orchestrator working or run-scoped company-analysis YAML files for required
    fields and basic schema validity.
  - Verifies score ranges, 0.1 increments, slug/file consistency, source URLs,
    source tier/kind, and minimum official-source coverage.
  - Requires child-orchestrator-added run_metadata. Raw company-analysis
    research output must not include run_metadata and should pass
    through child-orchestrator intake first.

What it does not do:
  - It does not modify any file.
  - It does not render Markdown output.
"""

from __future__ import annotations

import sys
from pathlib import Path

from company_analysis_yaml import load_yaml, validate_data


def expand_inputs(raw_inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in raw_inputs:
        path = Path(raw)
        if path.is_dir():
            paths.extend(sorted(path.rglob("*.yaml")))
        else:
            paths.append(path)
    return paths


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print((__doc__ or "").strip())
        return 2

    bad = 0
    for path in expand_inputs(argv[1:]):
        if not path.exists():
            print(f"{path}: not found")
            bad = 1
            continue
        try:
            data = load_yaml(path)
        except Exception as exc:
            print(f"{path}:")
            print(f"  - failed to parse YAML: {exc}")
            bad = 1
            continue
        result = validate_data(data, source_name=str(path))
        if result.issues:
            print(f"{path}:")
            for issue in result.issues:
                print(f"  - {issue}")
            bad = 1
        else:
            print(f"{path}: OK")
    return bad


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
