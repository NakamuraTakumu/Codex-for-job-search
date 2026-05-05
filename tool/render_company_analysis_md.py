#!/usr/bin/env python3
"""
Usage:
  python3 tool/render_company_analysis_md.py path/to/file.yaml [path/to/file2.yaml ...]
  python3 tool/render_company_analysis_md.py --stdout path/to/file.yaml
  python3 tool/render_company_analysis_md.py --output path/to/file.md path/to/file.yaml
  python3 tool/render_company_analysis_md.py --output-dir report/company_analysis/companies path/to/file.yaml

What it does:
  - Validates company-analysis YAML files.
  - Renders normalized Markdown output from the YAML input.

What it does not do:
  - It does not guess missing schema fields.
  - It does not protect against output path collisions. Use --output with a run-scoped path when running in parallel.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from company_analysis_yaml import load_yaml, render_markdown, validate_data


DATA_ROOT = Path("report/company_analysis/data")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render company-analysis Markdown from YAML.")
    parser.add_argument("paths", nargs="+", help="YAML files to render")
    parser.add_argument(
        "--output-dir",
        default="report/company_analysis/companies",
        help="Directory for rendered Markdown files (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        help="Write rendered Markdown to this file. Use with one input file.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print rendered Markdown to stdout instead of writing files. Use with one input file.",
    )
    args = parser.parse_args(argv[1:])
    if args.stdout and args.output:
        parser.error("--stdout and --output cannot be used together")
    if args.output and len(args.paths) != 1:
        parser.error("--output requires exactly one input file")
    return args


def infer_output_path(input_path: Path, output_dir: Path, data: dict) -> Path:
    try:
        rel = input_path.resolve().relative_to(DATA_ROOT.resolve())
    except Exception:
        return output_dir / f"{data['slug']}.md"
    return output_dir / rel.with_suffix(".md")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.stdout and len(args.paths) != 1:
        print("--stdout requires exactly one input file", file=sys.stderr)
        return 2

    out_dir = Path(args.output_dir)
    explicit_output = Path(args.output) if args.output else None
    if explicit_output:
        explicit_output.parent.mkdir(parents=True, exist_ok=True)
    elif not args.stdout:
        out_dir.mkdir(parents=True, exist_ok=True)

    bad = 0
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            print(f"{path}: not found", file=sys.stderr)
            bad = 1
            continue
        try:
            data = load_yaml(path)
        except Exception as exc:
            print(f"{path}: failed to parse YAML: {exc}", file=sys.stderr)
            bad = 1
            continue
        result = validate_data(data, source_name=str(path))
        if result.issues:
            print(f"{path}: validation failed", file=sys.stderr)
            for issue in result.issues:
                print(f"  - {issue}", file=sys.stderr)
            bad = 1
            continue
        rendered = render_markdown(result.data or data)
        if args.stdout:
            sys.stdout.write(rendered)
            if not rendered.endswith("\n"):
                sys.stdout.write("\n")
        else:
            out_path = explicit_output or infer_output_path(path, out_dir, result.data or data)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
            print(out_path)
    return bad


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
