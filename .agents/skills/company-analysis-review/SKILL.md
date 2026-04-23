---
name: company-analysis-review
description: Shared reviewer skill for checking company-analysis YAML against a fixed scope, using inline analysis YAML and optional rendered Markdown, and returning only review YAML in the fixed schema.
---

# Purpose
- Use this skill for the shared reviewer child launched from `company-analysis-runner`.
- The target is the `company-analysis` YAML embedded directly in the parent prompt, plus optionally rendered Markdown embedded in the same prompt.
- The reviewer must not rewrite the analysis itself; it returns only review YAML.
- The prompt assumes payload sections are embedded with delimiters such as `<<<BEGIN_...>>>` / `<<<END_...>>>`.

# Inputs
- Parent-fixed scope
- Analysis YAML embedded directly in the prompt
- Rendered Markdown embedded directly in the prompt when needed

# Output contract
- Return a single YAML object only.
- Do not mix in Markdown fences or any explanatory commentary.
- Use exactly this schema:

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

# Review scope
- `scope_integrity`
  - Whether `evaluation_target`, `hiring_entity`, `job_type`, `placement_candidates`, and `stability_entity` match the parent-fixed scope.
- `source_separation`
  - Whether unofficial information leaks into `facts_official`.
  - Whether official information leaks into `facts_unofficial`.
  - Whether `sources.tier` matches the actual evidence tier.
- `source_quality`
  - Whether official sources are sufficient.
  - Whether unofficial sources are dominating the judgment too strongly.
  - Whether unofficial evidence includes duplication or repost inflation.
  - Whether `review_site`, `career_site`, and `forum` are being used in the intended way.
- `structured_data`
  - Whether `fact_layer.official` is filled only from official information.
  - Whether `fact_layer.unofficial` overwrites official values.
  - Whether monthly vs annual pay, annual holidays vs paid leave, and average overtime vs fixed overtime are being confused.
- `section_boundary`
  - Whether boundaries such as `phd_value / role_fit / rd_env` are collapsing.
- `score_consistency`
  - Whether `facts_official`, `facts_unofficial`, `evaluation`, and final `score` are consistent.
- `summary_consistency`
  - Whether `summary` is consistent with the section-level judgments.
- `render_consistency`
  - Only check this when rendered Markdown is actually provided.
  - Whether the analysis YAML and rendered Markdown correspond to each other.
  - Whether the renderer dropped headings or content.
- `residual_uncertainty`
  - Whether uncertainty and scope ambiguity are preserved appropriately.

# Heuristics
- Do not let a single unofficial lineage overturn official information.
- If conflicting unofficial evidence is used strongly, check whether there are at least two independent unofficial lineages.
- Do not allow the description to become so thin that information needed for comparison or re-judgment is lost.
- Check whether `summary` becomes a mere repetition of the sections.
- The reviewer is not a broad re-analyst. It acts as a guardrail that independently checks high-risk areas which validator checks alone may miss.

# Verdict guidance
- `pass`
  - Use when there is no requested correction.
  - Keep `findings` empty.
- `revise`
  - Use when there is at least one requested correction.
  - Include one or more findings.

# Workflow
1. Check the parent-fixed scope.
2. Read the analysis YAML embedded directly in the prompt.
3. Read rendered Markdown only when render-level confirmation is needed and the Markdown is actually provided in the same prompt.
4. Treat `<<<BEGIN_...>>>` / `<<<END_...>>>` lines as delimiters only; review the payload, not the delimiter lines themselves.
5. Inspect high-risk areas according to the Required checks and Heuristics.
6. If no correction is needed, return `pass` and fill `passed_checks`.
7. If correction is needed, return `revise` and fill each finding with `severity`, `category`, `section`, `message`, and `suggested_fix`.
8. Return a single review YAML object only.

# Prohibitions
- Do not rewrite the analysis YAML.
- Do not regenerate the analysis YAML.
- Do not read existing company reports, comparison reviews, or other reviewer results outside the inline review target embedded in the current prompt.
- Do not interpret the embedded delimiter lines as review content.
- Do not change the fixed scope on your own.
- Do not mix any explanation outside the review YAML.
