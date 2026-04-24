---
name: company-analysis-runner
description: Parent orchestration skill for fixed-target company analysis that launches `company-analysis` evaluators, validates and renders returned YAML with fact_layer and section scores, and adds lightweight review or uncertainty checks only when needed.
---

# Purpose
- Use this skill when the parent agent needs to run company analysis end to end.
- Delegate the actual research pass to child agents using the `company-analysis` skill.
- The parent agent handles scope fixing, child launch, YAML validation, Markdown rendering, and file saving.
- When using this skill, the actual investigation and section scoring must always be done by subagents; the parent stays focused on orchestration.
- Review is not mandatory on every run. Add it only when there are high-risk issues that validator checks alone are unlikely to catch.
- Unless there is a strong reason not to, use `gpt-5.4-mini` as the default model for both analysis children and review children.
- Unless there is a strong reason not to, use `medium` as the default `reasoning_effort` for both analysis children and review children.

# Preconditions
- This skill uses subagents for the actual research and scoring work of company analysis.
- When running company analysis through this skill, the parent must not write the analysis body itself; investigation and section scores must be delegated to child agents.
- If a child model must be specified, start with `gpt-5.4-mini` and only move to a larger model when public information is extremely ambiguous, review feedback requires a rerun, or reasoning weakness is clearly visible.
- If a child `reasoning_effort` must be specified, start with `medium` and only move higher when public information is extremely ambiguous, review feedback requires a rerun, or reasoning weakness is clearly visible.
- Before research starts, decide at least:
  - `company_name`
  - `survey_date`
  - `slug`
  - `scope.user_label`
  - `scope.evaluation_target`
  - `scope.hiring_entity`
  - `scope.job_type`
  - `scope.placement_candidates`
  - `scope.stability_entity`
- Even if the user gives only a company name, do not widen the task into a whole-company evaluation. Fix an `evaluation_target` that is close to the actual application unit first.
- When the assumed candidate is a current doctoral student or a recent doctoral graduate without clear full-time work experience, prefer new-graduate tracks. Use experienced-hire tracks only when no new-graduate route exists, the new-graduate route is clearly inapplicable, or it is explicitly unsuitable.
- Determine the existence of research and software-engineering tracks from whether an official new-graduate-equivalent application route exists, not from whether the role merely seems realistic.
- If an official research-track route exists, prefer that research track as the default single `evaluation_target` for this workflow.
- Use a software-engineering track as the default target only when no official research-track route exists, or when the user explicitly asks for the engineering track instead.
- If both research and software-engineering application routes are officially confirmed, treat them as separate `evaluation_target`s when the user asks for both or when comparison is the goal; otherwise, default to the research track.
- When both tracks are analyzed, do not show them sequentially to the same child. Launch separate children for `research` and `swe`.
- Do not infer a research or software-engineering track from the existence of a lab page or technical PR page alone. Prioritize official recruiting routes such as job postings, recruiting pages, FAQ, or explanatory material.
- When parent-company or group-company numbers are used to support stability, preserve the mismatch between `scope.hiring_entity` and `scope.stability_entity`.
- If the official company identity is ambiguous and nearby corporate entities must also be checked, the parent should narrow the candidates to roughly three to five entities and treat them as separate `evaluation_target`s.
- If the user gives only a company name, the parent should also inspect major subsidiaries and nearby entities first and check whether each has its own independent new-graduate hiring route.
- Even when independent subsidiary hiring is found, the parent must not automatically analyze all of them. Summarize the candidates and their hiring status, then let the user choose the main analysis target.
- If multiple companies are given together, do not stop partway through each one. First scan all companies for subsidiaries, nearby entities, and independent hiring routes, then move to target confirmation.
- When many companies or targets are pending, keep one shared review-child slot reserved and use the remaining available child capacity for scanning or analysis children.
- When many companies or targets are pending, prefer bounded parallelism with a refill queue over an all-at-once launch. As soon as one child finishes or becomes blocked on correction, reuse that slot for the next pending company or target.

