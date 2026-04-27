#!/usr/bin/env python3
"""
Prepare a filesystem-based review input bundle for company-analysis review agents.

Usage:
  python3 .agents/skills/company-analysis-runner/tool/prepare_review_input.py --run-slug RUN analysis.yaml
  python3 .agents/skills/company-analysis-runner/tool/prepare_review_input.py --run-slug RUN --rendered rendered.md analysis.yaml

What it does:
  - Reads a validator-ready company-analysis YAML.
  - Writes tmp/company_analysis/review_inputs/<run_slug>/<uuid>.md by default.
  - Records the analysis YAML path, optional rendered Markdown path, fixed scope, and expected review output path.

What it does not do:
  - It does not run the review agent.
  - It does not validate the review result.
  - It does not modify the analysis YAML.
"""

from __future__ import annotations

import argparse
import uuid
from pathlib import Path
from typing import Any

import yaml


DEFAULT_INPUT_ROOT = Path("tmp/company_analysis/review_inputs")
DEFAULT_REVIEW_ROOT = Path("tmp/company_analysis/reviews")
REPORT_COMPANY_ANALYSIS_ROOT = Path("report/company_analysis")
COMPANY_ANALYSIS_SKILL_PATH = Path(".agents/skills/company-analysis/SKILL.md")
COMPANY_ANALYSIS_REVIEW_SKILL_PATH = Path(".agents/skills/company-analysis-review/SKILL.md")


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    return data


def require_scalar(data: dict[str, Any], key: str, source: str) -> str:
    value = data.get(key)
    if value is None or isinstance(value, (dict, list)):
        raise ValueError(f"{source}: missing non-empty string key: {key}")
    text = str(value)
    if not text:
        raise ValueError(f"{source}: missing non-empty string key: {key}")
    return text


def format_list(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, list):
        if not value:
            return "[]"
        return "\n".join(f"  - {item}" for item in value)
    return str(value)


def reject_report_company_analysis_path(path: Path, label: str) -> None:
    root = REPORT_COMPANY_ANALYSIS_ROOT.resolve()
    resolved = path.resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError(f"{label} must not be under {REPORT_COMPANY_ANALYSIS_ROOT}")


