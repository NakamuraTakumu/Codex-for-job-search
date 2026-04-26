# Acceptance Pipeline

## 用途

- `company-analysis-runner` が分析子から YAML を受け取った後の受理、review、rendering、保存を扱う。
- 子 YAML を final artifact として受け入れる前に読む。

## Tools

- **main validator**: `python3 tool/check_company_analysis_yaml.py <yaml-file>`
- **review validator**: `python3 tool/check_company_analysis_review.py <review-yaml>`
- **renderer**: `python3 tool/render_company_analysis_md.py <yaml-file>`

## 受理条件

- **metadata**:
  - final YAML には `run_metadata` が必須。
  - `run_metadata` には最低限 `executor`, `model`, `reasoning_effort`, `fixed_by_parent` を入れる。
  - 親は実際に子起動で使った設定を追記する。
  - final YAML で `model` や `reasoning_effort` を暗黙にしない。
- **validator**:
  - final YAML は main validator の hard requirement を満たす。
  - 公式 source は 4 件以上で、`recruit` と `company|ir` を含む。
  - `faq`、`benefits`、公式 `kind=research` source は優先探索対象だが、公開されていない場合は自動失敗ではなく、欠落または公開情報の薄さとして記録する。
- **非公式情報**:
  - final acceptance 条件は、非公式 lineage や暫定メモの記録を止める理由にはならない。
- **score**:
  - 合計スコア計算の正は Python 実装。分析子に合計を再計算させない。

## Pipeline

### 1. YAML Intake

1. **入力**: 分析子が返した message。
2. **処理**: YAML 外説明が混ざったか、部分 YAML だけか、unauthorized output があるかを親が判断する。
3. **正常時**: message 内の完全な YAML を作業用 file に保存して validation に進む。
4. **失敗時**:
   - YAML 外説明が混ざった場合、その点を明示して再出力を求める。
   - 部分 YAML の場合、不足 top-level key を列挙して完全な YAML 再出力を求める。
   - 子が成果物を自分で作成、変更、保存した場合、それらは unauthorized output とみなす。
   - unauthorized output は final artifact として扱わず、必要に応じて削除または隔離し、message で返された YAML から続行する。

### 2. Main Validation

1. **入力**: 作業用 YAML file。
2. **処理**:
   - final として受け入れる前に、親が `run_metadata` を追加する。
   - `python3 tool/check_company_analysis_yaml.py <yaml-file>` を実行する。
3. **正常時**: review 要否判定へ進む。
4. **失敗時**:
   - schema 違反を列挙し、分析子に完全な修正版 YAML 再出力を求める。
   - validator mismatch がある場合、親が黙って判断内容を修正しない。
   - 親が直してよいのは、保存名ミス、一時ファイル名など、内容判断に影響しない明らかな機械的問題だけ。

### 3. Review Decision

1. **入力**: validator 通過済み YAML。
2. **処理**: **Review Trigger** に当てはまるか確認する。
3. **正常時**:
   - trigger がある場合、**Review Handoff** へ進む。
   - trigger がない場合、rendering へ進む。
4. **並列時**:
   - 固定済み対象が複数ある run では、review が不要そうに見えても共有 review 子または review 用空き枠を 1 つ確保する。
   - review 子が未起動で空き枠もない場合、新しい分析子を起動せず、先に完了済み YAML の検証と review 要否判定を処理する。
   - 多数対象 run では、最初の review payload がなくても共有 review 子を prewarm してよい。
   - 単一対象で review trigger がない場合、開始直後に idle review 子を起動しない。

### 4. Review Handoff

1. **入力**: 固定 scope、analysis YAML、必要時の rendered Markdown。
2. **処理**:
   - review 子は `company-analysis-review` skill を使う。
   - 固定 scope と review 対象 YAML を prompt に直接埋め込む。
   - repository file path を渡して review 子に読ませない。
   - inline 引き渡しでは Markdown fence を使わず、明示的 delimiter 付きの plain-text block として埋め込む。
   - 同じ親 run 内では、実用上可能なら 1 つの共有 review 子を会社・対象をまたいで再利用する。
   - 共有 review 子を再利用する場合でも、template 内の reset 指示を残し、各 review を独立した新規対象として扱わせる。
   - 毎回の review 引き渡しで、現在意図している `slug` を明示し、それだけを理由に scope error としないよう伝える。
   - review 中は、過去の比較結果や期待する結論に合わせない。inline target data と必要最小限の文脈から判断させる。
3. **出力**: review YAML。
4. **注意**:
   - デフォルトでは会社ごとに review 子を作り直さない。
   - 複数の分析子が動いている場合、完了したものをまとめず、最初に完了した子からすぐ review へ渡す。
   - rendered Markdown は render-focused review のときだけ追加する。
   - review schema と詳細な review 観点は `company-analysis-review` skill を権威とする。