# Main workflow
1. If multiple companies are given, first inspect each company’s official information and collect major subsidiaries or nearby entities across the whole set. When the set is large, do this first-pass scan in parallel where practical.
2. For each company and each candidate entity, check whether an independent new-graduate hiring route exists.
3. Summarize the candidates by company. If multiple independently hiring entities exist, let the user choose which one should become the main analysis target.
4. If only one company is given, follow the same process for that company.
5. Once the target entity is fixed, inspect its official recruiting route and check whether research and software-engineering tracks exist.
6. If both `research` and `swe` are found, the parent decides how to handle them. By default it should fix `research` only; fix both as separate `evaluation_target`s when the user asks for both or when comparison is the point.
7. If the `evaluation_target` is still ambiguous, the parent must fix the application unit, hiring entity, job type, and, when needed, placement candidates before analysis starts.
8. As soon as the runner starts, launch one shared review-only child and keep it ready for inline review payloads.
9. For each fixed track, launch one child agent using the `company-analysis` evaluator. Do not block on file naming or review payload details before starting the child.
   - As a rule, specify `gpt-5.4-mini` as the model.
   - As a rule, specify `medium` as `reasoning_effort`.
   - Build the child prompt by filling `subagent_prompt_template.txt` placeholders only. Do not paraphrase, reorder, trim, or append ad hoc instructions around the template unless the template file itself is intentionally changed first.
   - When many fixed targets exist, keep the remaining child slots busy from a pending queue instead of launching one batch and idling. As soon as one analysis child finishes validation / review handoff or becomes blocked on correction, launch the next pending target.
10. Instruct each child to return a complete YAML object only.
11. Instruct the child to first fill `fact_layer.official` and `facts_official` from official information, then add `fact_layer.unofficial` and `facts_unofficial` as supporting unofficial information, and only then assign a single final `score`.
12. If important gaps remain after the official pass, require the child to perform at least one unofficial pass. Even if no usable value is found, require it to record searched unofficial lineages and failed-search reasons.
13. Do not require full official completeness before unofficial observations can be recorded. Relevant unofficial observations may be kept in `facts_unofficial` or `summary.concerns` as soon as they are found.
14. Explicitly tell the child not to mix official and unofficial information in the same field.
15. Explicitly tell the child to count unofficial evidence by independent lineage rather than raw URL count, and not to treat reposts, mirrors, or alternate surfaces of the same service as independent support.
16. If needed, explicitly tell the child not to read existing reports or other agent outputs.
17. Use one child per target as the default, and never feed `research` and `swe` sequentially to the same child.
18. Make the fixed `evaluation_target`, `hiring_entity`, and `job_type` explicit in the prompt so the child does not silently switch targets.
19. The parent chooses the `slug` for each target. Default to the shortest stable target-based slug that remains unambiguous, for example `japan_ibm_research` or `ntt_data_swe`.
   - Do not add dates by default.
   - Add a date suffix only when it is needed to distinguish multiple valid runs, avoid collisions in the same directory, or preserve parallel test artifacts explicitly.
   - If multiple targets exist, split them deterministically, for example `<company_slug>_<target_suffix>`, and do not reuse the same slug inside one run.
20. Append `run_metadata` to the YAML before accepting it as final. At minimum, use `executor`, `model`, `reasoning_effort`, and `fixed_by_parent`.
21. The parent decides where the returned YAML will be saved. The child must not save, update, or generate files on its own; it should return YAML only in the message.
22. As soon as any child returns YAML, process that child immediately. When multiple children are running, do not wait for all of them to finish before starting validation or review.
    - Keep the workflow pipelined: while one artifact is in validation or review, other analysis children should continue running whenever free slots remain.
