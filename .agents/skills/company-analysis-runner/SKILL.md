---
name: company-analysis-runner
description: 固定した採用対象について `company-analysis` 評価子を起動し、fact_layer とセクションスコアを含む YAML の検証、ファイル経由 review、レンダリング、保存を統括する親エージェント用 skill。
---

# Company Analysis Runner

## 目的

- 親エージェントが企業分析を最初から最後まで統括するときに使う。
- 調査とセクション採点は、必ず `company-analysis` skill を使う分析子へ委譲する。
- 親は、対象 scope 固定、分析子起動、YAML 検証、必須 review、Markdown rendering、保存、最終報告を担当する。
- 分析子と review 子の受け渡しは、通常は `tmp/company_analysis/` 配下のファイルを正本にする。chat inline payload は fallback に限る。
- 親は分析本文を書かず、判断内容に影響しない機械的問題だけを直してよい。

## 参照

- **対象 scope 固定**: `references/target_scope.md`
  - 会社実体、子会社、応募単位、`role_family`、応募 route、slug、並列対象の固定規則。
  - 会社名だけ、複数会社、応募 route や `role_family` が曖昧な場合は必ず読む。
- **受理 pipeline**: `references/acceptance_pipeline.md`
  - `run_metadata`、validator、必須 review、rendering、失敗時対応、不確実性確認、出力規約。
  - 子 YAML を受け取る前に読む。
- **分析子 prompt**: `subagent_prompt_template.txt`
  - 分析子へ渡す prompt template。placeholder だけを埋める。
- **review 子 prompt**: `review_prompt_template.txt`
  - review 子へ渡す prompt template。通常は review input bundle の path を渡す。
- **review skill**: `company-analysis-review`
  - review schema と詳細な review 観点の権威。runner 側で schema を再定義しない。

## 実行 default

- 分析子と review 子の default model は `gpt-5.4-mini`、`reasoning_effort` は `medium`。
- 公開情報が極端に曖昧、review で再実行が必要、または推論の弱さが明確な場合だけ、大きい model または高い `reasoning_effort` に上げる。
- 多数の会社または対象がある場合、一括起動ではなく上限付き並列と補充キューを使う。
- 固定済み対象が複数ある場合、review 子は原則として 1 run につき 1 つだけ起動し、対象ごとに review input bundle を渡して再利用する。
- review 子を増やしてよいのは、既存 review 子が壊れた、対象外の状態を保持して reset できない、重大な遅延で親 run が止まる、または render-focused review と内容 review を分離する必要がある場合に限る。
- 分析子の出力が 1 件完了したら、その都度 YAML intake、validation、必須 review まで進める。バッチ全体の完了を待たない。
- review 子が未起動で空き枠もない場合、新しい分析子を起動せず、先に完了済み YAML の検証と必須 review を処理する。
- review が `revise` の場合、同一成果物の修正・再 review は原則 1 回までとする。test run では用途に応じて medium 以下の `source_quality` finding を known issue として扱える。

## 固定入力

分析子を起動する前に、対象ごとに少なくとも次を固定する。

- `company_name`
- `survey_date`
- `slug`
- `scope.user_label`
- `scope.target_application_unit`
- `scope.hiring_entity_name`
- `scope.role_family`: `researcher`, `research_engineer`, `engineer`, `consultant`, `generalist`, `other` のいずれか。採用年度、卒業年度、雇用区分を入れない。
- `scope.alternative_application_units`: 同じ `hiring_entity_name` 配下の他の採用 route、職種 track、応募単位。
- `scope.stability_entity_name`

`scope.role_family` は職種ファミリーだけを表す。応募単位、採用 route、採用年度、卒業年度、雇用区分、cohort を入れない。

## Workflow

### 対象 Scope 固定

- `references/target_scope.md` に沿って、会社実体、応募単位、`role_family`、安定性を見る entity、slug を固定する。
- ユーザーが会社名だけを与えた場合でも、全社評価に広げず、実際の応募単位に近い `target_application_unit` を固定する。
- 独立採用する近接法人が複数ある場合は、候補と採用状況を要約し、主分析対象をユーザーに選ばせる。
- 複数の `role_family` または応募 route を分析する場合は、別々の `target_application_unit`、別 slug、別分析子として扱う。

### Scope Manifest 保存

- 複数の固定済み対象を分析する場合、分析子を起動する前に全対象の scope manifest Markdown を保存する。
- 保存先は `document/<run_slug>_target_scope.md` を default とする。test run の manifest を `report/company_analysis/` に置かない。
- manifest には少なくとも次の列を含める。
  - `status`
  - `slug`
  - `company_name`
  - `target_application_unit`
  - `hiring_entity_name`
  - `role_family`
  - `stability_entity_name`
  - `ambiguity_note`
