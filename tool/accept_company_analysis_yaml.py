#!/usr/bin/env python3
"""
Usage:
  python3 tool/accept_company_analysis_yaml.py <slug> < input.yaml

What it does:
  - Reads a company-analysis YAML object from stdin.
  - Rejects raw child YAML that already contains run_metadata.
  - Adds run_metadata with the runner defaults.
  - Writes tmp/company_analysis/working/<uuid>.yaml for validation and review.
  - Validates the working YAML.

What it does not do:
  - It does not run mandatory review.
  - It does not write final report/company_analysis/data artifacts.
  - It does not render Markdown output.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import yaml
from company_analysis_yaml import load_yaml, validate_data


WORKING_DIR = Path("tmp/company_analysis/working")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print((__doc__ or "").strip(), file=sys.stderr)
        return 2

    slug = argv[1]
    raw = sys.stdin.read()
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        print("stdin did not contain a YAML mapping", file=sys.stderr)
        return 2
    if (data.get("scope_check") or {}).get("verdict") == "revise_scope":
        print("scope revision requested; not accepting as final artifact", file=sys.stderr)
        return 1
    if "run_metadata" in data:
        print(
            "child YAML already contains forbidden run_metadata; "
            "request a clean company-analysis YAML before acceptance",
            file=sys.stderr,
        )
        return 1

    data["run_metadata"] = {
        "executor": "company-analysis-runner",
        "model": "gpt-5.4-mini",
        "reasoning_effort": "medium",
        "fixed_by_parent": True,
    }

    if data.get("slug") != slug:
        print(f"slug mismatch: data has {data.get('slug')!r}, expected {slug!r}", file=sys.stderr)
        return 1

    WORKING_DIR.mkdir(parents=True, exist_ok=True)
    out_path = WORKING_DIR / f"{uuid.uuid4()}.yaml"
    out_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    loaded = load_yaml(out_path)
    result = validate_data(loaded, source_name=str(out_path))
    if result.issues:
        print(f"{out_path}: validation failed", file=sys.stderr)
        for issue in result.issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1
    print(f"{slug}: prepared for review -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