23. Run `python3 tool/check_company_analysis_yaml.py <yaml-file>` to validate the format.
24. If validator checks fail, list the schema violations and send the YAML back to the child for a full re-output.
25. Once validator checks pass, the parent performs a light high-risk review on that YAML itself and decides whether a content review is needed before rendering.
26. Only when that pre-render check suggests content review is needed, embed the fixed scope and analysis YAML directly into the prompt and send them to the already-running shared review child to obtain review YAML.
   - As a rule, specify `gpt-5.4-mini` for the review child as well.
   - As a rule, specify `medium` as `reasoning_effort` for the review child as well.
   - Do not respawn the review child for each company or target by default. Reuse the same shared review child across multiple companies/targets in one parent run unless a reset is clearly needed.
   - On every review handoff, explicitly reset the review context. Tell the shared review child to ignore all previous review payloads, previous slugs, previous findings, and previous rendered outputs, and to judge only the inline payload embedded in the current prompt.
   - On every review handoff, explicitly restate the current intended `slug` and say that it is not a scope error.
27. Run `python3 tool/check_company_analysis_review.py <review-yaml>` to validate the review schema.
28. If the content-review verdict is `revise`, list the findings and send them back to the analysis child, requiring a full corrected YAML re-output.
29. Once the YAML is accepted for rendering, generate Markdown with `python3 tool/render_company_analysis_md.py <yaml-file>`.
30. Only when render-level confirmation is needed should the parent send the rendered Markdown, together with the fixed scope and analysis YAML, to the review child for a render-focused review.
31. Run `python3 tool/check_company_analysis_review.py <review-yaml>` for that render-focused review as well.
32. If the render-focused review returns `revise`, resolve the findings, rerun renderer or reviewer as needed, and only then finalize the artifacts.
33. In the final answer, refer to the saved YAML and Markdown, and refer to the review artifact as well if review was generated.

# Prompt template
Use `subagent_prompt_template.txt` in this skill directory as the default prompt template for analysis children.

- The parent should fill the `{{...}}` placeholders with the fixed scope.
- Even when `research` and `swe` are run in parallel, each child should receive only the template filled with its own fixed scope.
- Do not mix information about a different track of the same company into the prompt as comparison notes; compare later in the parent if needed.
- For fairness across companies, pass the template text itself after placeholder substitution. Do not paraphrase it, reorder it, trim it, or append side instructions outside the template body.
- Do not rewrite the template ad hoc on every run. If the prompt must change, edit the template file itself.
- When an analysis child is reused across multiple companies or targets, keep the template’s reset instruction intact so each handoff is treated as a fresh, self-contained target.
- On every analysis handoff, explicitly restate the current intended `slug` and require the YAML to be filled only from the current fixed scope and current-target sources.
- Keep the template’s fixed sequence: official information first, then unofficial information recorded separately.
- Keep in the template the rule that unofficial passes must not be skipped when important gaps remain, and that failed searches must still record checked lineages and reasons.

Use `review_prompt_template.txt` in this skill directory as the default prompt template for review children.

- The parent should fill the template with the fixed scope, the full analysis YAML text, and, when needed, the full rendered Markdown text.
- The default review input should be the analysis YAML text only.
- Add rendered Markdown only when render-level confirmation is actually needed.
- Review children must use the `company-analysis-review` skill.
- Do not use repository file paths as the handoff mechanism for review children.
- In inline handoff, do not use Markdown fences; embed payloads as plain-text blocks with explicit delimiters.
- When the shared review child is reused, keep the template’s reset instruction intact so each review is treated as a fresh, self-contained target.
- For fairness across companies, pass the review template text itself after placeholder substitution. Do not paraphrase it, reorder it, trim it, or append side instructions outside the template body.
- Do not rewrite the review template ad hoc on every run. If the prompt must change, edit the template file itself.

