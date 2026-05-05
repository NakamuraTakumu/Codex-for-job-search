---
name: company-analysis-review
description: 固定スコープに対して company-analysis YAML を確認し、review input bundle と参照先ファイルから、固定 schema の review YAML だけを返すレビュー子用 skill。
---

# 目的
- `company-analysis-child-orchestrator` から起動されるレビュー子で使う。
- 対象は、review prompt で指定された review input bundle と、bundle 内の `analysis_yaml_path`、必要時の `rendered_markdown_path`。
- reviewer は分析自体を書き換えない。review YAML だけを返す。
- filesystem handoff を通常経路とし、inline payload は filesystem handoff が使えない場合の fallback とする。

# 入力
- review input bundle path
- review input bundle に書かれた固定 scope、target context、handoff observations、analysis YAML path、必要時のみ rendered Markdown path、review output path、Reference Paths
- filesystem handoff が使えない場合だけ、review prompt 内の inline payload を fallback として使う。
- 同じ reviewer 子を複数対象で再利用する場合でも、各 prompt は自己完結しているものとして扱う。
- `role_family` は職種ファミリーであり、応募単位、採用 route、採用年度、卒業年度、雇用区分、cohort ではないものとして読む。

# 読み取り境界
- 通常は review input bundle、bundle の `analysis_yaml_path`、bundle の `Reference Paths` だけを読む。
- `rendered_markdown_path` が `null` でない場合だけ rendered Markdown を読む。
- inline fallback では、review prompt が明示した payload と path だけを読む。
- 既存企業レポート、過去分析、比較レビュー、他 reviewer 結果は、bundle に明示されていない限り読まない。

# 出力契約
- 単一の YAML オブジェクトだけを返す。
- Markdown fence や説明コメントを混ぜない。
- filesystem handoff の場合は、同じ YAML を bundle の `review_output_path` に保存する。
- inline fallback の場合は、review prompt が明示した保存先がない限りファイル保存しない。
- `review.verdict: revise` の場合は `review.findings` を 1 件以上含める。`pass` の場合は `review.findings: []` とする。
- `review.verdict: pass` の場合、`review.passed_checks` は 1 件以上にする。`revise` の場合も確認済み項目があれば入れてよい。
- `review.verdict: pass` の場合、`review.passed_checks` には少なくとも `instruction_compliance` と `scope_integrity` を含める。
- `review.verdict: pass` の場合、`review.pass_rationale` は修正不要と判断した短い根拠を書く。
- `review.residual_risks` は、修正要求ではないが後で監査・production 昇格判断に使う留保を list で残す。なければ `[]` とする。
- schema は必ず次に合わせる。

```text
top-level key: review

review.verdict: pass | revise
review.findings: list[review_finding]
review.passed_checks: list[str]
review.pass_rationale: str | null
review.residual_risks: list[str]

review_finding.severity: high | medium | low
review_finding.category: instruction_compliance | scope_integrity | source_separation | source_quality | structured_data | section_boundary | score_consistency | summary_consistency | render_consistency | residual_uncertainty
review_finding.section: metadata | scope | fact_layer | phd_value | role_fit | rd_env | compensation | hiring_process | stability | summary | sources | rendered_output
review_finding.message: str
review_finding.suggested_fix: str
```

# レビュー範囲
- `instruction_compliance`
  - analysis YAML が `.agents/skills/company-analysis/SKILL.md` の指示に反していないか。
  - `analysis_yaml_path` が子オーケストラの追加した `run_metadata` を含む working YAML の場合、その存在だけを `company-analysis` 孫調査エージェントの返却 YAML 違反として扱わない。孫調査エージェントの返却 payload 自体に `run_metadata` が混入した証拠がある場合だけ指摘する。
  - bundle の `Handoff Observations` にある `expected_handoff_path` だけを、孫調査エージェントが保存してよい handoff path として扱う。
  - `handoff_match` が `matched` 以外の場合、handoff file と message YAML の不一致、欠落、または fallback の影響を確認する。
  - `unauthorized_outputs` が `none_observed` 以外の場合、孫調査エージェントが子オーケストラ指定 handoff path 以外でファイル作成、更新、保存を行ったものとして指摘する。
  - `unexpected_rendering` が `none_observed` 以外の場合、孫調査エージェントが Markdown rendering を行ったものとして指摘する。
  - `child_run_metadata_present` が `true` の場合、孫調査エージェントの返却 YAML に `run_metadata` が混入したものとして指摘する。
  - reviewer 自身が bundle の `review_output_path` 以外へ review 成果物を保存していないか。
  - オーケストラ固定の `scope` を維持し、公開情報が薄いことを理由に近接職種へ置き換えていないか。
  - 会社プロフィールや全社評価へ広げず、固定された `target_application_unit` を「働く場」として評価しているか。
  - 公式 / 非公式の証拠分離、重要欠損時の追加調査、非公式情報の調査、事実と評価の分離を守っているか。
  - 公式 source 由来の候補値を、年度差、近接職種、共通制度、採用主体差、適用不確実性を理由に `fact_layer.official` から落としていないか。
  - 公式 source に候補値がなく、自己計算または根拠なし推定しかできない論点を、`fact_layer.official` ではなく留保付き評価として扱っているか。
  - ローカル既存成果物、過去分析、他 agent output を根拠として使っていないか。
