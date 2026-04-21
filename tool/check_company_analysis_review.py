#!/usr/bin/env python3
"""
Validate company-analysis review YAML files.

Usage:
  python3 tool/check_company_analysis_review.py path/to/review.yaml [path/to/review2.yaml ...]

What it does:
  - Checks that review YAML files follow the fixed review schema.
  - Validates verdict, finding enums, and required fields.

What it does not do:
  - It does not validate the underlying analysis YAML.
  - It does not rewrite or normalize any file.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


ALLOWED_VERDICTS = {"pass", "revise"}
ALLOWED_SEVERITIES = {"high", "medium", "low"}
ALLOWED_CATEGORIES = {
    "scope_integrity",
    "source_separation",
    "source_quality",
    "structured_data",
    "section_boundary",
    "score_consistency",
    "summary_consistency",
    "render_consistency",
    "residual_uncertainty",
}
ALLOWED_SECTIONS = {
    "scope",
    "fact_layer",
    "phd_value",
    "role_fit",
    "rd_env",
    "compensation",
    "hiring_process",
    "stability",
    "summary",
    "sources",
    "rendered_output",
}
ALLOWED_REVIEW_KEYS = {"verdict", "findings", "passed_checks"}
ALLOWED_FINDING_KEYS = {"severity", "category", "section", "message", "suggested_fix"}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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


def validate_review_data(data: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["top-level YAML must be a mapping"]

    if "review" not in data:
        return ["missing top-level key: review"]

    review = _ensure_dict(data["review"], "review", issues)
    for key in ["verdict", "findings", "passed_checks"]:
        if key not in review:
            issues.append(f"review missing key: {key}")
    extra_review_keys = sorted(set(review) - ALLOWED_REVIEW_KEYS)
    for key in extra_review_keys:
        issues.append(f"review has unknown key: {key}")

    verdict = review.get("verdict")
    if verdict not in ALLOWED_VERDICTS:
        issues.append(f"review.verdict must be one of {sorted(ALLOWED_VERDICTS)}")

    findings = _ensure_list(review.get("findings", []), "review.findings", issues)
    for i, finding in enumerate(findings):
        label = f"review.findings[{i}]"
        finding_map = _ensure_dict(finding, label, issues)
        for key in ["severity", "category", "section", "message", "suggested_fix"]:
            if key not in finding_map:
                issues.append(f"{label} missing key: {key}")
        extra_finding_keys = sorted(set(finding_map) - ALLOWED_FINDING_KEYS)
        for key in extra_finding_keys:
            issues.append(f"{label} has unknown key: {key}")
        if finding_map.get("severity") not in ALLOWED_SEVERITIES:
            issues.append(f"{label}.severity must be one of {sorted(ALLOWED_SEVERITIES)}")
        if finding_map.get("category") not in ALLOWED_CATEGORIES:
            issues.append(f"{label}.category must be one of {sorted(ALLOWED_CATEGORIES)}")
        if finding_map.get("section") not in ALLOWED_SECTIONS:
            issues.append(f"{label}.section must be one of {sorted(ALLOWED_SECTIONS)}")
        for key in ["message", "suggested_fix"]:
            value = finding_map.get(key)
            if not isinstance(value, str) or not value.strip():
                issues.append(f"{label}.{key} must be a non-empty string")

    passed_checks = _ensure_list(review.get("passed_checks", []), "review.passed_checks", issues)
    if passed_checks and not all(isinstance(x, str) and x.strip() for x in passed_checks):
        issues.append("review.passed_checks entries must be non-empty strings")

    if verdict == "pass" and findings:
        issues.append("review.verdict=pass requires review.findings to be empty")
    if verdict == "pass" and not passed_checks:
        issues.append("review.verdict=pass requires at least one review.passed_checks entry")
    if verdict == "revise" and not findings:
        issues.append("review.verdict=revise requires at least one review.finding")

    return issues


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print((__doc__ or "").strip())
        return 2

    bad = 0
    for raw in argv[1:]:
        path = Path(raw)
        if not path.exists():
            print(f"{path}: not found")
            bad = 1
            continue
        try:
            data = load_yaml(path)
        except Exception as exc:
            print(f"{path}: failed to parse YAML: {exc}")
            bad = 1
            continue
        issues = validate_review_data(data)
        if issues:
            bad = 1
            print(f"{path}:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"{path}: OK")
    return bad


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