# Validation
- The main validator is `tool/check_company_analysis_yaml.py`.
- The review validator is `tool/check_company_analysis_review.py`.
- The renderer is `tool/render_company_analysis_md.py`.
- The Python implementation is the source of truth for total-score calculation; do not ask child agents to recompute totals.
- `run_metadata` is required in final accepted YAML. At minimum, use `executor`, `model`, `reasoning_effort`, and `fixed_by_parent`.
- The parent should append the actual child-launch settings it used. Do not leave `model` or `reasoning_effort` implicit in final accepted YAML.
- By the time child YAML is accepted as final output, it must satisfy the validator’s hard requirements. In particular, official sources must include at least four entries and cover `recruit` and `company|ir`. `faq`, `benefits`, and official `kind=research` sources are still priority search targets, but if they do not exist publicly they should be recorded as absence or thin public coverage rather than treated as automatic failure. These are final acceptance conditions and are not reasons to stop recording unofficial lineages or tentative notes.
- The parent manages test vs production save locations separately; this skill does not fix them.

# Review workflow
- Review is not mandatory on every run; use it only when the parent’s high-risk check says it is needed.
- The content review itself should be done by a shared review-only subagent, separate from the analysis child.
- Launch the shared review-only subagent as soon as the runner starts, even if the first review payload has not arrived yet.
- Do not recreate the review agent for each company by default; keep one shared review-only subagent and reuse it across companies/targets in the same parent session when practical.
- When multiple analysis children are running, send the first completed child to review immediately instead of batching all completed analyses first.
- The parent passes the fixed scope and reviewed YAML data directly to the review child.
- Rendered Markdown is for a separate post-render review path; add it only when render-level confirmation is needed.
- The review child must not regenerate YAML; it should return only the fixed review schema.
- After obtaining review YAML, run `python3 tool/check_company_analysis_review.py <review-yaml>` to validate the review schema.
- When a pre-render content review returns `revise`, the parent must not edit the analysis content itself. Return the findings to the analysis child and require a full corrected YAML re-output.
- Default to at most one corrective rerun and one rereview per artifact. Do not keep the same artifact in an open-ended review loop unless a validator failure or a new high-severity issue appears.
- In the rereview, focus on whether the prior findings were resolved. Do not broaden into a fresh full review unless a new high-severity issue is visible.
- To simplify the retry loop, even light content fixes should normally be handled by the analysis child. The parent may fix only mechanical issues such as save names or temporary-file handling.
- During review, do not overfit to prior comparison results or an intended answer. Judge from the inline target data and the minimum context needed.

## Pre-render content-review triggers
- Launch a content review child before rendering if any of the following is true:
  - `fact_layer` contains assertive values such as `true` or `false` and the official support may be thin.
  - `summary`, `concerns`, or `not_suitable_for` contain claims that are broader or stronger than the section bodies support.
  - Unofficial information conflicts with official information and materially affects the final judgment.
  - `facts_official` or `facts_unofficial` look too thin to preserve enough information for comparison or re-judgment.
  - Important gaps remain, but the analysis text does not preserve their seriousness or the lack of further search clearly enough.
  - Important gaps remain, but unofficial sources are zero and there is no failed-search record for the unofficial pass.
- If none of these triggers is present, pre-render content review may be skipped.

## Post-render review triggers
- Launch a render-focused review after Markdown is generated if either of the following is true:
  - The parent suspects render-level inconsistency.
  - The parent wants explicit confirmation that rendered Markdown still matches the accepted YAML.
- Even when all review steps are skipped, validator checks and rendering must still be performed.

## Review rubric
### Required checks
- `scope_integrity`
  - Whether `evaluation_target`, `hiring_entity`, `job_type`, `placement_candidates`, and `stability_entity` match the parent-fixed scope.
- `source_separation`
  - Whether unofficial information leaks into `facts_official`.
  - Whether official information leaks into `facts_unofficial`.
  - Whether `sources.tier` matches the actual evidence tier.
- `source_quality`
  - Whether official sources are sufficient.
  - Whether unofficial sources dominate the evaluation too strongly.
  - Whether the evidence base is overly repetitive.
  - Whether reposts, mirrors, or alternate surfaces of the same unofficial service are being double-counted as independent evidence.
  - Whether `review_site`, `career_site`, and `forum` are being used in their intended roles.
