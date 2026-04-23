#!/usr/bin/env python3
"""
Compatibility shim for company-analysis YAML helpers.

The implementation lives under the company-analysis-runner skill:
`.agents/skills/company-analysis-runner/tool/company_analysis_yaml.py`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


IMPL_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents/skills/company-analysis-runner/tool/company_analysis_yaml.py"
)

if not IMPL_PATH.exists():
    raise ImportError(f"company-analysis implementation not found: {IMPL_PATH}")

SPEC = importlib.util.spec_from_file_location(
    "company_analysis_yaml_impl",
    IMPL_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"failed to load company-analysis implementation: {IMPL_PATH}")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

for name in dir(MODULE):
    if name.startswith("_"):
        continue
    globals()[name] = getattr(MODULE, name)

