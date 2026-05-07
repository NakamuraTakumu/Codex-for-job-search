---
name: recruitment-info-runner
description: 複数企業または company-analysis score 上位企業のインターン、選考、企業説明会・採用イベント情報を会社単位で集める親 runner skill。会社名と任意の cohort / 対象年度を target request に分け、固定 prompt template で recruitment-info-child-orchestrator 子を並列起動し、子に孫 research / review を管理させる依頼で使う。
---

# Recruitment Info Runner

## 目的

- 親エージェントは、ユーザー入力から recruitment info の target request を切り出し、会社ごとの child orchestrator を並列起動する。
- 親はインターン、選考、説明会の日程・締切・status を自分で調査または判断しない。
- 親は子プロンプトを自由記述で作らず、`child_orchestrator_prompt_template.txt` の placeholder だけを埋める。
- 親は子に `recruitment-info-child-orchestrator` を使わせ、調査と review はすべて孫 agent に委譲させる。
- 親は子の result status と保存済み YAML を読んで短く報告する。
- runner は aggregate artifact を作らない。
- Markdown summary はユーザーが明示的に求めた場合だけ作る。通常 run では data YAML と review YAML だけを正本 artifact にする。

## 入力契約

- target request は、最低限 `company_name` を持つ。
- 任意 field:
  - `applicant_graduation_cohort`
  - `target_year`
  - `output_root`
- 1 つの cohort、年度が複数会社に共通する場合、各 target request に同じ値を渡す。
- 職種、関心領域、company-analysis の応募単位は target request に含めない。採用情報は会社単位で収集し、職種や配属先は出力 item の事実 field として記録する。
- 会社名が不足している場合だけユーザーに確認する。
- 親は既存 report や web 調査で target request を補完しない。
- 親は既存 `report/recruitment-info/`、`document/recruitment_info_trial/`、`tmp/recruitment_info/` の調査済み YAML を target request の補完、baseline、品質判定に使わない。
- company-analysis report path を target request、子 prompt、孫 prompt に渡さない。
- ユーザーが「上位 score」「score 上位企業」などを指定した場合は、`tool/extract_top_score_targets.py` で `report/company_analysis/data/` から上位 target を作る。

## Score 上位抽出

- command:
  - `python3 .agents/skills/recruitment-info-runner/tool/extract_top_score_targets.py --profile phd --limit <n> --output <path>`
- score basis:
  - company-analysis site の博士卒用 score と同じく、各 section score を母集団内 z-score に変換してから博士卒向け weight を掛け、weighted z-score を 50±10 の 100 点 scale に正規化する。
  - 既定 weight は `phd_value: 0.30`、`role_fit: 0.10`、`rd_env: 0.05`、`compensation: 0.25`、`hiring_process: 0.10`、`stability: 0.20`。
  - 同一企業が複数 target を持つ場合は最高 normalized weighted score の target だけを残す。
- 出力された `company_name`、`target_id` を target request と保存 path 作成に使う。
- score 上位抽出は ranking と target 名作成のためだけに company-analysis YAML を読む。抽出元の report path を子または孫へ渡さない。

## 並列実行

- target request ごとに子を 1 体起動する。
- `spawn_agent.fork_context` は `false` にする。
- 子起動では `spawn_agent.model` を `gpt-5.4-mini`、`reasoning_effort` を `medium` に固定する。ユーザーが明示的に別 model を指定しない限り、`gpt-5.5` は使わない。
- 同時起動は最大 4 体にする。5 件以上は補充キューで処理する。
- 子 prompt は `child_orchestrator_prompt_template.txt` の placeholder だけを埋める。
- 子には調査本文、review 判断、fact 修正をさせない。
- 子には孫 research に指定した `output_yaml_path` だけを書かせ、孫 review に指定した `review_yaml_path` だけを書かせる。
- 子は review / revise を複数回実行してよいが、初回に起動した research 孫と review 孫を再利用させる。revise ごとに新しい孫を起動させない。
- 子の継続可否は `recruitment-info-child-orchestrator` の改善判定に従わせる。
- 子には full YAML artifact を chat に出させず、child result status だけを返させる。

