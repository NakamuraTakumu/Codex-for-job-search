---
name: company-analysis-runner
description: 固定した採用対象について `company-analysis` 評価子を起動し、fact_layer とセクションスコアを含む YAML の検証、レンダリング、必要時の軽量レビューを統括する親エージェント用 skill。
---

# Company Analysis Runner

## 目的

- 親エージェントが企業分析を最初から最後まで統括するときに使う。
- 調査とセクション採点は、必ず `company-analysis` skill を使う分析子へ委譲する。
- 親は、対象 scope 固定、分析子起動、YAML 検証、必要時の review、Markdown rendering、保存、最終報告を担当する。
- 親は分析本文を書かず、判断内容に影響しない機械的問題だけを直してよい。

## 参照

- **対象 scope 固定**: `references/target_scope.md`
  - 会社実体、子会社、応募単位、`role_family`、応募 route、slug、並列対象の固定規則。
  - 会社名だけ、複数会社、応募 route や `role_family` が曖昧な場合は必ず読む。
- **受理 pipeline**: `references/acceptance_pipeline.md`
  - `run_metadata`、validator、review trigger、rendering、失敗時対応、不確実性確認、出力規約。
  - 子 YAML を受け取る前に読む。
- **分析子 prompt**: `subagent_prompt_template.txt`
  - 分析子へ渡す prompt template。placeholder だけを埋める。
- **review 子 prompt**: `review_prompt_template.txt`
  - review 子へ渡す prompt template。analysis YAML と必要時の rendered Markdown は inline で埋める。
- **review skill**: `company-analysis-review`
  - review schema と詳細な review 観点の権威。runner 側で schema を再定義しない。

## 実行 default

- 分析子と review 子の default model は `gpt-5.4-mini`、`reasoning_effort` は `medium`。
- 公開情報が極端に曖昧、review で再実行が必要、または推論の弱さが明確な場合だけ、大きい model または高い `reasoning_effort` に上げる。
- 多数の会社または対象がある場合、一括起動ではなく上限付き並列と補充キューを使う。
- 固定済み対象が複数ある場合、共有 review 子または review 用空き枠を常に 1 つ確保する。
- review 子が未起動で空き枠もない場合、新しい分析子を起動せず、先に完了済み YAML の検証と review 要否判定を処理する。

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

### 1. 対象 scope 固定

1. `references/target_scope.md` に沿って、会社実体、応募単位、`role_family`、安定性を見る entity、slug を固定する。
2. ユーザーが会社名だけを与えた場合でも、全社評価に広げず、実際の応募単位に近い `target_application_unit` を固定する。
3. 独立採用する近接法人が複数ある場合は、候補と採用状況を要約し、主分析対象をユーザーに選ばせる。
4. 複数の `role_family` または応募 route を分析する場合は、別々の `target_application_unit`、別 slug、別分析子として扱う。

### 2. 分析子起動

1. 固定済み対象ごとに `company-analysis` 分析子を 1 つ起動する。
2. ファイル名や review payload の詳細で分析子起動を遅らせない。
3. `subagent_prompt_template.txt` の `{{...}}` placeholder だけを埋め、本文の言い換え、並べ替え、削除、場当たり的な追記をしない。
4. run ごとに template を場当たり的に書き換えない。prompt 変更が必要なら template file 自体を編集する。
5. 各分析子には自身の固定 scope だけを渡す。同じ会社の別 track 情報を比較メモとして混ぜない。
6. 分析子には、単一の完全な YAML オブジェクトだけを返すよう求める。
7. 分析子には、ファイル作成、更新、保存、Markdown rendering をさせない。
8. 必要に応じて、既存レポート、比較レビュー、他エージェント出力を読まないよう明示する。

### 3. 受理 pipeline

1. 分析子が YAML を返したら、他の子の完了を待たずに `references/acceptance_pipeline.md` に沿って処理する。
2. final として受け入れる前に `run_metadata` を追加する。
3. `python3 tool/check_company_analysis_yaml.py <yaml-file>` で検証する。
4. validator failure、部分 YAML、YAML 外説明、unauthorized output は、`references/acceptance_pipeline.md` の失敗時対応に従う。

### 4. Review pipeline

1. review は毎回必須ではない。validator だけでは拾いにくい高リスク問題がある場合だけ使う。
2. review が必要な場合、`review_prompt_template.txt` に固定 scope、analysis YAML、必要時の rendered Markdown を inline で埋める。
3. review 子は `company-analysis-review` skill を使う。repository file path を渡して読ませない。
4. 同じ親 run 内では、明確に reset が必要でない限り、共有 review 子を再利用する。
5. review YAML は `python3 tool/check_company_analysis_review.py <review-yaml>` で検証する。
6. verdict が `revise` の場合、finding を分析子へ戻し、完全な修正版 YAML 再出力を求める。

### 5. Rendering と保存

1. YAML が受理されたら、`python3 tool/render_company_analysis_md.py <yaml-file>` で Markdown を生成する。
2. rendering-level の不整合を疑う場合だけ、render-focused review を行う。
3. 親は YAML と Markdown の両方を残す。
4. 複数の `scope.target_application_unit` を固定した場合、`scope.target_application_unit` ごとに独立した YAML / Markdown pair を残す。
5. 最終回答では保存した YAML と Markdown を示す。review 成果物を生成した場合はそれも示す。
