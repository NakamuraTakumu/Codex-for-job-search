#!/usr/bin/env python3
"""
Render a common-data table from company-analysis YAML files.

Usage:
    python3 tool/render_company_common_table.py \
        document/company_analysis/data/*.yaml \
        --output document/company_analysis/reviews/common_data_20260416.md

    python3 tool/render_company_common_table.py \
        document/company_analysis/data/*.yaml \
        --output document/company_analysis/reviews/common_data_20260416.csv

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
    compute_final_total,
    format_days,
    format_overtime_hours,
    format_remote_policy,
    format_yen,
    load_yaml,
    validate_data,
)


HEADERS = [
    "会社名",
    "採用職種",
    "総合評価",
    "初任給",
    "平均年収",
    "月平均残業",
    "年間休日",
    "リモート",
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


def build_row(path: Path) -> list[str]:
    data = load_yaml(path)
    result = validate_data(data, str(path))
    if result.issues:
        joined = "; ".join(result.issues)
        raise ValueError(f"{path}: {joined}")

    structured = data["sections"]["compensation"]["structured"]
    return [
        data["company_name"],
        data["scope"]["job_type"],
        f"{compute_final_total(data):.1f}",
        format_yen(structured["starting_salary_yen"]),
        format_yen(structured["average_annual_income_yen"]),
        format_overtime_hours(structured["average_overtime_hours_per_month"]),
        format_days(structured["annual_holidays_days"]),
        format_remote_policy(structured["remote_work_policy"]),
    ]


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
            "- 総合評価は `tool/company_analysis_yaml.py` の重みと補正に基づく。",
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
