# Workspace Rules

## Document Organization
- Organize reusable documents under `document/` with topic-specific subdirectories instead of placing many files directly in `document/`.
- In this repository, company-analysis-related reusable documents may be placed directly under `document/` when the repository itself is already specialized enough that an extra `company_analysis/` label would be redundant.
- For company analysis outputs, use `report/company_analysis/companies/` for per-company analyses and `report/company_analysis/reviews/` for cross-company reviews or comparisons.
- Prefer concise document filenames. Avoid redundant prefixes when the parent directory already provides the context.
- Choose the shortest filename that still remains unambiguous within its directory.
- For company-analysis outputs, default to concise target-based slugs and filenames without dates, such as `japan_ibm_research`.
- Add a date to a company-analysis slug or filename only when it is needed to distinguish multiple valid runs, avoid collisions in the same directory, or preserve parallel test artifacts explicitly.

## Test vs Production Data
- Keep data, reports, and artifacts produced for testing clearly separate from production or accepted outputs.
- Do not overwrite or mix production files with test-generated files unless the user explicitly approves promotion of the test result.
- Make the distinction explicit in filenames, paths, or metadata so test outputs remain recognizable later.

## Evaluation Tasks
- In evaluation or scoring tasks, fix the exact evaluation target before scoring. Do not score a broad entity first and narrow the target afterward.
- When multiple evaluation results are compared for uncertainty analysis, separate `evaluation-target mismatch` from `scoring variance`. If the fixed targets differ, treat that as a scope problem first rather than as pure scoring disagreement.
- When naming structured-data keys for evaluation scope, make the key reveal both the value type and the semantic unit. Avoid vague names such as `evaluation_target` or `job_type` when the value could be confused between a company, application route, role family, or hiring category; prefer names like `target_application_unit`, `hiring_entity_name`, `role_family`, and `stability_entity_name` when those are the intended meanings.

## Company Analysis Workflow
- For company-analysis tasks, prefer using the `company-analysis-runner` skill as the default entry point.
- When a company-analysis task is requested, do not perform parent-side pre-analysis first; invoke the `company-analysis-runner` workflow immediately.
- Treat `company-analysis-runner` as the parent-agent orchestration layer and `company-analysis` as the evaluator used by subagents.
- Only bypass `company-analysis-runner` when the task is narrowly limited to inspecting or editing existing outputs, tools, or documentation rather than running the analysis workflow itself.
- For company-analysis-specific tooling, prefer placing scripts under the relevant skill directory rather than the repository-wide `tool/` directory, unless the script is genuinely shared across workflows in this repository.
- For research-oriented doctoral-candidate company analysis, when an official research-track application route exists, prefer fixing the default evaluation target to that research track first.
- Use a software-engineering or broader technical track as the default target only when no official research-track route exists, or when the user explicitly asks to analyze the engineering track instead.
- If both research and software-engineering routes officially exist, the parent may still analyze both as separate targets when the user asks for both or when comparison is the point, but the default single-target choice should be the research track.
- Require `run_metadata` in final company-analysis YAML outputs. Do not treat it as optional when the parent workflow is available; missing `run_metadata` should be considered an invalid final artifact.
- For company-analysis naming, keep `slug` and saved filenames aligned, and default to the shortest stable target-based name that remains unambiguous without a date.
- For fairness across companies, when `company-analysis-runner` hands off work to analysis or review subagents, pass the corresponding prompt template exactly as written except for filling its placeholders. Do not paraphrase, reorder, trim, or append ad hoc instructions unless the template file itself is intentionally updated first.
- When a review subagent is used in the company-analysis workflow, pass the analysis YAML and any rendered Markdown as inline data in the prompt rather than handing off repository file paths or asking the subagent to fetch them from the filesystem.

## Drafting and Review Separation
- When a task involves drafting an artifact and then checking, reviewing, or critiquing that artifact, prefer using a separate subagent for review rather than having the drafting subagent review its own output.
- Do not treat self-review by the drafting subagent as sufficient when an independent check is practical and materially improves reliability.
- If the same artifact needs both creation and verification, assign clear ownership: one agent drafts, another agent checks or reviews.