- `scope_integrity`
  - top-level metadata の `company_name`、`survey_date`、`slug`、`applicant_graduation_cohort` が fixed input と一致しているか。metadata の不整合は `section: metadata` を使う。
  - `target_application_unit`、`hiring_entity_name`、`role_family`、`alternative_application_units`、`workplace_entity_name` が fixed input の scope と一致しているか。
  - `role_family` が `researcher`、`research_engineer`、`engineer`、`consultant`、`generalist`、`other` のいずれかで、応募単位や cohort と混同されていないか。
  - `role_family` が `target_application_unit` と意味的に整合しているか。
  - 複数の `target_application_unit` の情報が 1 つの analysis YAML に混ざっていないか。
  - 固定 scope が、prompt に明示されたユーザー意図や `scope_rationale` と意味的に整合しているか。
  - ユーザーが研究職・Research・研究所を求めているのに、明示的な承認なしに SWE、コンサル職、広い技術職へ置き換わっていないか。
  - 近接職種が別対象ではなく研究系 target の代替として扱われていないか。
- `source_separation`
  - 非公式情報が `facts_official` に混入していないか。
  - 公式情報が `facts_unofficial` に混入していないか。
  - `sources.tier` が実際の根拠 tier と一致しているか。
- `source_quality`
  - 公式 source は原則 4 件以上で、採用情報と会社情報または IR 情報を含むか。
  - 公式 source が 4 件未満、または `recruit` と `company|ir` の必須 kind を満たせない場合、追加調査後の不足原因が `summary.concerns` の `公式source不足:` で始まる項目に残っているか。
  - 非公式情報の扱いが `.agents/skills/company-analysis/SKILL.md` の **非公式情報** 節に従っているか。
  - 典型的な非公式 source family の検索結果または不発理由が `facts_unofficial` または `summary.concerns` から追えるか。
  - 親会社、グループ会社、採用実体の source が区別されているか。
  - `review_site`、`career_site`、`forum` が意図した使い方になっているか。
- `structured_data`
  - `company-analysis` の `references/output-contract.md` を正本として、必須 key、型、enum、欠損値、禁止形式に反していないか。
  - `version`、`scope`、`fact_layer.official`、`fact_layer.unofficial`、6 つの section が必須 key をすべて含むか。
  - 不明な構造化値に `null` を使い、`unknown`、日本語 placeholder、非公開 numeric value の `0` を使っていないか。
  - `fact_layer.official` が公式 source 由来の候補値だけで埋められているか。
  - `fact_layer.unofficial` が公式値を上書きしていないか。
  - `applicant_graduation_cohort` が応募者条件として扱われ、採用年度や `fact_layer` の年度フィルタとして扱われていないか。
  - `fact_layer` が調査時点で最も新しく、固定 scope に最も近い候補値を優先しているか。
  - cohort 向け情報が未公開の場合、直近年度の同一応募単位、同一採用主体、共通制度、または近接職種として扱える情報を探しているか。
  - `fact_layer.official` が、近接職種、年度差、共通制度、採用主体差、公式 source 上の推定値を含む候補値を不必要に落としていないか。
  - `fact_layer.unofficial` が、低信頼、近接職種、年度差、非公式 source 上の推定値を含む候補値を不必要に落としていないか。
  - `fact_layer` に source year、適用 cohort、scope distance などの年度メタデータを追加していないか。
  - 博士応募資格、博士向け導線、博士優位、学位差の解釈が `fact_layer` に boolean として追加されず、`phd_value` の文章で区別されているか。
  - 月給と年収、年間休日と有給、平均残業と固定残業が混同されていないか。
  - 見えている初任給候補があるのに、`starting_salary_yen` や `starting_salary_*_yen` が不要に空欄になっていないか。
  - `starting_salary_yen` / `starting_salary_*_yen` が年収ではなく月額初任給として扱われているか。
  - `new_graduate_turnover_rate_within_3_years_percent`、`average_tenure_years`、`average_age_years` が正本契約の意味に沿って扱われているか。
  - `remote_work_policy` が、一人の anecdote ではなく広い制度情報に基づいているか。
  - 公式 source に候補値がない欠損を、自己計算または根拠なし推定で `fact_layer.official` に埋めていないか。
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
- 非公式情報の扱いは `.agents/skills/company-analysis/SKILL.md` の **非公式情報** 節を正本として確認する。
- 比較や再判断に必要な情報が失われるほど説明を薄くしない。
- `summary` が各セクションの単なる繰り返しになっていないか確認する。
- reviewer は広範な再分析者ではない。validator だけでは拾いにくい高リスク領域を独立に確認する guardrail として振る舞う。