def build_bundle(
    analysis_path: Path,
    rendered_path: Path | None,
    output_path: Path,
    review_path: Path,
    data: dict[str, Any],
    args: argparse.Namespace,
) -> str:
    scope = data.get("scope")
    if not isinstance(scope, dict):
        raise ValueError(f"{analysis_path}: missing mapping key: scope")

    slug = require_scalar(data, "slug", str(analysis_path))
    company_name = require_scalar(data, "company_name", str(analysis_path))
    survey_date = require_scalar(data, "survey_date", str(analysis_path))

    lines = [
        "# Company Analysis Review Input",
        "",
        "このファイルは `company-analysis-review` 子に渡す review input bundle です。",
        "reviewer はこのファイルに列挙された review target path と reference path だけを読み、review YAML だけを返してください。",
        "",
        "## Fixed Scope",
        "",
        f"- company_name: {company_name}",
        f"- survey_date: {survey_date}",
        f"- slug: {slug}",
        f"- intermediate_artifact_id: {args.artifact_id}",
        f"- scope.user_label: {scope.get('user_label')}",
        f"- scope.target_application_unit: {scope.get('target_application_unit')}",
        f"- scope.hiring_entity_name: {scope.get('hiring_entity_name')}",
        f"- scope.role_family: {scope.get('role_family')}",
        "- scope.alternative_application_units:",
        format_list(scope.get("alternative_application_units")),
        f"- scope.stability_entity_name: {scope.get('stability_entity_name')}",
        "",
        "## Parent Context",
        "",
        f"- user_requested_target: {args.user_requested_target}",
        f"- parent_scope_rationale: {args.parent_scope_rationale}",
        f"- rejected_or_nearby_application_units: {args.rejected_or_nearby_application_units}",
        "",
        "## Review Target Paths",
        "",
        f"- analysis_yaml_path: {analysis_path}",
        f"- rendered_markdown_path: {rendered_path if rendered_path else 'null'}",
        f"- review_output_path: {review_path}",
        "",
        "## Reference Paths",
        "",
        f"- company_analysis_skill_path: {COMPANY_ANALYSIS_SKILL_PATH}",
        f"- company_analysis_review_skill_path: {COMPANY_ANALYSIS_REVIEW_SKILL_PATH}",
        "",
        "## Instructions",
        "",
        "- `.agents/skills/company-analysis-review/SKILL.md` の `company-analysis-review` skill を使う。",
        "- この review input bundle と `analysis_yaml_path` の YAML を現在の唯一の review 対象として扱う。",
        "- `analysis_yaml_path` は親 runner が handoff 受理後に `run_metadata` を追加した validator-ready working YAML である。`run_metadata` の存在だけを company-analysis 子の返却 YAML 違反として扱わない。",
        "- `Reference Paths` は指示準拠確認のためだけに読む。既存分析結果や比較レビューを追加で読まない。",
        "- `rendered_markdown_path` が `null` の場合、render consistency は確認対象外にする。",
        "- 以前の review payload、以前の slug、以前の finding、以前の rendered output は無視する。",
        "- 現在意図している slug は `Fixed Scope` の `slug` とする。slug 文字列だけを理由に scope error としない。",
        "- 固定 scope が user_requested_target や parent_scope_rationale と意味的に矛盾する場合は scope error として扱う。",
        "- `message` と `suggested_fix` は日本語で書く。",
        "- `company-analysis` skill の指示に反していないかを必ず確認する。",
        "- 特に、固定 scope の維持、近接職種への無断置換禁止、会社全体評価への拡張禁止、公式 / 非公式の分離、重要欠損時の追加調査、推定値による `fact_layer` 補完の禁止、親指定 handoff path 以外でのファイル作成・保存・Markdown rendering 禁止を確認する。",
        "- `company-analysis` skill の指示違反に該当する場合は `category: instruction_compliance` を使う。内容上の不整合は最も具体的な category を使う。",
        "- 問題がなければ `passed_checks` に `instruction_compliance` を含める。",
        "- review YAML を `review_output_path` に保存し、同じ YAML を返答にも出す。",
        "- review YAML の外に説明文や Markdown fence を混ぜない。",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a filesystem-based company-analysis review input bundle."
    )
    parser.add_argument("analysis_yaml", help="Validator-ready company-analysis YAML")
    parser.add_argument("--run-slug", required=True, help="Run slug for tmp paths")
    parser.add_argument("--rendered", help="Optional rendered Markdown path")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_INPUT_ROOT),
        help="Review input root directory (default: %(default)s)",
    )
    parser.add_argument(
        "--review-output-dir",
        default=str(DEFAULT_REVIEW_ROOT),
        help="Review output root directory (default: %(default)s)",
    )
    parser.add_argument("--user-requested-target", default="null")
    parser.add_argument("--parent-scope-rationale", default="null")
    parser.add_argument("--rejected-or-nearby-application-units", default="null")
    parser.add_argument(
        "--artifact-id",
        help="UUID filename stem for the review bundle and review output (default: random UUID)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    analysis_path = Path(args.analysis_yaml)
    rendered_path = Path(args.rendered) if args.rendered else None
    data = load_yaml(analysis_path)
    args.artifact_id = args.artifact_id or str(uuid.uuid4())
    try:
        uuid.UUID(args.artifact_id)
    except ValueError as exc:
        raise ValueError("--artifact-id must be a valid UUID") from exc

    output_path = Path(args.output_dir) / args.run_slug / f"{args.artifact_id}.md"
    review_path = Path(args.review_output_dir) / args.run_slug / f"{args.artifact_id}.yaml"
    try:
        reject_report_company_analysis_path(output_path, "--output-dir")
        reject_report_company_analysis_path(review_path, "--review-output-dir")
    except ValueError as exc:
        raise SystemExit(str(exc))
    text = build_bundle(analysis_path, rendered_path, output_path, review_path, data, args)
    output_path.write_text(text, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
