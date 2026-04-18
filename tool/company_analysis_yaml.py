#!/usr/bin/env python3
"""
Helpers for company-analysis YAML validation and Markdown rendering.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


SECTION_ORDER = [
    ("phd_value", "## 1. 博士人材の評価", "博士人材の評価"),
    ("role_fit", "## 2. 仕事内容・配属確度", "仕事内容・配属確度"),
    ("rd_env", "## 3. 研究開発・技術環境", "研究開発・技術環境"),
    ("compensation", "## 4. 処遇・働き方", "処遇・働き方"),
    ("hiring_process", "## 5. 選考コストと評価の納得感", "選考コストと評価の納得感"),
    ("stability", "## 6. 企業基盤・安定性", "企業基盤・安定性"),
]

WEIGHTS = {
    "phd_value": 0.30,
    "role_fit": 0.10,
    "rd_env": 0.05,
    "compensation": 0.25,
    "hiring_process": 0.10,
    "stability": 0.20,
}


@dataclass
class ValidationResult:
    issues: list[str]
    data: dict[str, Any] | None


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def is_tenth_step(value: float) -> bool:
    return abs(round(value * 10) - value * 10) < 1e-9


def compute_base_total(data: dict[str, Any]) -> float:
    total = 20 * sum(
        WEIGHTS[key] * float(data["sections"][key]["score"]) for key, *_ in SECTION_ORDER
    )
    return round(total, 1)


def compute_final_total(data: dict[str, Any]) -> float:
    base = compute_base_total(data)
    adjustment = float(data["adjustment"]["value"])
    return round(base + adjustment, 1)


def clean_text(value: str) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    text = re.sub(r"([、。]) ", r"\1", text)
    return text


def format_yen(value: int | None) -> str:
    if value is None:
        return "未公表"
    return f"{value:,}円"


def format_overtime_hours(value: float | int | None) -> str:
    if value is None:
        return "未公表"
    return f"{float(value):.1f}時間"


def format_days(value: int | None) -> str:
    if value is None:
        return "未公表"
    return f"{value}日"


def format_remote_policy(value: str) -> str:
    labels = {
        "full": "フルリモート可",
        "hybrid": "ハイブリッド",
        "limited": "一部利用可",
        "none": "原則出社",
        "unknown": "未公表",
    }
    return labels.get(value, value)


def format_bool_ja(value: bool) -> str:
    return "はい" if value else "いいえ"


def _ensure_dict(value: Any, label: str, issues: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        issues.append(f"{label} must be a mapping")
        return {}
    return value


def _ensure_list(value: Any, label: str, issues: list[str]) -> list[Any]:
    if not isinstance(value, list):
        issues.append(f"{label} must be a list")
        return []
    return value


def validate_data(data: Any, source_name: str = "<memory>") -> ValidationResult:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ValidationResult(["top-level YAML must be a mapping"], None)

    req_top = [
        "version",
        "company_name",
        "survey_date",
        "slug",
        "scope",
        "sections",
        "adjustment",
        "summary",
        "sources",
    ]
    for key in req_top:
        if key not in data:
            issues.append(f"missing top-level key: {key}")

    if issues:
        return ValidationResult(issues, data)

    if data["version"] != 1:
        issues.append("version must be 1")

    if not isinstance(data["company_name"], str) or not data["company_name"].strip():
        issues.append("company_name must be a non-empty string")

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(data["survey_date"])):
        issues.append("survey_date must match YYYY-MM-DD")

    if not re.fullmatch(r"[a-z0-9_]+", str(data["slug"])):
        issues.append("slug must match [a-z0-9_]+")

    source_path = Path(source_name)
    if source_path.stem and source_path.suffix in {".yaml", ".yml"}:
        base_parts = source_path.with_suffix("").parts
        candidates = {source_path.stem}
        for i in range(len(base_parts)):
            candidates.add("_".join(base_parts[i:]))
        if data["slug"] not in candidates:
            issues.append(
                f"slug {data['slug']} does not match filename/path candidates {sorted(candidates)}"
            )

    if "run_metadata" in data:
        run_meta = _ensure_dict(data["run_metadata"], "run_metadata", issues)
        for key in ["executor", "model", "reasoning_effort", "fixed_by_parent"]:
            if key not in run_meta:
                issues.append(f"run_metadata missing key: {key}")
        for key in ["executor", "model", "reasoning_effort"]:
            if key in run_meta and (not isinstance(run_meta[key], str) or not run_meta[key].strip()):
                issues.append(f"run_metadata.{key} must be a non-empty string")
        if "fixed_by_parent" in run_meta and not isinstance(run_meta["fixed_by_parent"], bool):
            issues.append("run_metadata.fixed_by_parent must be a boolean")

    scope = _ensure_dict(data["scope"], "scope", issues)
    for key in [
        "user_label",
        "evaluation_target",
        "hiring_entity",
        "job_type",
        "placement_candidates",
        "stability_entity",
        "ambiguity_note",
    ]:
        if key not in scope:
            issues.append(f"scope missing key: {key}")

    if scope:
        for key in ["user_label", "evaluation_target", "hiring_entity", "job_type", "stability_entity", "ambiguity_note"]:
            if key in scope and (not isinstance(scope[key], str) or not scope[key].strip()):
                issues.append(f"scope.{key} must be a non-empty string")
        placements = _ensure_list(scope.get("placement_candidates", []), "scope.placement_candidates", issues)
        if placements and not all(isinstance(x, str) and x.strip() for x in placements):
            issues.append("scope.placement_candidates entries must be non-empty strings")

    sections = _ensure_dict(data["sections"], "sections", issues)
    for key, *_ in SECTION_ORDER:
        if key not in sections:
            issues.append(f"sections missing key: {key}")
    for key, *_ in SECTION_ORDER:
        section = _ensure_dict(sections.get(key, {}), f"sections.{key}", issues)
        for subkey in ["score", "facts", "evaluation"]:
            if subkey not in section:
                issues.append(f"sections.{key} missing key: {subkey}")
        if "score" in section:
            try:
                score = float(section["score"])
            except Exception:
                issues.append(f"sections.{key}.score must be numeric")
            else:
                if not 1.0 <= score <= 5.0:
                    issues.append(f"sections.{key}.score must be between 1.0 and 5.0")
                if not is_tenth_step(score):
                    issues.append(f"sections.{key}.score must use 0.1 increments")
        for subkey in ["facts", "evaluation"]:
            if subkey in section and (not isinstance(section[subkey], str) or not section[subkey].strip()):
                issues.append(f"sections.{key}.{subkey} must be a non-empty string")
        if key == "compensation":
            structured = _ensure_dict(
                section.get("structured", {}), "sections.compensation.structured", issues
            )
            int_keys = [
                "starting_salary_yen",
                "average_annual_income_yen",
                "annual_holidays_days",
            ]
            for subkey in int_keys:
                if subkey not in structured:
                    issues.append(f"sections.compensation.structured missing key: {subkey}")
                    continue
                value = structured[subkey]
                if value is None:
                    continue
                if not isinstance(value, int):
                    issues.append(
                        f"sections.compensation.structured.{subkey} must be an integer or null"
                    )
                    continue
                if value < 0:
                    issues.append(
                        f"sections.compensation.structured.{subkey} must be non-negative"
                    )
            optional_int_keys = [
                "starting_salary_bachelor_yen",
                "starting_salary_master_yen",
                "starting_salary_doctor_yen",
            ]
            for subkey in optional_int_keys:
                if subkey not in structured:
                    continue
                value = structured[subkey]
                if value is None:
                    continue
                if not isinstance(value, int):
                    issues.append(
                        f"sections.compensation.structured.{subkey} must be an integer or null"
                    )
                    continue
                if value < 0:
                    issues.append(
                        f"sections.compensation.structured.{subkey} must be non-negative"
                    )
            overtime_key = "average_overtime_hours_per_month"
            if overtime_key not in structured:
                issues.append(f"sections.compensation.structured missing key: {overtime_key}")
            else:
                overtime = structured[overtime_key]
                if overtime is not None:
                    if not isinstance(overtime, (int, float)):
                        issues.append(
                            "sections.compensation.structured.average_overtime_hours_per_month "
                            "must be numeric or null"
                        )
                    elif overtime < 0:
                        issues.append(
                            "sections.compensation.structured.average_overtime_hours_per_month "
                            "must be non-negative"
                        )
            policy_key = "remote_work_policy"
            allowed_policies = {"full", "hybrid", "limited", "none", "unknown"}
            if policy_key not in structured:
                issues.append(f"sections.compensation.structured missing key: {policy_key}")
            else:
                policy = structured[policy_key]
                if not isinstance(policy, str) or policy not in allowed_policies:
                    issues.append(
                        "sections.compensation.structured.remote_work_policy must be one of "
                        f"{sorted(allowed_policies)}"
                    )

    adjustment = _ensure_dict(data["adjustment"], "adjustment", issues)
    for key in ["value", "reason"]:
        if key not in adjustment:
            issues.append(f"adjustment missing key: {key}")
    if "value" in adjustment:
        try:
            adj = float(adjustment["value"])
        except Exception:
            issues.append("adjustment.value must be numeric")
        else:
            if not -5.0 <= adj <= 5.0:
                issues.append("adjustment.value must be between -5.0 and 5.0")
            if not is_tenth_step(adj):
                issues.append("adjustment.value must use 0.1 increments")
    if "reason" in adjustment and not isinstance(adjustment["reason"], str):
        issues.append("adjustment.reason must be a string")

    summary = _ensure_dict(data["summary"], "summary", issues)
    for key in ["conclusion", "final_comment", "suitable_for", "not_suitable_for", "concerns"]:
        if key not in summary:
            issues.append(f"summary missing key: {key}")
    if summary:
        for key in ["conclusion", "final_comment"]:
            if key in summary and (not isinstance(summary[key], str) or not summary[key].strip()):
                issues.append(f"summary.{key} must be a non-empty string")
        for key in ["suitable_for", "not_suitable_for", "concerns"]:
            items = _ensure_list(summary.get(key, []), f"summary.{key}", issues)
            if items and not all(isinstance(x, str) and x.strip() for x in items):
                issues.append(f"summary.{key} entries must be non-empty strings")

    sources = _ensure_list(data["sources"], "sources", issues)
    if not sources:
        issues.append("sources must contain at least one entry")
    for i, src in enumerate(sources):
        label = f"sources[{i}]"
        src_map = _ensure_dict(src, label, issues)
        for key in ["label", "url"]:
            if key not in src_map:
                issues.append(f"{label} missing key: {key}")
        if "label" in src_map and (not isinstance(src_map["label"], str) or not src_map["label"].strip()):
            issues.append(f"{label}.label must be a non-empty string")
        if "url" in src_map:
            if not isinstance(src_map["url"], str) or not re.fullmatch(r"https?://\S+", src_map["url"]):
                issues.append(f"{label}.url must be a valid http(s) URL")

    return ValidationResult(issues, data)


def render_markdown(data: dict[str, Any]) -> str:
    scope = data["scope"]
    sections = data["sections"]
    summary = data["summary"]
    base_total = compute_base_total(data)
    final_total = compute_final_total(data)

    placement = "、".join(scope["placement_candidates"])
    lines: list[str] = [
        f"# {data['company_name']}",
        f"調査日: {data['survey_date']}",
        "",
    ]

    run_meta = data.get("run_metadata")
    if isinstance(run_meta, dict):
        lines.extend(
            [
                "## 実行メタデータ",
                f"- 実行主体: {clean_text(run_meta['executor'])}",
                f"- モデル: {clean_text(run_meta['model'])}",
                f"- 推論労力: {clean_text(run_meta['reasoning_effort'])}",
                f"- 親による固定: {format_bool_ja(bool(run_meta['fixed_by_parent']))}",
                "",
            ]
        )

    lines.extend(
        [
        "## 結論",
        clean_text(summary["conclusion"]),
        "",
        "## 分析対象の確定",
        f"- ユーザー指定名: {scope['user_label']}",
        f"- 分析対象単位: {scope['evaluation_target']}",
        f"- 採用主体: {scope['hiring_entity']}",
        f"- 採用職種: {scope['job_type']}",
        f"- 主な配属候補: {placement}",
        f"- 企業基盤に使う法人単位: {scope['stability_entity']}",
        f"- 曖昧性の処理: {clean_text(scope['ambiguity_note'])}",
        "",
        ]
    )

    for key, heading, label in SECTION_ORDER:
        section = sections[key]
        lines.extend([heading, f"- 事実: {clean_text(section['facts'])}"])
        if key == "compensation":
            structured = section["structured"]
            degree_salary_parts = []
            degree_labels = [
                ("starting_salary_bachelor_yen", "学士"),
                ("starting_salary_master_yen", "修士"),
                ("starting_salary_doctor_yen", "博士"),
            ]
            for subkey, label in degree_labels:
                if subkey in structured:
                    degree_salary_parts.append(f"{label} {format_yen(structured[subkey])}")
            structured_parts = [f"初任給 {format_yen(structured['starting_salary_yen'])}"]
            if degree_salary_parts:
                structured_parts.append("学位別初任給 " + " / ".join(degree_salary_parts))
            structured_parts.extend(
                [
                    f"平均年収 {format_yen(structured['average_annual_income_yen'])}",
                    f"月平均残業 {format_overtime_hours(structured['average_overtime_hours_per_month'])}",
                    f"年間休日 {format_days(structured['annual_holidays_days'])}",
                    f"リモート方針 {format_remote_policy(structured['remote_work_policy'])}",
                ]
            )
            lines.append("- 構造化項目: " + ", ".join(structured_parts))
        lines.extend(
            [
                f"- 評価: {clean_text(section['evaluation'])}",
                f"- スコア: {float(section['score']):.1f} / 5.0",
                "",
            ]
        )

    formula_terms = " + ".join(
        f"{WEIGHTS[key]:.2f}×{float(sections[key]['score']):.1f}" for key, *_ in SECTION_ORDER
    )
    lines.extend(
        [
            "## 数式評価",
            *[
                f"- {label}: `{float(sections[key]['score']):.1f} / 5.0`"
                for key, _, label in SECTION_ORDER
            ],
            f"- `総合評価 = 20 × ({formula_terms})`",
            f"- `総合評価 = {base_total:.1f}`",
            "",
            "## 補正",
        ]
    )

    adjustment = float(data["adjustment"]["value"])
    reason = data["adjustment"]["reason"].strip()
    if adjustment == 0:
        lines.append("- なし")
    else:
        lines.append(f"- {adjustment:+.1f}")
        lines.append(f"- 理由: {reason}")
    lines.extend(
        [
            "",
            "## 最終評価",
            f"- {final_total:.1f} / 100",
            f"- {clean_text(summary['final_comment'])}",
            "",
            "## 向いている人",
            *[f"- {item}" for item in summary["suitable_for"]],
            "",
            "## 向いていない人",
            *[f"- {item}" for item in summary["not_suitable_for"]],
            "",
            "## 懸念点",
            *[f"- {item}" for item in summary["concerns"]],
            "",
            "## 参考文献",
            *[f"- {src['label']}: {src['url']}" for src in data["sources"]],
            "",
        ]
    )
    return "\n".join(lines)
