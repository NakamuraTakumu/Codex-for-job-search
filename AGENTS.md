# Workspace Rules

## Document Organization
- Organize reusable documents under `document/` with topic-specific subdirectories instead of placing many files directly in `document/`.
- For company analysis outputs, use `report/company_analysis/companies/` for per-company analyses and `report/company_analysis/reviews/` for cross-company reviews or comparisons.
- Prefer concise document filenames. Avoid redundant prefixes when the parent directory already provides the context.
- Choose the shortest filename that still remains unambiguous within its directory.

## Test vs Production Data
- Keep data, reports, and artifacts produced for testing clearly separate from production or accepted outputs.
- Do not overwrite or mix production files with test-generated files unless the user explicitly approves promotion of the test result.
- Make the distinction explicit in filenames, paths, or metadata so test outputs remain recognizable later.

## Evaluation Tasks
- In evaluation or scoring tasks, fix the exact evaluation target before scoring. Do not score a broad entity first and narrow the target afterward.
- When multiple evaluation results are compared for uncertainty analysis, separate `evaluation-target mismatch` from `scoring variance`. If the fixed targets differ, treat that as a scope problem first rather than as pure scoring disagreement.

## Company Analysis Workflow
- For company-analysis tasks, prefer using the `company-analysis-runner` skill as the default entry point.
- When a company-analysis task is requested, do not perform parent-side pre-analysis first; invoke the `company-analysis-runner` workflow immediately.
- Treat `company-analysis-runner` as the parent-agent orchestration layer and `company-analysis` as the evaluator used by subagents.
- Only bypass `company-analysis-runner` when the task is narrowly limited to inspecting or editing existing outputs, tools, or documentation rather than running the analysis workflow itself.

## Drafting and Review Separation
- When a task involves drafting an artifact and then checking, reviewing, or critiquing that artifact, prefer using a separate subagent for review rather than having the drafting subagent review its own output.
- Do not treat self-review by the drafting subagent as sufficient when an independent check is practical and materially improves reliability.
- If the same artifact needs both creation and verification, assign clear ownership: one agent drafts, another agent checks or reviews.
