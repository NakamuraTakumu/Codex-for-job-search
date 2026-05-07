#!/usr/bin/env python3
"""Extract top company-analysis targets for recruitment-info runs.

Usage:
  python3 extract_top_score_targets.py --limit 10 --output /tmp/top.yaml
  python3 extract_top_score_targets.py --data-dir report/company_analysis/data --limit 5
  python3 extract_top_score_targets.py --profile phd --limit 20
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml


SECTIONS = (
    "phd_value",
    "role_fit",
    "rd_env",
    "compensation",
    "hiring_process",
    "stability",
)

WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "equal": {section: 1.0 / len(SECTIONS) for section in SECTIONS},
    "phd": {
        "phd_value": 0.30,
        "role_fit": 0.10,
        "rd_env": 0.05,
        "compensation": 0.25,
        "hiring_process": 0.10,
        "stability": 0.20,
    },
}


def load_yaml(path: Path) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def target_id(company_name: str, fallback: str) -> str:
    raw = company_name.lower()
    raw = re.sub(r"[^a-z0-9]+", "_", raw)
    normalized = re.sub(r"_+", "_", raw).strip("_")
    return normalized if len(normalized) >= 8 else fallback


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def population_sd(values: list[float], average: float) -> float:
    variance = sum((value - average) ** 2 for value in values) / len(values)
    return variance ** 0.5


def extract(data_dir: Path, limit: int, profile: str) -> dict[str, Any]:
    weights = WEIGHT_PROFILES[profile]
    rows: list[dict[str, Any]] = []
    for path in sorted(data_dir.glob("*.yaml")):
        data = load_yaml(path)
        if not data:
            continue
        sections = data.get("sections")
        if not isinstance(sections, dict):
            continue
        scores: dict[str, float] = {}
        for section in SECTIONS:
            item = sections.get(section)
            if not isinstance(item, dict) or not isinstance(item.get("score"), (int, float)):
                break
            scores[section] = float(item["score"])
        if len(scores) != len(SECTIONS):
            continue
        scope = data.get("scope") if isinstance(data.get("scope"), dict) else {}
        company_name = str(data.get("company_name") or "")
        avg = sum(scores.values()) / len(scores)
        rows.append(
            {
                "target_id": target_id(company_name, path.stem),
                "company_name": company_name,
                "source_file": path.name,
                "score_average": round(avg, 3),
                "score_total": round(sum(scores.values()), 1),
                "section_scores": scores,
            }
        )

    section_stats: dict[str, dict[str, float]] = {}
    for section in SECTIONS:
        values = [row["section_scores"][section] for row in rows]
        if not values:
            section_stats[section] = {"mean": 0.0, "sd": 1.0}
            continue
        average = mean(values)
        sd = population_sd(values, average)
        section_stats[section] = {"mean": average, "sd": sd if sd > 0 else 1.0}

    weighted_values: list[float] = []
    for row in rows:
        weighted_z = 0.0
        for section in SECTIONS:
            stats = section_stats[section]
            z_score = (row["section_scores"][section] - stats["mean"]) / stats["sd"]
            weighted_z += weights[section] * z_score
        row["weighted_z"] = weighted_z
        weighted_values.append(weighted_z)

    weighted_mean = mean(weighted_values) if weighted_values else 0.0
    weighted_sd = population_sd(weighted_values, weighted_mean) if weighted_values else 1.0
    if weighted_sd <= 0:
        weighted_sd = 1.0
    for row in rows:
        normalized = 50 + 10 * ((row["weighted_z"] - weighted_mean) / weighted_sd)
        row["weighted_score"] = round(max(0, min(100, normalized)), 1)
        row["weighted_z"] = round(row["weighted_z"], 6)

    rows.sort(key=lambda r: (r["weighted_score"], r["score_average"], r["score_total"]), reverse=True)
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        company = row["company_name"]
        if company in seen:
            continue
        seen.add(company)
        unique.append(row)
        if len(unique) >= limit:
            break
    return {
        "score_basis": f"{profile} weighted z-score normalized model from company-analysis YAML section scores",
        "weight_profile": profile,
        "weights": weights,
        "normalization": {
            "section_stats": {
                section: {
                    "mean": round(stats["mean"], 6),
                    "sd": round(stats["sd"], 6),
                }
                for section, stats in section_stats.items()
            },
            "weighted_z_mean": round(weighted_mean, 6),
            "weighted_z_sd": round(weighted_sd, 6),
            "score_formula": "50 + 10 * ((weighted_z - weighted_z_mean) / weighted_z_sd), bounded to 0..100",
        },
        "data_dir": str(data_dir),
        "targets": unique,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="report/company_analysis/data")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--profile", choices=sorted(WEIGHT_PROFILES), default="phd")
    parser.add_argument("--output")
    args = parser.parse_args()

    result = extract(Path(args.data_dir), args.limit, args.profile)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
