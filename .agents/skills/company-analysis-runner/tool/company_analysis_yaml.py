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

OFFICIAL_SOURCE_KINDS = {
    "recruit",
    "faq",
    "benefits",
    "company",
    "ir",
    "research",
    "business",
    "other",
}

UNOFFICIAL_SOURCE_KINDS = {
    "review_site",
    "forum",
    "career_site",
    "blog",
    "other",
}

ROLE_FAMILIES = {
    "researcher",
    "research_engineer",
    "engineer",
    "consultant",
    "generalist",
    "other",
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
    return compute_total(data)


def section_score(section: dict[str, Any]) -> float:
    return float(section["score"])


def compute_total(data: dict[str, Any]) -> float:
    total = 20 * sum(
        WEIGHTS[key] * section_score(data["sections"][key])
        for key, *_ in SECTION_ORDER
    )
    return round(total, 1)


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


def format_application_route(value: str | None) -> str:
    labels = {
        "direct": "この評価対象へ直接応募",
        "parent_company": "親会社ルート経由でこの評価対象へ到達",
        "group_company": "グループ会社ルート経由でこの評価対象へ到達",
        "unknown": "未公表",
    }
    if value is None:
        return "未公表"
    return labels.get(value, value)


def format_bool_ja(value: bool) -> str:
    return "はい" if value else "いいえ"


def format_optional_bool_ja(value: bool | None) -> str:
    if value is None:
        return "未公表"
    return "あり" if value else "なし"


def get_fact_layer_official(data: dict[str, Any]) -> dict[str, Any]:
    fact_layer = data.get("fact_layer", {})
    return fact_layer["official"]


def get_fact_layer_unofficial(data: dict[str, Any]) -> dict[str, Any] | None:
    fact_layer = data.get("fact_layer", {})
    unofficial = fact_layer.get("unofficial")
    return unofficial if isinstance(unofficial, dict) else None


def has_meaningful_unofficial_fact_layer(structured: dict[str, Any] | None) -> bool:
    if not structured:
        return False
    for value in structured.values():
        if value is None:
            continue
        if isinstance(value, str) and value == "unknown":
            continue
        return True
    return False


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


def _validate_comp_structured(
    structured: dict[str, Any], label: str, issues: list[str], require_all_keys: bool
) -> None:
    int_keys = [
        "starting_salary_yen",
        "average_annual_income_yen",
        "annual_holidays_days",
    ]
    for subkey in int_keys:
        if subkey not in structured:
            if require_all_keys:
                issues.append(f"{label} missing key: {subkey}")
            continue
        value = structured[subkey]
        if value is None:
            continue
        if not isinstance(value, int):
            issues.append(f"{label}.{subkey} must be an integer or null")
            continue
        if value < 0:
            issues.append(f"{label}.{subkey} must be non-negative")

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
            issues.append(f"{label}.{subkey} must be an integer or null")
            continue
        if value < 0:
            issues.append(f"{label}.{subkey} must be non-negative")

    optional_bool_keys = [
        "has_degree_based_starting_salary_gap",
        "has_doctoral_hiring_track",
        "has_doctoral_grade_advantage",
        "has_target_job_hiring_track",
    ]
    for subkey in optional_bool_keys:
        if subkey not in structured:
            if require_all_keys:
                issues.append(f"{label} missing key: {subkey}")
            continue
        value = structured[subkey]
        if value is not None and not isinstance(value, bool):
            issues.append(f"{label}.{subkey} must be a boolean or null")

    overtime_key = "average_overtime_hours_per_month"
    if overtime_key not in structured:
        if require_all_keys:
            issues.append(f"{label} missing key: {overtime_key}")
    else:
        overtime = structured[overtime_key]
        if overtime is not None:
            if not isinstance(overtime, (int, float)):
                issues.append(f"{label}.average_overtime_hours_per_month must be numeric or null")
            elif overtime < 0:
                issues.append(f"{label}.average_overtime_hours_per_month must be non-negative")

    policy_key = "remote_work_policy"
    allowed_policies = {"full", "hybrid", "limited", "none", "unknown"}
    if policy_key not in structured:
        if require_all_keys:
            issues.append(f"{label} missing key: {policy_key}")
    else:
        policy = structured[policy_key]
        if not isinstance(policy, str) or policy not in allowed_policies:
            issues.append(
                f"{label}.remote_work_policy must be one of {sorted(allowed_policies)}"
            )

    route_key = "application_route"
    allowed_routes = {"direct", "parent_company", "group_company", "unknown"}
    if route_key not in structured:
        if require_all_keys:
            issues.append(f"{label} missing key: {route_key}")
    else:
        route = structured[route_key]
        if route is not None and (
            not isinstance(route, str) or route not in allowed_routes
        ):
            issues.append(
                f"{label}.application_route must be one of {sorted(allowed_routes)} or null"
            )


def validate_data(data: Any, source_name: str = "<memory>") -> ValidationResult:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ValidationResult(["top-level YAML must be a mapping"], None)

    req_top = [
        "version",
        "company_name",
        "survey_date",
        "slug",
        "run_metadata",
        "scope",
        "fact_layer",
        "sections",
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
        "target_application_unit",
        "hiring_entity_name",
        "role_family",
        "alternative_application_units",
        "stability_entity_name",
        "ambiguity_note",
    ]:
        if key not in scope:
            issues.append(f"scope missing key: {key}")

    if scope:
        for key in [
            "user_label",
            "target_application_unit",
            "hiring_entity_name",
            "stability_entity_name",
            "ambiguity_note",
        ]:
            if key in scope and (not isinstance(scope[key], str) or not scope[key].strip()):
                issues.append(f"scope.{key} must be a non-empty string")
        role_family = scope.get("role_family")
        if role_family not in ROLE_FAMILIES:
            issues.append(f"scope.role_family must be one of {sorted(ROLE_FAMILIES)}")
        alternatives = _ensure_list(
            scope.get("alternative_application_units", []),
            "scope.alternative_application_units",
            issues,
        )
        if alternatives and not all(isinstance(x, str) and x.strip() for x in alternatives):
            issues.append("scope.alternative_application_units entries must be non-empty strings")

    fact_layer = _ensure_dict(data["fact_layer"], "fact_layer", issues)
    if "official" not in fact_layer:
        issues.append("fact_layer missing key: official")
    official_fact = _ensure_dict(
        fact_layer.get("official", {}),
        "fact_layer.official",
        issues,
    )
    _validate_comp_structured(
        official_fact,
        "fact_layer.official",
        issues,
        require_all_keys=True,
    )
    if "unofficial" not in fact_layer:
        issues.append("fact_layer missing key: unofficial")
    unofficial_fact = _ensure_dict(
        fact_layer.get("unofficial", {}),
        "fact_layer.unofficial",
        issues,
    )
    _validate_comp_structured(
        unofficial_fact,
        "fact_layer.unofficial",
        issues,
        require_all_keys=True,
    )

    sections = _ensure_dict(data["sections"], "sections", issues)
    for key, *_ in SECTION_ORDER:
        if key not in sections:
            issues.append(f"sections missing key: {key}")
    for key, *_ in SECTION_ORDER:
        section = _ensure_dict(sections.get(key, {}), f"sections.{key}", issues)
        if "score" not in section:
            issues.append(f"sections.{key} missing key: score")
        elif any(legacy in section for legacy in ["score_final", "score_official"]):
            issues.append(
                f"sections.{key} must not include legacy score_final/score_official"
            )
        else:
            try:
                score = float(section["score"])
            except Exception:
                issues.append(f"sections.{key}.score must be numeric")
            else:
                if not 1.0 <= score <= 5.0:
                    issues.append(f"sections.{key}.score must be between 1.0 and 5.0")
                if not is_tenth_step(score):
                    issues.append(f"sections.{key}.score must use 0.1 increments")

        if "facts_official" not in section:
            issues.append(f"sections.{key} missing key: facts_official")
        elif not isinstance(section["facts_official"], str) or not section["facts_official"].strip():
            issues.append(f"sections.{key}.facts_official must be a non-empty string")
        if "facts_unofficial" not in section:
            issues.append(f"sections.{key} missing key: facts_unofficial")
        elif not isinstance(section["facts_unofficial"], str):
            issues.append(f"sections.{key}.facts_unofficial must be a string")

        if "evaluation" not in section:
            issues.append(f"sections.{key} missing key: evaluation")
        elif not isinstance(section["evaluation"], str) or not section["evaluation"].strip():
            issues.append(f"sections.{key}.evaluation must be a non-empty string")
        if any(field in section for field in ["structured_official", "structured_unofficial"]):
            issues.append(
                f"sections.{key}.structured_* is no longer allowed; use top-level fact_layer"
            )

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
    official_kinds_seen: set[str] = set()
    official_count = 0
    for i, src in enumerate(sources):
        label = f"sources[{i}]"
        src_map = _ensure_dict(src, label, issues)
        for key in ["label", "url", "tier", "kind"]:
            if key not in src_map:
                issues.append(f"{label} missing key: {key}")
        if "label" in src_map and (not isinstance(src_map["label"], str) or not src_map["label"].strip()):
            issues.append(f"{label}.label must be a non-empty string")
        if "url" in src_map:
            if not isinstance(src_map["url"], str) or not re.fullmatch(r"https?://\S+", src_map["url"]):
                issues.append(f"{label}.url must be a valid http(s) URL")
        tier = src_map.get("tier")
        if tier not in {"official", "unofficial"}:
            issues.append(f"{label}.tier must be one of ['official', 'unofficial']")
            continue
        kind = src_map.get("kind")
        allowed_kinds = OFFICIAL_SOURCE_KINDS if tier == "official" else UNOFFICIAL_SOURCE_KINDS
        if kind not in allowed_kinds:
            issues.append(f"{label}.kind must be one of {sorted(allowed_kinds)} for tier={tier}")
            continue
        if tier == "official":
            official_count += 1
            official_kinds_seen.add(kind)

    if official_count < 4:
        issues.append("sources must contain at least four official entries")
    required_official_kind_groups = [
        {"recruit"},
        {"company", "ir"},
    ]
    for group in required_official_kind_groups:
        if not official_kinds_seen.intersection(group):
            issues.append(
                f"sources missing required official source kind from {sorted(group)}"
            )

    return ValidationResult(issues, data)


def render_markdown(data: dict[str, Any]) -> str:
    scope = data["scope"]
    sections = data["sections"]
    summary = data["summary"]
    fact_official = get_fact_layer_official(data)
    fact_unofficial = get_fact_layer_unofficial(data)
    base_total = compute_total(data)

    alternative_units = (
        "、".join(scope["alternative_application_units"])
        if scope["alternative_application_units"]
        else "なし"
    )
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
        f"## 結論（{scope['target_application_unit']}）",
        clean_text(summary["conclusion"]),
        "",
        "## 分析対象の確定",
        f"- ユーザー指定名: {scope['user_label']}",
        f"- 応募対象単位: {scope['target_application_unit']}",
        f"- 採用 entity: {scope['hiring_entity_name']}",
        f"- 職種ファミリー: {scope['role_family']}",
        f"- 他の応募単位候補: {alternative_units}",
        f"- 企業基盤に使う entity: {scope['stability_entity_name']}",
        f"- 曖昧性の処理: {clean_text(scope['ambiguity_note'])}",
        "",
        ]
    )

    degree_labels = [
        ("starting_salary_bachelor_yen", "学士"),
        ("starting_salary_master_yen", "修士"),
        ("starting_salary_doctor_yen", "博士"),
    ]
    official_degree_parts = []
    for subkey, label in degree_labels:
        if subkey in fact_official:
            official_degree_parts.append(f"{label} {format_yen(fact_official[subkey])}")
    official_parts = [
        f"月額初任給 {format_yen(fact_official['starting_salary_yen'])}",
    ]
    if official_degree_parts:
        official_parts.append("学位別月額初任給 " + " / ".join(official_degree_parts))
    official_parts.extend(
        [
            f"学位別初任給差 {format_optional_bool_ja(fact_official.get('has_degree_based_starting_salary_gap'))}",
            f"博士向け採用導線 {format_optional_bool_ja(fact_official.get('has_doctoral_hiring_track'))}",
            f"博士向け格付け差 {format_optional_bool_ja(fact_official.get('has_doctoral_grade_advantage'))}",
            f"対象応募単位の採用導線 {format_optional_bool_ja(fact_official.get('has_target_job_hiring_track'))}",
            f"応募経路 {format_application_route(fact_official.get('application_route'))}",
            f"平均年収 {format_yen(fact_official['average_annual_income_yen'])}",
            f"月平均残業 {format_overtime_hours(fact_official['average_overtime_hours_per_month'])}",
            f"年間休日 {format_days(fact_official['annual_holidays_days'])}",
            f"リモート方針 {format_remote_policy(fact_official['remote_work_policy'])}",
        ]
    )
    lines.append("## 主要数値・制度事実")
    lines.append("- 公式: " + ", ".join(official_parts))
    if has_meaningful_unofficial_fact_layer(fact_unofficial):
        unofficial_degree_parts = []
        for subkey, label in degree_labels:
            if subkey in fact_unofficial:
                unofficial_degree_parts.append(f"{label} {format_yen(fact_unofficial[subkey])}")
        unofficial_parts = []
        if "starting_salary_yen" in fact_unofficial:
            unofficial_parts.append(f"月額初任給 {format_yen(fact_unofficial['starting_salary_yen'])}")
        if unofficial_degree_parts:
            unofficial_parts.append("学位別月額初任給 " + " / ".join(unofficial_degree_parts))
        bool_labels = [
            ("has_degree_based_starting_salary_gap", "学位別初任給差"),
            ("has_doctoral_hiring_track", "博士向け採用導線"),
            ("has_doctoral_grade_advantage", "博士向け格付け差"),
            ("has_target_job_hiring_track", "対象応募単位の採用導線"),
        ]
        for subkey, label in bool_labels:
            if subkey in fact_unofficial:
                unofficial_parts.append(
                    f"{label} {format_optional_bool_ja(fact_unofficial.get(subkey))}"
                )
        if "application_route" in fact_unofficial:
            unofficial_parts.append(
                f"応募経路 {format_application_route(fact_unofficial.get('application_route'))}"
            )
        if "average_annual_income_yen" in fact_unofficial:
            unofficial_parts.append(
                f"平均年収 {format_yen(fact_unofficial['average_annual_income_yen'])}"
            )
        if "average_overtime_hours_per_month" in fact_unofficial:
            unofficial_parts.append(
                f"月平均残業 {format_overtime_hours(fact_unofficial['average_overtime_hours_per_month'])}"
            )
        if "annual_holidays_days" in fact_unofficial:
            unofficial_parts.append(
                f"年間休日 {format_days(fact_unofficial['annual_holidays_days'])}"
            )
        if "remote_work_policy" in fact_unofficial:
            unofficial_parts.append(
                f"リモート方針 {format_remote_policy(fact_unofficial['remote_work_policy'])}"
            )
        if unofficial_parts:
            lines.append("- 非公式参考: " + ", ".join(unofficial_parts))
    lines.append("")

    for key, heading, label in SECTION_ORDER:
        section = sections[key]
        lines.append(heading)
        lines.append(f"- 公式情報: {clean_text(section['facts_official'])}")
        unofficial = section.get("facts_unofficial", "")
        if str(unofficial).strip():
            lines.append(f"- 非公式情報: {clean_text(unofficial)}")
        lines.extend(
            [
                f"- 評価: {clean_text(section['evaluation'])}",
                f"- スコア: {section_score(section):.1f} / 5.0",
                "",
            ]
        )

    final_formula_terms = " + ".join(
        f"{WEIGHTS[key]:.2f}×{section_score(sections[key]):.1f}"
        for key, *_ in SECTION_ORDER
    )
    lines.extend(
        [
            "## 数式評価",
            *[
                f"- {label}: `{section_score(sections[key]):.1f} / 5.0`"
                for key, _, label in SECTION_ORDER
            ],
            f"- `総合評価（補正前） = 20 × ({final_formula_terms})`",
            f"- `総合評価（補正前） = {base_total:.1f}`",
            "",
            "## 最終評価",
            f"- 総合評価: {base_total:.1f} / 100",
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
            *[
                (
                    f"- [{ '公式' if src.get('tier') == 'official' else '非公式' }] {src['label']}: {src['url']}"
                    if src.get("tier") in {"official", "unofficial"}
                    else f"- {src['label']}: {src['url']}"
                )
                for src in data["sources"]
            ],
            "",
        ]
    )
    return "\n".join(lines)