### 5. Review Result

1. **入力**: review YAML。
2. **処理**: `python3 tool/check_company_analysis_review.py <review-yaml>` を実行する。
3. **正常時**:
   - verdict が `pass` の場合、rendering へ進む。
   - verdict が `revise` の場合、finding を分析子へ戻し、完全な修正版 YAML 再出力を求める。
4. **失敗時**:
   - review 子が invalid review YAML を返した場合、schema 違反を列挙して review 子に再出力を求める。
   - レンダリング前内容 review が `revise` を返した場合、親が分析内容を自分で直さない。
   - デフォルトでは、1 成果物につき修正 rerun と rereview は各 1 回までとする。
   - validator failure または新しい high severity issue が出ない限り、同じ成果物を無期限 review にしない。
   - rereview では、前回 finding が解消されたかを中心に見る。
   - 新しい high severity issue が見える場合を除き、rereview を完全な新規 review に広げない。

### 6. Rendering

1. **入力**: 受理済み YAML。
2. **処理**: `python3 tool/render_company_analysis_md.py <yaml-file>` で Markdown を生成する。
3. **正常時**: output 保存へ進む。
4. **render-focused review**:
   - 親が rendering-level の不整合を疑っている場合だけ起動する。
   - 受理済み YAML と rendered Markdown が一致していることを明示的に確認したい場合だけ起動する。
   - render-focused review でも `python3 tool/check_company_analysis_review.py <review-yaml>` を実行する。
   - render-focused review が `revise` を返した場合、finding を解消し、必要に応じて renderer または reviewer を再実行してから成果物を確定する。
5. **必須条件**: すべての review を省略する場合でも、validator と rendering は必ず実行する。

## Review Trigger

- **scope_integrity**:
  - ユーザーが求めた対象と、親が固定した `scope.target_application_unit` の意味単位がずれている可能性がある。
  - `scope.role_family` が `scope.target_application_unit` と意味的に合っていない可能性がある。
  - 複数の `scope.target_application_unit` の情報が 1 つの YAML に混ざっている可能性がある。
  - 研究職・Research・研究所・R&D の意図に対して、近接する data science 職、SWE、consulting 職、広い技術職を固定した可能性がある。
- **structured_data**:
  - `fact_layer` に `true` や `false` など断定的な値があり、公式根拠が薄い可能性がある。
- **summary_consistency**:
  - `summary`、`concerns`、`not_suitable_for` が、各 section 本文より広い、または強い主張をしている。
- **source_quality**:
  - 非公式 source の内容が `facts_official` または `fact_layer.official` に入っている可能性がある。
  - 親会社、グループ会社、採用実体の source が区別されずに使われている。
  - 非公式情報が公式情報と矛盾し、最終判断に重要な影響を与えている。
  - `facts_official` または `facts_unofficial` が薄すぎ、比較や再判断に必要な情報が残っていない。
  - 重要な空白が残っているのに、その重大さや追加調査不足が分析文に十分残っていない。
  - 重要な空白が残っているのに、非公式 source が 0 件で、非公式確認の失敗記録もない。
- **score_consistency**:
  - section の `facts_official` / `facts_unofficial` と `evaluation` / `score` の強さが釣り合っていない。

## Uncertainty Mode

- **入力**: 同じ固定 scope に対する不確実性確認要求。
- **実行**:
  - 同じ固定 scope に対して少なくとも 3 つの独立した分析子を起動する。
  - 各子には異なる `slug` を与える。
  - 比較自体が目的でない限り、子に既存レポート、比較レビュー、過去の不確実性確認結果、他エージェント出力を読ませない。
  - 各 YAML に main validator を実行する。
- **集計**:
  - 親は総合評価と section score について、範囲、平均、中央値、標準偏差を集計する。
  - `evaluation-target mismatch` と `scoring variance` を混同しない。

## Output

- 親エージェントは YAML と Markdown の両方を残す。
- 複数の `scope.target_application_unit` を固定した場合、`scope.target_application_unit` ごとに独立した YAML / Markdown pair を残す。
- 対象名は決定的にし、`slug` と保存ファイル名を合わせる。
- default は日付なしの簡潔な対象ベース名とする。
- 日付は、曖昧性解消または複数 run の明示的保存に必要な場合だけ付ける。
- cross-target comparison が必要な場合、親は別の comparison note または review artifact を作る。
- 保存先、命名、test と production の分離は親が決める。
- 必要に応じて、不確実性 review や比較 review も適切な場所に保存する。
