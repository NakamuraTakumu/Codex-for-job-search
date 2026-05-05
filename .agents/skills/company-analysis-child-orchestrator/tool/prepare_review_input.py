#!/usr/bin/env python3
"""
Prepare a filesystem-based review input bundle for company-analysis review agents.

Usage:
  python3 .agents/skills/company-analysis-child-orchestrator/tool/prepare_review_input.py --run-id RUN --fixed-input-yaml fixed.yaml --expected-handoff-path handoff.yaml --handoff-match matched --unauthorized-outputs none_observed --unexpected-rendering none_observed --child-run-metadata-present false --requested-target TARGET --scope-rationale RATIONALE analysis.yaml
  python3 .agents/skills/company-analysis-child-orchestrator/tool/prepare_review_input.py --run-id RUN --fixed-input-yaml fixed.yaml --expected-handoff-path handoff.yaml --handoff-match matched --unauthorized-outputs none_observed --unexpected-rendering none_observed --child-run-metadata-present false --requested-target TARGET --scope-rationale RATIONALE --rendered rendered.md analysis.yaml

What it does:
  - Reads a validator-ready company-analysis YAML.
  - Writes tmp/company_analysis/runs/<run_id>/review_inputs/<uuid>.md by default.
  - Records the analysis YAML path, optional rendered Markdown path, orchestrator-fixed scope, handoff observations, and expected review output path.

What it does not do:
  - It does not run the review agent.
  - It does not validate the review result.
  - It does not modify the analysis YAML.
"""

from __future__ import annotations

import argparse
import re
import uuid
from pathlib import Path
from typing import Any

import yaml


DEFAULT_RUN_ROOT = Path("tmp/company_analysis/runs")
REPORT_COMPANY_ANALYSIS_ROOTS = [
    Path("document/report/company_analysis"),
    Path("report/company_analysis"),
]
COMPANY_ANALYSIS_SKILL_PATH = Path(".agents/skills/company-analysis/SKILL.md")
COMPANY_ANALYSIS_REVIEW_SKILL_PATH = Path(".agents/skills/company-analysis-review/SKILL.md")
COMPANY_ANALYSIS_OUTPUT_CONTRACT_PATH = Path(
    ".agents/skills/company-analysis/references/output-contract.md"
)
COMPANY_ANALYSIS_SCOPE_CHECK_PATH = Path(
    ".agents/skills/company-analysis/references/scope-check.md"
)
COMPANY_ANALYSIS_SCORING_PATH = Path(
    ".agents/skills/company-analysis/references/scoring.md"
)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    return data


def require_run_id(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9_]+", value):
        raise ValueError("--run-id must match [a-z0-9_]+")
    return value


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
    resolved = path.resolve()
    for root_path in REPORT_COMPANY_ANALYSIS_ROOTS:
        root = root_path.resolve()
        if resolved == root or root in resolved.parents:
            raise ValueError(f"{label} must not be under {root_path}")


def load_fixed_input(args: argparse.Namespace) -> dict[str, Any]:
    if not args.fixed_input_yaml:
        raise ValueError(
            "--fixed-input-yaml is required so review expected values are not "
            "derived from analysis_yaml"
        )
    fixed_path = Path(args.fixed_input_yaml)
    fixed = load_yaml(fixed_path)
    if "fixed_input" in fixed:
        fixed = fixed["fixed_input"]
        if not isinstance(fixed, dict):
            raise ValueError(f"{fixed_path}: fixed_input must be a mapping")
    scope = fixed.get("scope")
    if not isinstance(scope, dict):
        raise ValueError(f"{fixed_path}: missing mapping key: scope")
    for key in [
        "company_name",
        "survey_date",
        "slug",
        "applicant_graduation_cohort",
    ]:
        require_scalar(fixed, key, str(fixed_path))
    for key in [
        "user_label",
        "target_application_unit",
        "hiring_entity_name",
        "role_family",
        "workplace_entity_name",
        "ambiguity_note",
    ]:
        require_scalar(scope, key, f"{fixed_path}: scope")
    alternatives = scope.get("alternative_application_units")
    if not isinstance(alternatives, list) or not all(
        isinstance(item, str) for item in alternatives
    ):
        raise ValueError(
            f"{fixed_path}: scope.alternative_application_units must be a list of strings"
        )
    return fixed