- `status` は `ready_for_analysis`、`needs_scope_check`、`not_application_unit` のいずれかにする。
- `target_application_unit` と `hiring_entity_name` は空欄にしない。ここが未固定の対象は分析子を起動せず、`needs_scope_check` として manifest に残す。
- manifest 保存後、ユーザーが明示的に「続けてよい」と言っている場合だけ分析子起動へ進む。すでに実行許可がある場合でも、manifest path を短く報告してから進む。

### 分析子起動

- 固定済み対象ごとに `company-analysis` 分析子を 1 つ起動する。
- 各分析子に `tmp/company_analysis/subagent_outputs/<run_slug>/<uuid>.yaml` 形式の handoff path を 1 つ割り当てる。中間成果物のファイル名は UUID にし、slug は YAML 内部と最終成果物名に残す。
- `subagent_prompt_template.txt` の `{{...}}` placeholder だけを埋め、本文の言い換え、並べ替え、削除、場当たり的な追記をしない。
- run ごとに template を場当たり的に書き換えない。prompt 変更が必要なら template file 自体を編集する。
- 各分析子には自身の固定 scope だけを渡す。同じ会社の別 track 情報を比較メモとして混ぜない。
- 分析子には、単一の完全な YAML オブジェクトだけをメッセージで返し、同じ YAML を handoff path に保存するよう求める。handoff file が正本であり、親は file が存在しない限り完了扱いにしない。
- 分析子には、handoff path 以外のファイル作成、更新、保存、Markdown rendering をさせない。
- 必要に応じて、既存レポート、比較レビュー、他エージェント出力を読まないよう明示する。

### 受理 Pipeline

- 分析子が YAML を返したら、他の子の完了を待たずに handoff file または message YAML を `references/acceptance_pipeline.md` に沿って処理する。
- `scope_check.verdict: revise_scope` が返った場合は final artifact として受け入れず、親が scope を修正してから再実行する。
  - 通常 YAML 作成前に止まった場合は、原則として同じ分析子へ修正後 scope を渡して再実行する。
  - すでに広い scope で調査を進めた後、または対象職種・採用実体が大きく変わる場合だけ、新しい分析子を起動する。
- final として受け入れる前に `run_metadata` を追加する。
- `python3 tool/check_company_analysis_yaml.py <yaml-file>` で検証する。
- validator failure、部分 YAML、YAML 外説明、unauthorized output は、`references/acceptance_pipeline.md` の失敗時対応に従う。

### Review Pipeline

- review は全 final artifact で必須とする。validator を通過した YAML は、他の分析子の完了を待たず、rendering 前に必ず review 子へ渡す。
- `python3 .agents/skills/company-analysis-runner/tool/prepare_review_input.py --run-slug <run_slug> <working-yaml>` で review input bundle を作る。
- `review_prompt_template.txt` には review input bundle path だけを埋める。analysis YAML や rendered Markdown の本文は通常 inline で渡さない。
- review 子は `company-analysis-review` skill を使い、bundle に書かれた path と、指示準拠確認に必要な skill 文書だけを読む。
- 同じ親 run 内では、明確に reset が必要でない限り、1 つの共有 review 子を再利用する。対象ごとに新しい review 子を立てない。
- review YAML は bundle の `review_output_path` に保存させ、`python3 tool/check_company_analysis_review.py <review-yaml>` で検証する。
- verdict が `revise` の場合、finding を分析子へ戻し、完全な修正版 YAML 再出力を求める。

### Rendering と保存

- YAML が受理されたら、`python3 tool/render_company_analysis_md.py <yaml-file>` で Markdown を生成する。
- rendering-level の不整合を疑う場合は、内容 review とは別に render-focused review を行う。
- 親は YAML と Markdown の両方を残す。
- accepted YAML は `report/company_analysis/data/`、accepted Markdown は `report/company_analysis/companies/`、accepted review artifact は `report/company_analysis/reviews/` を default とする。
- scope manifest、比較メモ、test/run note、workflow consideration は `document/` に保存する。
- 中間 handoff、working YAML、review input bundle、review output draft は `tmp/company_analysis/` に保存する。
- 複数の `scope.target_application_unit` を固定した場合、`scope.target_application_unit` ごとに独立した YAML / Markdown pair を残す。
- 最終回答では保存した YAML と Markdown を示す。review 成果物を生成した場合はそれも示す。