# Scope Intent Guardrail
- `user_requested_target` が `null` の場合、過去 turn や既存ファイルからユーザー意図を推測しない。その場合は、fixed input の scope と YAML 内部の整合性だけを見る。
- `user_requested_target` が明示されている場合、fixed input の scope はその対象と同じ応募単位、または明示的に承認された別対象でなければならない。
- 研究職・Research・研究所・R&D を求める `user_requested_target` に対して、fixed input の scope が SWE、コンサル職、generalist、または broad technical track へ変わっている場合は、原則として high severity の `scope_integrity` finding を返す。
- Data Scientist、AI/Data Research Scientist、Research Scientist などの data / AI 系名称は一律に scope mismatch としない。`company-analysis` の `references/scope-check.md` に照らし、公式に研究職または研究開発系 application unit として固定されている場合は `researcher` または `research_engineer` として扱う。
- 公式募集が薄い、当年採用が未定、または情報が少ないことは、近接職種への置換理由にしない。固定した研究系 target の不確実性として扱わせる。
- 近接職種を分析してよいのは、`scope_rationale` にユーザーの明示承認、比較目的、または別 target として追加した理由がある場合だけとする。
- scope intent mismatch がある場合、`suggested_fix` ではユーザー意図の target に戻すか、近接職種を別 `run_id`・別 artifact として分離するよう求める。

# Verdict の使い分け
- `pass`
  - 修正要求がない場合に使う。
  - `findings` は空にする。
  - `pass_rationale` に、scope、source、structured data、score/summary 整合のうち pass 判断を支える主要根拠を 1-3 文で書く。
  - `residual_risks` に、scope ambiguity、source weakness、production 昇格可否に関わる留保を残す。留保がなければ `[]` とする。
- `revise`
  - 1 件以上の修正要求がある場合に使う。
  - finding を 1 件以上含める。
  - `pass_rationale` は `null` とする。
  - `residual_risks` は修正要求とは別に残す留保を入れる。留保がなければ `[]` とする。

# ワークフロー
- review prompt が指定した review input bundle を読む。
- bundle の `Fixed Input`、`Target Context`、`Handoff Observations`、`Review Target Paths`、`Reference Paths` を確認する。
- bundle の `Instructions` は現在対象の追加制約として扱う。
- bundle に書かれた `analysis_yaml_path` の YAML を読む。
- bundle に書かれた `Reference Paths` は、指示、schema、scope、scoring への準拠確認のためだけに読む。特に `company-analysis` の `SKILL.md`、`references/output-contract.md`、`references/scope-check.md`、必要時の `references/scoring.md` を正本として扱う。
- `rendered_markdown_path` が `null` でない場合だけ rendered Markdown を読む。
- reviewer 子が再利用されている場合、過去の review state を捨て、現在の review input bundle と参照先 file だけで判断する。
- 必ず `instruction_compliance` を確認し、その後に他の必須チェックとヒューリスティックに沿って高リスク領域を確認する。
- 修正不要なら `pass` を返し、`passed_checks` を埋める。
- `pass` の場合でも、後から判断根拠を追えるよう `pass_rationale` と `residual_risks` を埋める。
- 修正が必要なら `revise` を返し、各 finding に `severity`、`category`、`section`、`message`、`suggested_fix` を入れる。
- finding の `category` は最も具体的なものを使う。`instruction_compliance` は `company-analysis` skill の指示違反そのものに使い、内容上の不整合には専用 category を優先する。
- filesystem handoff の場合は review YAML を bundle の `review_output_path` に保存する。
- 単一の review YAML オブジェクトだけを返す。

# 禁止事項
- analysis YAML を書き換えない。
- analysis YAML を再生成しない。
- 現在の review input bundle と、bundle が明示した `analysis_yaml_path` / `rendered_markdown_path` / `Reference Paths` 以外の既存企業レポート、比較レビュー、他 reviewer 結果を読まない。
- 現在 prompt または bundle に明示されていない限り、過去の slug、過去の payload、以前の turn と比較しない。
- review のために追加の web 調査をしない。
- inline fallback が使われる場合でも、delimiter 行を review content と解釈しない。
- 固定 scope を自分で変更しない。
- review YAML の外に説明を混ぜない。
- filesystem handoff では bundle の `review_output_path`、inline fallback では review prompt が明示した保存先以外に review 成果物を保存しない。
