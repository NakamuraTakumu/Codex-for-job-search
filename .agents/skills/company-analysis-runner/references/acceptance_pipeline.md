# Acceptance Pipeline

## 用途

- `company-analysis-runner` が分析子から YAML を受け取った後の受理、review、rendering、保存を扱う。
- 子 YAML を final artifact として受け入れる前に読む。

## Tools

- **handoff preparer**: `python3 tool/accept_subagent_company_analysis.py <handoff-yaml-or-dir> [slug ...]`
- **main validator**: `python3 tool/check_company_analysis_yaml.py <yaml-file>`
- **review input preparer**: `python3 .agents/skills/company-analysis-runner/tool/prepare_review_input.py --run-slug <run_slug> <working-yaml>`
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

### YAML Intake

- **入力**: 親が指定した `tmp/company_analysis/subagent_outputs/<run_slug>/<uuid>.yaml` の handoff file を主入力とし、分析子が返した message YAML を fallback とする。中間成果物のファイル名は UUID にし、slug は YAML 内部で確認する。
- **処理**: handoff file と message の YAML が同じ対象を指すか、YAML 外説明が混ざったか、部分 YAML だけか、unauthorized output があるか、または `scope_check.verdict: revise_scope` かを親が判断する。
- **正常時**: handoff file または message 内の完全な YAML を作業用 file として validation に進む。
- **失敗時**:
  - `scope_check.verdict: revise_scope` の場合、final artifact として受理しない。親が scope を修正し、scope manifest を更新してから、修正後 scope で再実行する。
  - handoff file がない、壊れている、または message YAML と slug / scope が食い違う場合、message YAML で安全に続行できるか判断し、必要なら完全な YAML 再出力を求める。
  - YAML 外説明が混ざった場合、その点を明示して再出力を求める。
  - 部分 YAML の場合、不足 top-level key を列挙して完全な YAML 再出力を求める。
  - 子が親指定 handoff path 以外に成果物を自分で作成、変更、保存した場合、それらは unauthorized output とみなす。
  - unauthorized output は final artifact として扱わず、必要に応じて削除または隔離し、message で返された YAML から続行する。

### Main Validation

- **入力**: 作業用 YAML file。handoff preparer を使う場合は `tmp/company_analysis/working/<uuid>.yaml`。
- **処理**:
  - final として受け入れる前に、親が `run_metadata` を追加する。
  - `tool/accept_subagent_company_analysis.py` は review 前の作業用 YAML 作成と validation までを補助する。final 保存、Markdown rendering、review 省略には使わない。
  - `python3 tool/check_company_analysis_yaml.py <yaml-file>` を実行する。
- **正常時**: 必須 review へ進む。
- **失敗時**:
  - schema 違反を列挙し、分析子に完全な修正版 YAML 再出力を求める。
  - validator mismatch がある場合、親が黙って判断内容を修正しない。
  - 親が直してよいのは、保存名ミス、一時ファイル名など、内容判断に影響しない明らかな機械的問題だけ。

### Review Decision

- **入力**: validator 通過済み YAML。
- **処理**: validator を通過した YAML は、その都度 **Review Handoff** へ進める。複数対象 run でも、他の分析子の完了を待たない。
- **正常時**:
  - review が `pass` なら rendering へ進む。
  - review が `revise` なら分析子へ修正依頼する。
- **並列時**:
  - 固定済み対象が複数ある run では、完了順に review できるよう共有 review 子を原則 1 つだけ起動して再利用する。
  - 固定済み対象が複数あり、分析子を並列起動した場合、最初の review input bundle がなくても共有 review 子を必ず prewarm する。
  - review 子が未起動のまま分析子出力を待っていることに気づいた場合、新しい分析子を起動せず、共有 review 子の起動と完了済み YAML の検証・review を先に処理する。
  - `wait_agent` は最初に完了した分析子を受け取るために使い、全分析子の完了を待つ batch wait にしない。
  - 単一対象でも validator 通過後は必ず review 子を起動する。

### Review Handoff

- **入力**: review input bundle file。bundle には固定 scope、analysis YAML path、必要時の rendered Markdown path、review output path を含める。
- **処理**:
  - review 子は `company-analysis-review` skill を使う。
  - `python3 .agents/skills/company-analysis-runner/tool/prepare_review_input.py --run-slug <run_slug> <working-yaml>` で `tmp/company_analysis/review_inputs/<run_slug>/<uuid>.md` を作る。
  - prewarm 済み review 子には、bundle ができるたびに `review_prompt_template.txt` で review input bundle path だけを渡す。analysis YAML や rendered Markdown の本文は通常 inline で渡さない。
  - review 子は bundle に明示された `analysis_yaml_path` と、`rendered_markdown_path` が `null` でない場合だけその Markdown を読む。
  - 同じ親 run 内では、実用上可能なら 1 つの共有 review 子を会社・対象をまたいで再利用する。対象ごとに新しい review 子を作らない。
  - review 子を追加起動するのは、既存 review 子が壊れた、reset できない状態を保持している、重大な遅延で親 run が止まる、または render-focused review を分離する必要がある場合に限る。
  - 共有 review 子を再利用する場合でも、template 内の reset 指示を残し、各 review input bundle を独立した新規対象として扱わせる。
  - 毎回の review 引き渡しで、現在意図している `slug` を明示し、それだけを理由に scope error としないよう伝える。
  - review 中は、過去の比較結果や期待する結論に合わせない。review input bundle と参照先 file だけから判断させる。
