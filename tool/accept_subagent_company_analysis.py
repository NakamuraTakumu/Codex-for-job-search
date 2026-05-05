#!/usr/bin/env python3
"""
Usage:
  python3 tool/accept_subagent_company_analysis.py --run-id RUN <handoff-yaml-or-dir-or-session-jsonl>
  python3 tool/accept_subagent_company_analysis.py --run-id RUN --model gpt-5.4-mini --reasoning-effort medium <handoff-yaml-or-dir>

What it does:
  - Accepts completed company-analysis YAML payloads from tmp handoff files.
  - Falls back to extracting completed payloads from Codex session logs for legacy runs.
  - Rejects raw grandchild research YAML that already contains run_metadata.
  - Adds child-orchestrator run_metadata.
  - Writes tmp/company_analysis/runs/<run_id>/working/<uuid>.yaml.
  - Validates the working YAML.

What it does not do:
  - It does not run mandatory review.
  - It does not write final report/company_analysis/data artifacts.
  - It does not render Markdown output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

from company_analysis_yaml import load_yaml, validate_data


RUN_ROOT = Path("tmp/company_analysis/runs")


def iter_logs(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(path.rglob("*.jsonl"))
    return [path]


def iter_yaml_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted([*path.rglob("*.yaml"), *path.rglob("*.yml")])
    if path.suffix in {".yaml", ".yml"}:
        return [path]
    return []


def handoff_payloads(path: Path) -> list[str]:
    payloads: list[str] = []
    for yaml_path in iter_yaml_files(path):
        try:
            text = yaml_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if text.lstrip().startswith(("version:", "scope_check:")):
            payloads.append(text)
    return payloads


def text_from_message_payload(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in payload.get("content") or []:
        if isinstance(item, dict) and item.get("type") in {"input_text", "output_text"}:
            chunks.append(str(item.get("text", "")))
    return "\n".join(chunks)


def completed_payloads(log_path: Path) -> list[str]:
    payloads: list[str] = []
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return payloads
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = event.get("payload") or {}
        if event.get("type") == "event_msg" and payload.get("type") == "task_complete":
            msg = payload.get("last_agent_message")
            if isinstance(msg, str) and msg.lstrip().startswith("version:"):
                payloads.append(msg)
            continue
        if event.get("type") == "response_item" and payload.get("type") == "message":
            text = text_from_message_payload(payload)
            if "<subagent_notification>" not in text:
                continue
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                continue
            try:
                note = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
            status = note.get("status") or {}
            if not isinstance(status, dict):
                continue
            completed = status.get("completed")
            if isinstance(completed, str) and completed.lstrip().startswith("version:"):
                payloads.append(completed)
    return payloads


def build_run_metadata(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "executor": args.executor,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "fixed_by_parent": True,
    }


def validate_run_id(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9_]+", value):
        raise ValueError("--run-id must match [a-z0-9_]+")
    return value


def accept_yaml(
    raw: str,
    seen: set[str],
    output_dir: Path,
    run_metadata: dict[str, Any],
) -> bool:
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        return False
    if (data.get("scope_check") or {}).get("verdict") == "revise_scope":
        scope_check = data["scope_check"]
        schema_slug = scope_check.get("slug", "<missing>")
        print(f"{schema_slug}: scope revision requested; not accepted as run-scoped artifact")
        seen.add(str(schema_slug))
        return True
    schema_slug = data.get("slug")
    if not isinstance(schema_slug, str) or not schema_slug:
        return False
    if schema_slug in seen:
        return False
    if "run_metadata" in data:
        raise ValueError(
            f"{schema_slug}: grandchild research YAML already contains forbidden run_metadata; "
            "request a clean company-analysis YAML before acceptance",
        )

    data["run_metadata"] = dict(run_metadata)
    output_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = output_dir / f"{uuid.uuid4()}.yaml"
    yaml_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    loaded = load_yaml(yaml_path)
    result = validate_data(loaded, source_name=str(yaml_path))
    if result.issues:
        print(f"{yaml_path}: validation failed", file=sys.stderr)
        for issue in result.issues:
            print(f"  - {issue}", file=sys.stderr)
        return False

    print(f"{schema_slug}: prepared for review -> {yaml_path}")
    seen.add(schema_slug)
    return True


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare completed company-analysis handoff YAML for validation and review."
    )
    parser.add_argument(
        "input",
        help="Handoff YAML file, directory, or legacy Codex session JSONL",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Run identifier for tmp paths. Must match [a-z0-9_]+.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for review-ready working YAML files (default: tmp/company_analysis/runs/<run_id>/working)",
    )
    parser.add_argument(
        "--executor",
        default="company-analysis-child-orchestrator",
        help="run_metadata.executor value (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
        help="Actual grandchild research model for run_metadata.model (default: %(default)s)",
    )
    parser.add_argument(
        "--reasoning-effort",
        default="medium",
        help="Actual grandchild research reasoning effort for run_metadata.reasoning_effort (default: %(default)s)",
    )
    return parser.parse_args(argv[1:])


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.run_id:
        args.run_id = validate_run_id(args.run_id)
    root = Path(args.input)
    output_dir = Path(args.output_dir) if args.output_dir else RUN_ROOT / args.run_id / "working"
    run_metadata = build_run_metadata(args)
    seen: set[str] = set()
    failures = 0
    payloads = handoff_payloads(root)
    if not payloads:
        for log_path in iter_logs(root):
            payloads.extend(completed_payloads(log_path))
    if not payloads:
        print(f"{root}: no completed company-analysis YAML payload found", file=sys.stderr)
        return 1
    for raw in payloads:
        try:
            accepted = accept_yaml(raw, seen, output_dir, run_metadata)
        except Exception as exc:
            print(f"{root}: failed to accept payload: {exc}", file=sys.stderr)
            failures += 1
            continue
        if not accepted:
            print(f"{root}: payload was not accepted", file=sys.stderr)
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
