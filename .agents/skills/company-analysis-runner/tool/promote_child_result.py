#!/usr/bin/env python3
"""
Promote an accepted company-analysis child result to report artifacts.

Usage:
  python3 .agents/skills/company-analysis-runner/tool/promote_child_result.py child_result.yaml
  python3 .agents/skills/company-analysis-runner/tool/promote_child_result.py --overwrite child_result.yaml

What it does:
  - Reads one child result YAML whose status is accepted and whose adopted
    grandchild review agent is recorded.
  - Copies the accepted analysis YAML, rendered Markdown, and review YAML to:
      document/report/company_analysis/data/<run_id>.yaml
      document/report/company_analysis/companies/<run_id>.md
      document/report/company_analysis/reviews/<run_id>.yaml
  - Prints a YAML summary of promoted paths.

What it does not do:
  - It does not judge the analysis content.
  - It does not validate or rewrite the child artifacts.
  - It does not overwrite existing report artifacts unless --overwrite is set.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Any

import yaml


DEFAULT_REPORT_ROOT = Path("document/report/company_analysis")


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    return data


def require_run_id(value: Any) -> str:
    run_id = str(value or "")
    if not re.fullmatch(r"[a-z0-9_]+", run_id):
        raise ValueError("child result run_id must match [a-z0-9_]+")
    return run_id


def require_existing_file(value: Any, key: str) -> Path:
    if not value:
        raise ValueError(f"child result missing required path: {key}")
    path = Path(str(value))
    if not path.is_file():
        raise ValueError(f"{key} does not exist or is not a file: {path}")
    return path


def require_adopted_review_agent(child_result: dict[str, Any]) -> None:
    spawned_agents = child_result.get("spawned_agents")
    if not isinstance(spawned_agents, list):
        raise ValueError("child result spawned_agents must be a list")
    for agent in spawned_agents:
        if not isinstance(agent, dict):
            continue
        if agent.get("role") != "grandchild_review":
            continue
        if agent.get("adopted") is not True and agent.get("status") != "adopted":
            continue
        if not agent.get("agent_id"):
            continue
        if not agent.get("output_path"):
            continue
        return
    raise ValueError(
        "child result status is accepted but no adopted grandchild_review agent "
        "with agent_id and output_path is recorded"
    )


def copy_file(source: Path, destination: Path, overwrite: bool) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"destination already exists: {destination}")
    shutil.copy2(source, destination)
    return str(destination)


def promote(child_result_path: Path, report_root: Path, overwrite: bool) -> dict[str, Any]:
    child_result = load_yaml(child_result_path)
    status = child_result.get("status")
    if status != "accepted":
        raise ValueError(f"child result status must be accepted, got: {status!r}")
    require_adopted_review_agent(child_result)

    run_id = require_run_id(child_result.get("run_id"))
    analysis_yaml = require_existing_file(child_result.get("analysis_yaml_path"), "analysis_yaml_path")
    rendered_markdown = require_existing_file(
        child_result.get("rendered_markdown_path"), "rendered_markdown_path"
    )
    review_yaml = require_existing_file(child_result.get("review_yaml_path"), "review_yaml_path")

    promoted_paths = {
        "analysis_yaml_path": copy_file(
            analysis_yaml, report_root / "data" / f"{run_id}.yaml", overwrite
        ),
        "rendered_markdown_path": copy_file(
            rendered_markdown, report_root / "companies" / f"{run_id}.md", overwrite
        ),
        "review_yaml_path": copy_file(
            review_yaml, report_root / "reviews" / f"{run_id}.yaml", overwrite
        ),
    }
    return {
        "status": "promoted",
        "run_id": run_id,
        "source_child_result_path": str(child_result_path),
        "report_root": str(report_root),
        "promoted_paths": promoted_paths,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("child_result_yaml", type=Path)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    summary = promote(args.child_result_yaml, args.report_root, args.overwrite)
    print(yaml.safe_dump(summary, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
