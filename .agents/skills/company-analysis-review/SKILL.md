---
name: company-analysis-review
description: 固定スコープに対して company-analysis YAML を確認し、review input bundle と参照先ファイルから、固定 schema の review YAML だけを返す共有レビュー子用 skill。
---

# 目的
- `company-analysis-runner` から起動される共有レビュー子で使う。
- 対象は、親プロンプトで指定された review input bundle と、bundle 内の `analysis_yaml_path`、必要時の `rendered_markdown_path`。
- reviewer は分析自体を書き換えない。review YAML だけを返す。
- filesystem handoff を通常経路とし、inline payload は filesystem handoff が使えない場合の fallback とする。

# 入力
- review input bundle path
- review input bundle に書かれた固定 scope、親 context、analysis YAML path、必要時のみ rendered Markdown path、review output path
- filesystem handoff が使えない場合だけ、親 prompt 内の inline payload を fallback として使う。
- 同じ reviewer 子を複数対象で再利用する場合でも、各 prompt は自己完結しているものとして扱う。
- `role_family` は職種ファミリーであり、応募単位、採用 route、採用年度、卒業年度、雇用区分、cohort ではないものとして読む。

# 出力契約
- 単一の YAML オブジェクトだけを返す。
- Markdown fence や説明コメントを混ぜない。
- filesystem handoff の場合は、同じ YAML を bundle の `review_output_path` に保存する。
- inline fallback の場合は、親が明示した保存先がない限りファイル保存しない。
- `review.verdict: revise` の場合は `review.findings` を 1 件以上含める。`pass` の場合は `review.findings: []` とする。
- `review.verdict: pass` の場合、`review.passed_checks` は 1 件以上にする。`revise` の場合も確認済み項目があれば入れてよい。
- schema は必ず次に合わせる。

```text
review.verdict: pass | revise
review.findings: list[review_finding]
review.passed_checks: list[str]

review_finding.severity: high | medium | low
review_finding.category: instruction_compliance | scope_integrity | source_separation | source_quality | structured_data | section_boundary | score_consistency | summary_consistency | render_consistency | residual_uncertainty
review_finding.section: scope | fact_layer | phd_value | role_fit | rd_env | compensation | hiring_process | stability | summary | sources | rendered_output
review_finding.message: str
review_finding.suggested_fix: str
```

# レビュー範囲
- `instruction_compliance`
  - analysis YAML が `.agents/skills/company-analysis/SKILL.md` の指示に反していないか。
  - 子が親指定 handoff path 以外でファイル作成、更新、保存、Markdown rendering を行っていないか。
  - reviewer 自身が bundle の `review_output_path` 以外へ review 成果物を保存していないか。
  - 親固定の `scope` を維持し、公開情報が薄いことを理由に近接職種へ置き換えていないか。
  - 会社プロフィールや全社評価へ広げず、固定された `target_application_unit` を「働く場」として評価しているか。
  - 公式 / 非公式の証拠分離、重要欠損時の追加調査、非公式情報の調査、事実と評価の分離を守っているか。
  - 公式・非公式とも直接情報がない論点の推定を、確認済み facts ではなく留保付き評価として扱っているか。
  - ローカル既存成果物、過去分析、他 agent output を根拠として使っていないか。
- `scope_integrity`
  - `target_application_unit`、`hiring_entity_name`、`role_family`、`alternative_application_units`、`stability_entity_name` が親固定スコープと一致しているか。
  - `role_family` が `researcher`、`research_engineer`、`engineer`、`consultant`、`generalist`、`other` のいずれかで、応募単位や cohort と混同されていないか。
  - `role_family` が `target_application_unit` と意味的に整合しているか。
  - 複数の `target_application_unit` の情報が 1 つの analysis YAML に混ざっていないか。
  - 固定 scope が、prompt に明示されたユーザー意図や親の対象固定理由と意味的に整合しているか。
  - ユーザーが研究職・Research・研究所を求めているのに、明示的な承認なしにデータサイエンス職、SWE、コンサル職、広い技術職へ置き換わっていないか。
  - 近接職種が別対象ではなく研究系 target の代替として扱われていないか。
- `source_separation`
  - 非公式情報が `facts_official` に混入していないか。
  - 公式情報が `facts_unofficial` に混入していないか。
  - `sources.tier` が実際の根拠 tier と一致しているか。
- `source_quality`
  - 公式 source が十分か。
  - 非公式 source が判断を過度に支配していないか。
  - 非公式根拠に重複や転載による水増しがないか。
  - 親会社、グループ会社、採用実体の source が区別されているか。
  - `review_site`、`career_site`、`forum` が意図した使い方になっているか。