- `structured_data`
  - Whether `fact_layer.official` is filled only from official information.
  - Whether `fact_layer.unofficial` overwrites official values.
  - Whether monthly vs annual pay, annual holidays vs paid leave, and average overtime vs fixed overtime are being confused.
- `section_boundary`
  - Whether the boundaries between `phd_value`, `role_fit`, and `rd_env` are collapsing.
- `score_consistency`
  - Whether `facts_official`, `facts_unofficial`, `evaluation`, and final `score` are consistent.
  - Whether the final judgment is explainable after taking unofficial evidence into account.
- `summary_consistency`
  - Whether `summary` is consistent with the section-level judgments.
- `render_consistency`
  - Whether the analysis YAML and rendered Markdown match.
  - Whether the renderer caused missing headings or rendering problems.
- `residual_uncertainty`
  - Whether uncertainty and scope ambiguity are preserved appropriately.

### Heuristics
- `source_quality`
  - Do not let a single unofficial lineage overturn official information. The “two independent unofficial lineages” rule mainly matters when overturning a conclusion. Keeping a single weak unofficial lineage as tentative evidence is still allowed.
  - Do not make the description so short that it loses information needed for comparison or re-judgment. If non-duplicative supporting information exists but was cut too aggressively, treat that as information loss.
- `summary_consistency`
  - `summary` should be a summary, not a section-by-section restatement. Check whether it stays concise while preserving the key points.

## Review return schema
- Review output must be a single YAML object only.
- Use exactly this format:

```text
review.verdict: pass | revise
review.findings: list[review_finding]
review.passed_checks: list[str]

review_finding.severity: high | medium | low
review_finding.category: scope_integrity | source_separation | source_quality | structured_data | section_boundary | score_consistency | summary_consistency | render_consistency | residual_uncertainty
review_finding.section: scope | fact_layer | phd_value | role_fit | rd_env | compensation | hiring_process | stability | summary | sources | rendered_output
review_finding.message: str
review_finding.suggested_fix: str
```

# Uncertainty workflow
- For uncertainty checks, launch at least three independent child agents on the same fixed scope.
- Give each child a different `slug`.
- Unless the comparison itself is the goal, do not let children read existing reports, comparison reviews, past uncertainty results, or other agent outputs.
- Run validator checks on each YAML.
- The parent aggregates ranges, means, medians, and standard deviations for total evaluations and section scores.
- Do not confuse `evaluation-target mismatch` with `scoring variance`.

# Failure handling
- The parent decides whether the child mixed commentary outside YAML or returned only partial YAML.
- If the child mixed commentary outside YAML, tell it explicitly and require a re-output.
- If the child returned partial YAML, list the missing top-level keys and require a re-output.
- If the child created, modified, or saved artifacts on its own, treat those files as unauthorized outputs. Do not treat them as final artifacts; remove or quarantine them as needed, and continue from the YAML returned in the message.
- If validator mismatches exist, do not silently patch them in the parent; return the schema violations and require correction.
- If the review child returns invalid review YAML, list the schema violations and require a re-output from the review child.
- If the review verdict is `revise`, return the findings to the analysis child and require a full corrected YAML re-output.
- The parent may still fix clearly mechanical issues such as save-name mistakes or temporary-file naming, as long as the content judgment is unaffected.

# Output expectations
- The parent agent should leave behind both YAML and Markdown artifacts.
- If both `research` and `swe` are fixed, leave one independent YAML / Markdown pair for each target.
- Name targets deterministically and keep `slug` aligned with saved filenames.
- Default to concise target-based names without dates. Example: `ntt_data_research`, `ntt_data_swe`.
- Add dates only when they are needed for disambiguation or explicit preservation of multiple runs.
- If cross-target comparison is needed, the parent should create a separate comparison note or review artifact.
- The parent decides save paths, naming, and test-vs-production separation.
- If needed, the parent should also save uncertainty reviews or comparison reviews in an appropriate place.
