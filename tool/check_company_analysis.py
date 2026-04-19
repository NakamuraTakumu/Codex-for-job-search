#!/usr/bin/env python3
"""
Usage:
  python3 tool/check_company_analysis.py path/to/file.md [path/to/file2.md ...]

What it does:
  - Checks company-analysis markdown files for required sections.
  - Verifies that the survey date is present directly under the H1.
  - Verifies that each scoring section has fact/evaluation/score bullets.
  - Verifies that the final score matches the score shown in the calculation.

What it does not do:
  - It does not modify any file.
  - It does not rewrite formatting.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQ_HEADINGS = [
    "## 結論",
    "## 分析対象の確定",
    "## 1. 博士人材の評価",
    "## 2. 仕事内容・配属確度",
    "## 3. 研究開発・技術環境",
    "## 4. 処遇・働き方",
    "## 5. 選考コストと評価の納得感",
    "## 6. 企業基盤・安定性",
    "## 数式評価",
    "## 補正",
    "## 最終評価",
    "## 向いている人",
    "## 向いていない人",
    "## 懸念点",
    "## 参考文献",
]

SCORE_SECTIONS = REQ_HEADINGS[2:8]
WEIGHTS = [0.30, 0.10, 0.05, 0.25, 0.10, 0.20]


def section_body(text: str, heading: str) -> str | None:
    pattern = rf"(?ms)^{re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text)
    return match.group(1) if match else None


def first_score_value(text: str, heading: str) -> str | None:
    body = section_body(text, heading)
    if body is None:
        return None
    match = re.search(r"- スコア（統合・補正前）:\s*`?([0-9]+(?:\.[0-9])?) / 5(?:\.0)?`?", body)
    return match.group(1) if match else None


def computed_total(scores: list[str]) -> str:
    vals = [float(score) for score in scores]
    total = 20 * sum(weight * val for weight, val in zip(WEIGHTS, vals, strict=True))
    return f"{total:.1f}"


def calc_total(text: str) -> str | None:
    body = section_body(text, "## 数式評価")
    if body is None:
        return None
    match = re.search(
        r"(?m)^- `統合総合評価（補正前） = ([0-9]+(?:\.[0-9])?)`$",
        body,
    )
    return match.group(1) if match else None


def final_total(text: str) -> str | None:
    body = section_body(text, "## 最終評価")
    if body is None:
        return None
    match = re.search(r"統合最終評価:\s*([0-9]+(?:\.[0-9])?)\s*/\s*100", body)
    return match.group(1) if match else None


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []

    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        issues.append("missing H1 title")
    if len(lines) < 2 or not re.fullmatch(r"調査日: \d{4}-\d{2}-\d{2}", lines[1]):
        issues.append("missing survey date directly below H1")

    for heading in REQ_HEADINGS:
        if heading not in text:
            issues.append(f"missing heading: {heading}")

    for heading in SCORE_SECTIONS:
        body = section_body(text, heading)
        if body is None:
            continue
        for label in ("- 公式情報:", "- 評価:", "- スコア（公式）:", "- スコア（統合・補正前）:"):
            if label not in body:
                issues.append(f"{heading}: missing {label}")

    scores = [first_score_value(text, heading) for heading in SCORE_SECTIONS]
    if any(score is None for score in scores):
        issues.append("one or more section scores could not be parsed")
    else:
        expected = computed_total(scores)  # type: ignore[arg-type]

    calc = calc_total(text)
    final = final_total(text)
    if calc is None:
        issues.append("could not parse calculated total from ## 数式評価")
    if final is None:
        issues.append("could not parse final total from ## 最終評価")
    if all(score is not None for score in scores):
        if calc is not None and calc != expected:
            issues.append(f"calculated total {calc} does not match recomputed total {expected}")
        if final is not None and final != expected:
            issues.append(f"final total {final} does not match recomputed total {expected}")
    if calc is not None and final is not None and calc != final:
        issues.append(f"calculated total {calc} does not match final total {final}")

    return issues


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip())
        return 2

    bad = 0
    for raw in argv[1:]:
        path = Path(raw)
        if not path.exists():
            print(f"{path}: not found")
            bad = 1
            continue
        issues = check_file(path)
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
