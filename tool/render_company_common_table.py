#!/usr/bin/env python3
"""
Render a common-data table from company-analysis YAML files.

Usage:
    python3 tool/render_company_common_table.py \
        report/company_analysis/data/*.yaml \
        --output report/company_analysis/reviews/common_data_20260416.md

    python3 tool/render_company_common_table.py \
        report/company_analysis/data/*.yaml \
        --output report/company_analysis/reviews/common_data_20260416.csv

Input:
    - One or more company-analysis YAML files.

Output:
    - A Markdown or CSV file containing a common-data table.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from company_analysis_yaml import (
    SECTION_ORDER,
    compute_total,
    format_days,
    format_overtime_hours,
    format_remote_policy,
    format_yen,
    get_fact_layer_official,
    get_fact_layer_unofficial,
    load_yaml,
    section_score,
    validate_data,
)


SCORE_HEADERS = [label for _, _, label in SECTION_ORDER]
FACT_COLUMNS = [
    ("初任給", "starting_salary_yen", format_yen),
    ("学士初任給", "starting_salary_bachelor_yen", format_yen),
    ("修士初任給", "starting_salary_master_yen", format_yen),
    ("博士初任給", "starting_salary_doctor_yen", format_yen),
    ("平均年収", "average_annual_income_yen", format_yen),
    ("月平均残業", "average_overtime_hours_per_month", format_overtime_hours),
    ("年間休日", "annual_holidays_days", format_days),
    ("リモート", "remote_work_policy", format_remote_policy),
]
DISPLAY_FACT_KEYS = [key for _, key, _ in FACT_COLUMNS]

HEADERS = [
    "slug",
    "会社名",
    "応募対象単位",
    "採用 entity",
    "職種ファミリー",
    "統合最終評価",
    *SCORE_HEADERS,
    *[label for label, _, _ in FACT_COLUMNS],
]


def expand_inputs(raw_inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in raw_inputs:
        path = Path(raw)
        if path.is_dir():
            paths.extend(sorted(path.rglob("*.yaml")))
        else:
            paths.append(path)
    return paths


def is_missing_fact_value(value: object) -> bool:
    return value is None or value == "unknown"


def merge_fact_layers(
    official: dict[str, object],
    unofficial: dict[str, object] | None,
) -> dict[str, object]:
    merged = dict(official)
    if not unofficial:
        return merged

    for key in DISPLAY_FACT_KEYS:
        if is_missing_fact_value(merged.get(key)) and not is_missing_fact_value(
            unofficial.get(key)
        ):
            merged[key] = unofficial[key]
    return merged


def build_raw_row(path: Path, use_unofficial_fallback: bool = False) -> list[object]:
    data = load_yaml(path)
    result = validate_data(data, str(path))
    if result.issues:
        joined = "; ".join(result.issues)
        raise ValueError(f"{path}: {joined}")

    structured = get_fact_layer_official(data)
    if use_unofficial_fallback:
        structured = merge_fact_layers(structured, get_fact_layer_unofficial(data))
    return [
        data["slug"],
        data["company_name"],
        data["scope"]["target_application_unit"],
        data["scope"]["hiring_entity_name"],
        data["scope"]["role_family"],
        compute_total(data),
        *[
            section_score(data["sections"][key])
            for key, _, _ in SECTION_ORDER
        ],
        *[structured[key] for _, key, _ in FACT_COLUMNS],
    ]


def build_raw_row_with_unofficial_fallback(path: Path) -> list[object]:
    return build_raw_row(path, use_unofficial_fallback=True)


def build_row(path: Path, use_unofficial_fallback: bool = False) -> list[str]:
    raw_row = build_raw_row(path, use_unofficial_fallback=use_unofficial_fallback)
    fact_start = 6 + len(SCORE_HEADERS)
    return [
        raw_row[0],
        raw_row[1],
        raw_row[2],
        raw_row[3],
        raw_row[4],
        f"{raw_row[5]:.1f}",
        *[f"{value:.1f}" for value in raw_row[6 : 6 + len(SCORE_HEADERS)]],
        *[
            formatter(raw_row[fact_start + idx])
            for idx, (_, _, formatter) in enumerate(FACT_COLUMNS)
        ],
    ]


def collect_raw_rows(paths: list[Path]) -> list[list[object]]:
    return [build_raw_row(path) for path in sorted(paths)]


def collect_raw_rows_with_unofficial_fallback(
    paths: list[Path],
) -> list[list[object]]:
    return [build_raw_row_with_unofficial_fallback(path) for path in sorted(paths)]


def collect_rows(paths: list[Path]) -> list[list[str]]:
    return [build_row(path) for path in sorted(paths)]


def render_markdown(paths: list[Path]) -> str:
    lines = [
        "# 企業共通データ一覧",
        "",
        "各社 YAML の構造化共通項目と Python 集計による総合評価を一覧化した表。",
        "",
        "| " + " | ".join(HEADERS) + " |",
        "| " + " | ".join(["---"] * len(HEADERS)) + " |",
    ]
    for row in collect_rows(paths):
        lines.append("| " + " | ".join(row) + " |")
    lines.extend(
        [
            "",
            "注記:",
            "- `未公表` は YAML 上で `null` だった項目。",
            "- `統合最終評価` は company-analysis YAML 実装の重みに基づく。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_csv(paths: list[Path], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADERS)
        for row in collect_rows(paths):
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="Input YAML files")
    parser.add_argument("--output", required=True, help="Output Markdown path")
    args = parser.parse_args()

    input_paths = expand_inputs(args.inputs)
    output_path = Path(args.output)
    if output_path.suffix.lower() == ".csv":
        render_csv(input_paths, output_path)
    else:
        markdown = render_markdown(input_paths)
        output_path.write_text(markdown, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