def build_bundle(
    analysis_path: Path,
    rendered_path: Path | None,
    output_path: Path,
    review_path: Path,
    fixed: dict[str, Any],
    args: argparse.Namespace,
) -> str:
    scope = fixed["scope"]

    slug = require_scalar(fixed, "slug", "fixed input")
    company_name = require_scalar(fixed, "company_name", "fixed input")
    survey_date = require_scalar(fixed, "survey_date", "fixed input")
    applicant_graduation_cohort = require_scalar(
        fixed, "applicant_graduation_cohort", "fixed input"
    )

    lines = [
        "# Company Analysis Review Input",
        "",
        "このファイルは `company-analysis-review` 子に渡す review input bundle です。",
        "reviewer はこのファイルに列挙された review target path と reference path だけを読み、review YAML だけを返してください。",
        "",
        "## Fixed Input",
        "",
        f"- company_name: {company_name}",
        f"- survey_date: {survey_date}",
        f"- slug: {slug}",
        f"- run_id: {args.run_id}",
        f"- applicant_graduation_cohort: {applicant_graduation_cohort}",
        f"- intermediate_artifact_id: {args.artifact_id}",
        f"- scope.user_label: {scope.get('user_label')}",
        f"- scope.target_application_unit: {scope.get('target_application_unit')}",
        f"- scope.hiring_entity_name: {scope.get('hiring_entity_name')}",
        f"- scope.role_family: {scope.get('role_family')}",
        "- scope.alternative_application_units:",
        format_list(scope.get("alternative_application_units")),
        f"- scope.workplace_entity_name: {scope.get('workplace_entity_name')}",
        f"- scope.ambiguity_note: {scope.get('ambiguity_note')}",
        "",
        "## Target Context",
        "",
        f"- requested_target: {args.requested_target}",
        f"- scope_rationale: {args.scope_rationale}",
        f"- rejected_or_nearby_application_units: {args.rejected_or_nearby_application_units}",
        "",
        "## Handoff Observations",
        "",
        f"- expected_handoff_path: {args.expected_handoff_path}",
        f"- handoff_match: {args.handoff_match}",
        f"- unauthorized_outputs: {args.unauthorized_outputs}",
        f"- unexpected_rendering: {args.unexpected_rendering}",
        f"- child_run_metadata_present: {args.child_run_metadata_present}",
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
        f"- company_analysis_output_contract_path: {COMPANY_ANALYSIS_OUTPUT_CONTRACT_PATH}",
        f"- company_analysis_scope_check_path: {COMPANY_ANALYSIS_SCOPE_CHECK_PATH}",
        f"- company_analysis_scoring_path: {COMPANY_ANALYSIS_SCORING_PATH}",
        f"- company_analysis_review_skill_path: {COMPANY_ANALYSIS_REVIEW_SKILL_PATH}",
        "",
        "## Instructions",
        "",
        "- `.agents/skills/company-analysis-review/SKILL.md` の `company-analysis-review` skill を使う。",
        "- この review input bundle と `analysis_yaml_path` の YAML を現在の唯一の review 対象として扱う。",
        "- `analysis_yaml_path` は子オーケストラが孫調査 handoff 受理後に `run_metadata` を追加した validator-ready working YAML である。`run_metadata` の存在だけを孫調査エージェントの返却 YAML 違反として扱わない。",
        "- `Reference Paths` は指示準拠確認のためだけに読む。既存分析結果や比較レビューを追加で読まない。",
        "- `rendered_markdown_path` が `null` の場合、render consistency は確認対象外にする。",
        "- `Handoff Observations` に書かれた `expected_handoff_path` だけを孫調査エージェントの保存許可先として扱う。",
        "- `handoff_match` が `matched` 以外の場合は、handoff file と message YAML の不一致または fallback として確認する。",
        "- `unauthorized_outputs` が `none_observed` 以外の場合は、子オーケストラが孫調査エージェントの許可外ファイル作成・更新・保存を観測したものとして `instruction_compliance` finding を返す。",
        "- `unexpected_rendering` が `none_observed` 以外の場合は、孫調査エージェントが Markdown rendering を行ったものとして `instruction_compliance` finding を返す。",
        "- `child_run_metadata_present` が `true` の場合は、孫調査エージェントの返却 YAML に `run_metadata` が混入したものとして `instruction_compliance` finding を返す。",
        "- 以前の review payload、以前の slug、以前の finding、以前の rendered output は無視する。",
        "- `Fixed Input` の `slug` は schema 互換の機械的識別子であり、slug 文字列だけを理由に scope error としない。",
        "- `applicant_graduation_cohort` は応募者条件であり、採用年度や `fact_layer` の年度フィルタとして扱わない。",
        "- `fact_layer` の数値・制度 facts は、調査時点で最も新しく、固定 scope に最も近い確認済み fact を優先しているか確認する。",
        "- cohort 向け情報が未公開の場合、同一応募単位、同一採用主体、または共通制度として扱える直近年度の情報を探しているか確認する。",
        "- `fact_layer` に source year、適用 cohort、scope distance などの年度メタデータを追加していないか確認する。",
        "- 固定 scope が requested_target や scope_rationale と意味的に矛盾する場合は scope error として扱う。",
        "- `message` と `suggested_fix` は日本語で書く。",
        "- `company-analysis` skill の指示に反していないかを必ず確認する。",
        "- 特に、固定 scope の維持、近接職種への無断置換禁止、会社全体評価への拡張禁止、公式 / 非公式の分離、重要欠損時の追加調査、推定値による `fact_layer` 補完の禁止、指定 handoff path 以外でのファイル作成・保存・Markdown rendering 禁止を確認する。",
        "- `company-analysis` skill の指示違反に該当する場合は `category: instruction_compliance` を使う。内容上の不整合は最も具体的な category を使う。",
        "- 問題がなければ `passed_checks` に `instruction_compliance` と `scope_integrity` を含める。",
        "- `pass` の場合でも、`pass_rationale` に修正不要と判断した短い根拠を書き、`residual_risks` に scope ambiguity、source weakness、production 昇格可否に関わる留保を残す。留保がなければ `residual_risks: []` とする。",
        "- `revise` の場合は `pass_rationale: null` とし、修正要求ではない留保だけを `residual_risks` に残す。留保がなければ `residual_risks: []` とする。",
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
    parser.add_argument(
        "--run-id",
        dest="run_id",
        required=True,
        help="Run identifier for tmp paths",
    )
    parser.add_argument(
        "--fixed-input-yaml",
        required=True,
        help=(
            "YAML file containing the orchestrator-fixed company_name, survey_date, slug, "
            "applicant_graduation_cohort, and scope mapping"
        ),
    )
    parser.add_argument(
        "--expected-handoff-path",
        required=True,
        help="Parent-assigned path that the analysis child was allowed to write.",
    )
    parser.add_argument(
        "--handoff-match",
        required=True,
        choices=["matched", "message_fallback", "missing", "mismatch", "not_checked"],
        help="Whether handoff file YAML and message YAML matched for the current target.",
    )
    parser.add_argument(
        "--unauthorized-outputs",
        required=True,
        help="Use 'none_observed' when the child orchestrator found no grandchild output outside the expected handoff path; otherwise describe paths/actions.",
    )
    parser.add_argument(
        "--unexpected-rendering",
        required=True,
        help="Use 'none_observed' when the child orchestrator found no grandchild Markdown rendering; otherwise describe the rendered outputs.",
    )
    parser.add_argument(
        "--child-run-metadata-present",
        required=True,
        choices=["true", "false"],
        help="Whether the raw grandchild research YAML already contained run_metadata before child-orchestrator acceptance.",
    )
    parser.add_argument("--rendered", help="Optional rendered Markdown path")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Review input directory (default: tmp/company_analysis/runs/<run_id>/review_inputs)",
    )
    parser.add_argument(
        "--review-output-dir",
        default=None,
        help="Review output directory (default: tmp/company_analysis/runs/<run_id>/reviews)",
    )
    parser.add_argument("--requested-target", "--user-requested-target", dest="requested_target", required=True)
    parser.add_argument("--scope-rationale", "--parent-scope-rationale", dest="scope_rationale", required=True)
    parser.add_argument("--rejected-or-nearby-application-units", default="null")
    parser.add_argument(
        "--artifact-id",
        help="UUID filename stem for the review bundle and review output (default: random UUID)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.run_id = require_run_id(args.run_id)
    analysis_path = Path(args.analysis_yaml)
    rendered_path = Path(args.rendered) if args.rendered else None
    load_yaml(analysis_path)
    fixed = load_fixed_input(args)
    args.artifact_id = args.artifact_id or str(uuid.uuid4())
    try:
        uuid.UUID(args.artifact_id)
    except ValueError as exc:
        raise ValueError("--artifact-id must be a valid UUID") from exc

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else DEFAULT_RUN_ROOT / args.run_id / "review_inputs"
    )
    review_output_dir = (
        Path(args.review_output_dir)
        if args.review_output_dir
        else DEFAULT_RUN_ROOT / args.run_id / "reviews"
    )
    output_path = output_dir / f"{args.artifact_id}.md"
    review_path = review_output_dir / f"{args.artifact_id}.yaml"
    try:
        reject_report_company_analysis_path(output_path, "--output-dir")
        reject_report_company_analysis_path(review_path, "--review-output-dir")
    except ValueError as exc:
        raise SystemExit(str(exc))
    text = build_bundle(analysis_path, rendered_path, output_path, review_path, fixed, args)
    output_path.write_text(text, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
