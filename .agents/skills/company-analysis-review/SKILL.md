---
name: company-analysis-review
description: 企業分析 YAML を固定スコープに照らしてレビューする共通 reviewer 子エージェント用 skill。親から直接渡された analysis YAML データと必要なら描画済み Markdown データを読み、内容は修正せず、固定 schema の review YAML のみを返す。
---

# Purpose
- この skill は `company-analysis-runner` から起動される共通 reviewer 子のために使う
- 対象は親から prompt 内で直接渡された `company-analysis` の analysis YAML と、必要なら補助的に渡される render 済み Markdown である
- reviewer は analysis 本体を書き換えず、review YAML だけを返す
- prompt 内では `<<<BEGIN_...>>>` / `<<<END_...>>>` の delimiter で review 対象が埋め込まれる前提とする

# Inputs
- 親が固定した scope
- prompt に直接埋め込まれた review 対象の analysis YAML
- 必要なら prompt に直接埋め込まれた render 済み Markdown

# Output contract
- 返却は単一の YAML オブジェクトのみ
- markdown fence や補足説明を混ぜない
- 形式は次に固定する

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
  - `evaluation_target`, `hiring_entity`, `job_type`, `placement_candidates`, `stability_entity` が親の fixed scope と整合しているか
- `source_separation`
  - `facts_official` と `facts_unofficial` が混ざっていないか
  - `sources.tier` が実際の根拠種別と一致しているか
- `source_quality`
  - 公式ソースが十分か
  - 非公式ソースが過剰に評価を支配していないか
  - 非公式の重複や転載水増しがないか
  - `review_site`, `career_site`, `forum` の用途が崩れていないか
- `structured_data`
  - `fact_layer.official` が公式情報だけで埋まっているか
  - `fact_layer.unofficial` が公式値を上書きしていないか
  - 月額/年額、年間休日/有給、平均残業/固定残業の取り違えがないか
- `section_boundary`
  - `phd_value / role_fit / rd_env` などの境界が崩れていないか
- `score_consistency`
  - `facts_official` / `facts_unofficial` / `evaluation` と最終 `score` が整合しているか
- `summary_consistency`
  - `summary` と各 section の判断が矛盾していないか
- `render_consistency`
  - render 済み Markdown が渡されたときだけ見る
  - analysis YAML と render 済み Markdown の対応が崩れていないか
  - renderer で見出しや内容が欠落していないか
- `residual_uncertainty`
  - 不確実性や scope ambiguity が適切に残されているか

# Heuristics
- 単発の非公式根拠だけで公式情報を覆していないか
- 公式と食い違う非公式を強く使うなら、独立した非公式 2 系列があるか
- 記述量が薄すぎて、比較や再判断に必要な補助情報を落としていないか
- summary が各 section の単なる繰り返しになっていないか
- reviewer は broad な再分析者ではなく、validator では拾いにくい高リスク箇所を独立確認する guardrail として振る舞う

# Verdict guidance
- `pass`
  - 修正要求がないとき
  - `findings` は空にする
- `revise`
  - 修正要求が 1 件でもあるとき
  - `findings` を 1 件以上入れる

# Workflow
1. 親が固定した scope を確認する
2. prompt に直接埋め込まれた analysis YAML を読む
3. render-level の確認が必要なときだけ、同じ prompt に埋め込まれた render 済み Markdown も読む
4. `<<<BEGIN_...>>>` / `<<<END_...>>>` delimiter 自体は review 対象に含めず、payload だけを読む
5. Required checks と Heuristics に沿って高リスク箇所を点検する
6. 修正要求がなければ `pass` とし、`passed_checks` を書く
7. 修正要求があれば `revise` とし、各 finding に `severity`, `category`, `section`, `message`, `suggested_fix` を入れる
8. 単一の review YAML オブジェクトだけを返す

# Prohibitions
- analysis YAML を書き換えない
- analysis YAML を再生成しない
- 今回 prompt に埋め込まれた review 対象以外の既存会社レポート、比較レビュー、他 reviewer 結果を読まない
- prompt に埋め込まれた delimiter 行そのものを内容として解釈しない
- fixed scope を独断で変更しない
- review YAML 以外の説明を混ぜない