- **出力**: review YAML。review 子は bundle の `review_output_path` に保存し、同じ YAML を返答する。
- **注意**:
  - デフォルトでは会社ごとに review 子を作り直さない。
  - 複数の分析子が動いている場合、完了したものをまとめず、最初に完了した子からすぐ review へ渡す。
  - review 子の起動を、最初の analysis YAML の validation 完了後まで遅らせない。
  - rendered Markdown は rendering 後の render-focused review のときだけ追加する。通常の必須 review では analysis YAML を対象にする。
  - inline payload は、filesystem handoff が壊れている、または reviewer が file を読めない場合だけ fallback として使う。
  - review schema と詳細な review 観点は `company-analysis-review` skill を権威とする。

### Scope Rerun Ownership

- **通常 YAML 作成前に `scope_check` で止まった場合**: 親が scope manifest を修正し、同じ分析子に修正後 scope と新しい UUID handoff path を渡して再実行する。
- **広い scope で調査済みの場合**: 旧結果は final artifact にせず、親が新しい分析子を起動する。
- **採用実体または職種が大きく変わる場合**: 親が別 slug として扱い、新しい分析子を起動する。
- **親の scope 固定ミスだけの場合**: 親が manifest を直し、handoff path を更新してから既存分析子へ戻す。

### Review Result

- **入力**: review YAML。
- **処理**: `python3 tool/check_company_analysis_review.py <review-yaml>` を実行する。
- **正常時**:
  - verdict が `pass` の場合、rendering へ進む。
  - verdict が `revise` の場合、finding を分析子へ戻し、完全な修正版 YAML 再出力を求める。
- **失敗時**:
  - review 子が invalid review YAML を返した場合、schema 違反を列挙して review 子に再出力を求める。
  - レンダリング前内容 review が `revise` を返した場合、親が分析内容を自分で直さない。
  - デフォルトでは、1 成果物につき修正 rerun と rereview は各 1 回までとする。
  - validator failure または新しい high severity issue が出ない限り、同じ成果物を無期限 review にしない。
  - rereview では、前回 finding が解消されたかを中心に見る。
  - 新しい high severity issue が見える場合を除き、rereview を完全な新規 review に広げない。
  - test rerun では、medium 以下の `source_quality` finding を known issue として記録し、production artifact へ昇格しない条件で処理を継続してよい。

### Rendering

- **入力**: 受理済み YAML。
- **処理**: `python3 tool/render_company_analysis_md.py <yaml-file>` で Markdown を生成する。
- **正常時**: output 保存へ進む。
- **render-focused review**:
  - 親が rendering-level の不整合を疑っている場合だけ起動する。
  - 受理済み YAML と rendered Markdown が一致していることを明示的に確認したい場合だけ起動する。
  - render-focused review でも `python3 tool/check_company_analysis_review.py <review-yaml>` を実行する。
  - render-focused review が `revise` を返した場合、finding を解消し、必要に応じて renderer または reviewer を再実行してから成果物を確定する。
- **必須条件**: validator、内容 review、rendering は必ず実行する。review を省略して final artifact にしない。

## Review Scope

- review schema と詳細な review 観点は `company-analysis-review` skill を権威とする。
- runner 固有の確認事項だけを review input bundle に渡す。
  - 親固定 scope と user requested target の関係。
  - analysis YAML path、必要時の rendered Markdown path、review output path。
  - 子が親指定 handoff path 以外でファイル作成・更新・保存・Markdown rendering をしていないか。
  - 通常 review では rendered Markdown を渡さず、render-focused review の場合だけ渡すこと。

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
- accepted YAML は `report/company_analysis/data/`、accepted Markdown は `report/company_analysis/companies/`、accepted review artifact は `report/company_analysis/reviews/` を default とする。
- ユーザーが「テスト」「test」「試行」「検証」と明示した run では、accepted output の保存先を `report/company_analysis/` にしない。YAML、Markdown、review artifact は `tmp/company_analysis/test_outputs/<run_slug>/data/`、`tmp/company_analysis/test_outputs/<run_slug>/companies/`、`tmp/company_analysis/test_outputs/<run_slug>/reviews/` に保存する。
- test output を `report/company_analysis/` に昇格してよいのは、ユーザーが明示的に promotion / accepted artifact 化を承認した場合だけとする。
- scope manifest、比較メモ、test/run note、workflow consideration は `document/` に保存する。
- 中間 handoff、working YAML、review input bundle、review output draft は `tmp/company_analysis/` に保存する。
- 必要に応じて、不確実性 review や比較 review も上記の保存先契約に従って保存する。