- `structured_data`
  - `fact_layer.official` が公式情報だけで埋められているか。
  - `fact_layer.unofficial` が公式値を上書きしていないか。
  - 博士応募資格、博士向け導線、博士優位、学位差の解釈が `fact_layer` に boolean として追加されず、`phd_value` の文章で区別されているか。
  - 月給と年収、年間休日と有給、平均残業と固定残業が混同されていないか。
  - 見えている初任給候補があるのに、`starting_salary_yen` や `starting_salary_*_yen` が不要に空欄になっていないか。
  - `starting_salary_yen` / `starting_salary_*_yen` が年収ではなく月額初任給として扱われているか。
  - `remote_work_policy` が、一人の anecdote ではなく広い制度情報に基づいているか。
  - 公式・非公式とも直接情報がない欠損を、推定値で `fact_layer` に埋めていないか。
- `section_boundary`
  - `phd_value / role_fit / rd_env` などの境界が崩れていないか。
- `score_consistency`
  - `facts_official`、`facts_unofficial`、`evaluation`、最終 `score` が整合しているか。
- `summary_consistency`
  - `summary` がセクション別判断と整合しているか。
- `render_consistency`
  - rendered Markdown が実際に提供されている場合だけ確認する。
  - analysis YAML と rendered Markdown が対応しているか。
  - renderer が heading や内容を落としていないか。
- `residual_uncertainty`
  - 不確実性やスコープ曖昧性が適切に残されているか。

# ヒューリスティック
- 単一の非公式 lineage だけで公式情報を覆さない。
- 矛盾する非公式根拠を強く使う場合、少なくとも 2 つの独立非公式 lineage があるか確認する。
- 転載、ミラー、同一サービスの別表示、同じ求人票の重複ページは 1 lineage として扱う。
- 比較や再判断に必要な情報が失われるほど説明を薄くしない。
- `summary` が各セクションの単なる繰り返しになっていないか確認する。
- reviewer は広範な再分析者ではない。validator だけでは拾いにくい高リスク領域を独立に確認する guardrail として振る舞う。

# Scope Intent Guardrail
- `user_requested_target` が `null` の場合、過去 turn や既存ファイルからユーザー意図を推測しない。その場合は、親固定 scope と YAML 内部の整合性だけを見る。
- `user_requested_target` が明示されている場合、親固定 scope はその対象と同じ応募単位、または明示的に承認された別対象でなければならない。
- 研究職・Research・研究所・R&D を求める `user_requested_target` に対して、親固定 scope がデータサイエンス職、SWE、コンサル職、generalist、または broad technical track へ変わっている場合は、原則として high severity の `scope_integrity` finding を返す。
- 公式募集が薄い、当年採用が未定、または情報が少ないことは、近接職種への置換理由にしない。固定した研究系 target の不確実性として扱わせる。
- 近接職種を分析してよいのは、`parent_scope_rationale` にユーザーの明示承認、比較目的、または別 target として追加した理由がある場合だけとする。
- scope intent mismatch がある場合、`suggested_fix` ではユーザー意図の target に戻すか、近接職種を別 slug・別 artifact として分離するよう求める。

# Verdict の使い分け
- `pass`
  - 修正要求がない場合に使う。
  - `findings` は空にする。
- `revise`
  - 1 件以上の修正要求がある場合に使う。
  - finding を 1 件以上含める。

# ワークフロー
- 親が指定した review input bundle を読む。
- bundle の `Fixed Scope`、`Parent Context`、`Review Target Paths`、`Reference Paths` を確認する。
- bundle に書かれた `analysis_yaml_path` の YAML を読む。
- bundle に書かれた `Reference Paths` は、指示準拠確認のためだけに読む。
- `rendered_markdown_path` が `null` でない場合だけ rendered Markdown を読む。
- reviewer 子が再利用されている場合、過去の review state を捨て、現在の review input bundle と参照先 file だけで判断する。
- 必ず `instruction_compliance` を確認し、その後に他の必須チェックとヒューリスティックに沿って高リスク領域を確認する。
- 修正不要なら `pass` を返し、`passed_checks` を埋める。
- 修正が必要なら `revise` を返し、各 finding に `severity`、`category`、`section`、`message`、`suggested_fix` を入れる。
- finding の `category` は最も具体的なものを使う。`instruction_compliance` は `company-analysis` skill の指示違反そのものに使い、内容上の不整合には専用 category を優先する。
- filesystem handoff の場合は review YAML を bundle の `review_output_path` に保存する。
- 単一の review YAML オブジェクトだけを返す。

# 禁止事項
- analysis YAML を書き換えない。
- analysis YAML を再生成しない。
- 現在の review input bundle と、bundle が明示した `analysis_yaml_path` / `rendered_markdown_path` / `Reference Paths` 以外の既存企業レポート、比較レビュー、他 reviewer 結果を読まない。
- 現在 prompt または bundle に明示されていない限り、過去の slug、過去の payload、以前の turn と比較しない。
- inline fallback が使われる場合でも、delimiter 行を review content と解釈しない。
- 固定 scope を自分で変更しない。
- review YAML の外に説明を混ぜない。
- filesystem handoff では bundle の `review_output_path`、inline fallback では親が明示した保存先以外に review 成果物を保存しない。