## 子 Prompt Template

- 正本: `child_orchestrator_prompt_template.txt`
- placeholder:
  - `{{company_name}}`
  - `{{applicant_graduation_cohort}}`
  - `{{target_year}}`
  - `{{checked_date}}`
  - `{{output_root}}`
  - `{{output_yaml_path}}`
  - `{{review_yaml_path}}`
- 不明値は `null` として埋める。placeholder 行を削らない。
- template 本文を場当たり的に言い換えない。要件変更が必要な場合は template を更新してから使う。

## 保存契約

- `output_root` の既定値: `report/recruitment-info`
- 標準 directory:
  - data YAML: `<output_root>/data`
  - review YAML: `<output_root>/reviews`
  - optional Markdown summary: `<output_root>/companies`
- 子ごとの YAML 保存先:
  - `<output_root>/data/<target_id>.yaml`
- target_id は会社名、または score 上位抽出 script が返す `target_id` から `[a-z0-9_]+` に正規化した保存用 ID として作る。
- target_id は保存用 ID であり、採用対象の意味判断に使わない。
- 既存の `<output_root>/data/<target_id>.yaml` や review YAML は、新規調査の入力として読まない。存在しても baseline 比較や補完に使わない。
- runner は aggregate YAML を作らない。final response には各 target の data YAML path を含める。
- runner は summary、aggregate、統合 data を自動作成しない。ユーザーが summary を求めた場合も、保存済み YAML から導出した Markdown だけにする。
- 子が返した status の `output_yaml_path` を読み、保存済み YAML が invalid、Markdown、または説明混じりの場合は、同じ子に保存ファイルの再出力を求める。
- score 上位抽出などの一時ファイルだけは `tmp/recruitment_info/` に保存してよい。調査結果の正本は `report/recruitment-info/data/` に置く。

## Workflow

1. **target request 作成**:
   - チャット本文から会社名の list を作る。
   - 共通条件があれば各 target に転記する。
   - score 上位指定の場合は `tool/extract_top_score_targets.py` を使い、抽出根拠 YAML を保存する。
   - score 上位抽出結果の report path や company-analysis YAML 本文は子へ渡さない。
   - 既存 recruitment-info 出力から target、締切、route、event、internship を補完しない。
2. **子起動**:
   - 各 target について template を埋め、子を起動する。
   - 起動時の model は `gpt-5.4-mini`、reasoning effort は `medium` にする。
   - 子は `recruitment-info-child-orchestrator` skill を使う。
   - 子は調査と review を孫 agent に委譲し、自分では web 調査、採用判断、review 判断、YAML 本文作成を行わない。
   - 子は review が `revise` の場合、同じ research 孫と review 孫を使い回し、改善見込みがある間だけ research 再出力と再 review を繰り返し、改善が止まった場合は `review_revise` として終了する。
3. **保存結果確認**:
   - 子の保存 status を受け取る。
   - 子の `research_yaml_path` と `review_yaml_path` を読む。
   - 子の `review_rounds`、`revision_rounds`、`stop_reason` があれば報告に使う。
   - research YAML が invalid、Markdown、説明混じり、または主要 field 欠落の場合は、同じ子に孫 research への差し戻しを求める。
   - 親は子または孫の主張を新規 web 調査で上書きしない。明らかな形式欠落だけ補正依頼する。
4. **報告**:
   - 会社ごとの導出 ToDo、インターン、選考、説明会、未確認点を短くまとめる。
   - 詳細は保存済み data YAML を要約し、source URL と data YAML path を残す。

## 完了条件

- 起動したすべての子から結果を受け取っている。
- 各 target について、インターン、選考、説明会の確認済み情報または確認不能理由がある。
- 各 target の data YAML path が `report/recruitment-info/data/` に存在する。
- 各 accepted target について、review YAML path が `report/recruitment-info/reviews/` に存在する。
- aggregate YAML を作っていない。
- final response で、子プロンプト template を使ったこと、各 data YAML path、失敗または未完了 target があればその status を示す。
