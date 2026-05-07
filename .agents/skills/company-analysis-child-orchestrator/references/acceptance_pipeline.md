# Acceptance Pipeline

## 用途

- 子オーケストラが、孫調査エージェントの YAML を run-scoped artifact として受理するまでの手順を定める。
- 子オーケストラは、target request から fixed input YAML を作った後にこの file を読む。

## Tools

- **handoff preparer**: `python3 tool/accept_subagent_company_analysis.py --run-id <run_id> <handoff-yaml-or-dir>`
  - 子オーケストラは、孫調査エージェントを実際に起動した model と `reasoning_effort` を `--model` と `--reasoning-effort` に必ず明示する。
- **main validator**: `python3 tool/check_company_analysis_yaml.py <yaml-file>`
- **YAML helper implementation**: `.agents/skills/company-analysis-child-orchestrator/tool/company_analysis_yaml.py`
  - root `tool/company_analysis_yaml.py` は compatibility shim。子オーケストラは validator / renderer command 経由で使い、直接 schema を再実装しない。
- **review input preparer**:
  - `python3 .agents/skills/company-analysis-child-orchestrator/tool/prepare_review_input.py --run-id <run_id> --fixed-input-yaml <fixed-input-yaml> --expected-handoff-path <handoff-output-path> --handoff-match <matched|message_fallback|missing|mismatch|not_checked> --unauthorized-outputs <observation> --unexpected-rendering <observation> --child-run-metadata-present <true|false> --requested-target <target-or-null> --scope-rationale <rationale-or-null> <working-yaml>`
- **review validator**: `python3 tool/check_company_analysis_review.py <review-yaml>`
- **renderer**:
  - explicit file output: `python3 tool/render_company_analysis_md.py --output <markdown-file> <yaml-file>`

## 参照境界

- 子オーケストラは、この pipeline、child-orchestrator の prompt template、専用 tool、validator だけを使って受理処理を進める。
- 子オーケストラは、孫調査用 skill、孫 review 用 skill、他 target output、過去 artifact、比較 note を schema 確認や待機中作業のために読まない。
- 孫調査と孫 review には、各 prompt template が指定する role 専用 skill / reference だけを読ませる。
- 孫 agent の出力待ち中は、`wait_agent`、当該 handoff / review output path の最小確認、必要な再通知だけを行う。

## 読み取り範囲

- 子オーケストラがこの pipeline で読む path は、現在の `tmp/company_analysis/runs/<run_id>/` 配下、child-orchestrator skill directory、専用 tool、validator に限る。
- `document/report/company_analysis/`、他 run directory、過去 test output、既存 review、比較 note は読まない。
- `tmp/company_analysis/`、`document/report/company_analysis/`、`document/` 全体の file listing をしない。
- path 発見は、現在の run directory、明示引数、helper が出力した path だけを使う。

## 孫 agent 管理

- 子オーケストラは、孫調査 agent と孫 review agent をそれぞれ 1 体だけ起動する。
- `wait_agent` timeout、handoff file 未出現、review output 未出現だけでは追加起動しない。
- timeout または file 未出現時は、同じ agent に最小限の再通知を送り、同じ agent からの出力を待つ。
- review `revise`、validator failure、または修正版 working YAML に対する rereview では、新しい孫 review agent を起動せず、同じ孫 review agent に新しい review input bundle を渡す。
- 追加起動は、agent failure、回収不能、同一 agent への再出力依頼後も invalid output が続く場合に限る。
- 追加起動した場合は、旧 agent id、破棄理由、採用 agent id、採用 output path を子 result の `spawned_agents` に残す。
- 孫 review agent を起動できない、または採用済み孫 review agent の valid `pass` review を得られない場合、子オーケストラは review fallback artifact を作って `accepted` にしてはいけない。`status: review_failed` の result YAML を返す。

## 受理条件

- `run_root` から標準 artifact paths を導出する:
  - `child_inputs_dir`: `<run_root>/child_inputs`
  - `subagent_outputs_dir`: `<run_root>/subagent_outputs`
  - `working_dir`: `<run_root>/working`
  - `review_inputs_dir`: `<run_root>/review_inputs`
  - `reviews_dir`: `<run_root>/reviews`
  - `outputs_dir`: `<run_root>/outputs`
  - `child_results_dir`: `<run_root>/child_results`
- fixed input YAML は子オーケストラが target request から固定した scope 正本であり、analysis YAML から作らない。
- fixed input YAML には top-level の `company_name`、`survey_date`、`slug`、`applicant_graduation_cohort`、`scope` が必要である。
- `slug` は company-analysis YAML schema 互換の機械的識別子であり、原則として `run_id` を `[a-z0-9_]+` に正規化した値を使う。scope 固定や評価判断には使わない。
- fixed input YAML の `scope` には `user_label`、`target_application_unit`、`hiring_entity_name`、`role_family`、`alternative_application_units`、`workplace_entity_name`、`ambiguity_note` が必要である。
- 受理後 YAML には `run_metadata` が必須。
- `run_metadata` には最低限 `executor`、`model`、`reasoning_effort`、`fixed_by_parent` を入れる。
- `fixed_by_parent` は互換性のための legacy key として使い、値は「孫調査エージェントではなくオーケストラが scope を固定した」ことを表す。
- 子オーケストラは、実際に孫調査エージェント起動で明示した model と `reasoning_effort` を `run_metadata` に追加する。default 値や親からの継承推定で埋めない。
- 孫調査 YAML に `run_metadata` が含まれている場合は出力契約違反として扱い、review input bundle に `child_run_metadata_present: true` を残す。
- 受理後 YAML は main validator の hard requirement を満たす。
- review は全 run-scoped artifact で必須とし、validator 通過後、rendering 前に実行する。
- review は、実際に起動した孫 review agent が返した valid review YAML だけを内容 review として数える。子オーケストラが review YAML を代筆、機械生成、または bundle/validator だけで確定したものは accepted 条件を満たさない。
- 子オーケストラは分析本文や評価判断を書き換えない。修正できるのは保存名、一時ファイル名、`run_metadata` 追加など判断内容に影響しない機械的処理だけに限る。

## Pipeline

### Grandchild Research

- **入力**: 子が固定した fixed input、UUID handoff path、`subagent_prompt_template.txt`。
- **処理**:
  - 子オーケストラは孫調査エージェントを 1 体起動する。
  - 既に孫調査 agent を起動済みなら、新しい孫調査 agent を起動せず、その agent の完了または再出力を待つ。
  - prompt template は placeholder だけを埋める。本文の言い換え、並べ替え、削除、場当たり的な追記をしない。
  - 孫調査エージェントには、指定 handoff path 以外の成果物を作らせない。
- **出力**: handoff YAML、または message fallback YAML。

### YAML Intake

- **入力**: `tmp/company_analysis/runs/<run_id>/subagent_outputs/<uuid>.yaml` の handoff file を主入力とし、孫調査エージェントが返した message YAML を fallback とする。
- **処理**:
  - handoff file と message YAML が同じ対象を指すか確認する。
  - YAML 外説明、部分 YAML、unauthorized output、`scope_check.verdict: revise_scope` を確認する。
  - 子が作った fixed input を正本とし、analysis YAML から fixed scope を逆算しない。
- **失敗時**:
  - `scope_check.verdict: revise_scope` は `status: revise_scope` の result YAML として返す。
  - handoff file がない、壊れている、message YAML と scope が食い違う、YAML 外説明が混ざる、または部分 YAML の場合は、孫調査エージェントに完全な YAML 再出力を求める。
  - unauthorized output は受理 artifact として扱わず、review input bundle または子 result に記録する。

### Main Validation

- **入力**: `tmp/company_analysis/runs/<run_id>/working/<uuid>.yaml` の作業用 YAML file。
- **処理**:
  - run-scoped artifact として受け入れる前に、子オーケストラが `run_metadata` を追加する。
  - `python3 tool/check_company_analysis_yaml.py <yaml-file>` を実行する。
- **失敗時**:
  - schema 違反を列挙し、孫調査エージェントに完全な修正版 YAML 再出力を求める。
  - validator mismatch がある場合、子オーケストラが黙って判断内容を修正しない。
  - 再出力後も失敗する場合は `status: validator_failed` の result YAML として返す。

### Review Handoff

- **入力**: validator 通過済み YAML、fixed input、handoff observations。
- **処理**:
  - 子オーケストラは review input bundle を `tmp/company_analysis/runs/<run_id>/review_inputs/` 配下に作る。
  - 孫レビューエージェントを 1 体起動し、`review_prompt_template.txt` の placeholder だけを埋めて渡す。
  - 既に孫レビュー agent を起動済みなら、review input bundle が変わっていても新しい孫レビュー agent を起動せず、その agent に現在の bundle を渡して完了または再出力を待つ。
  - 孫レビューエージェントは `company-analysis-review` skill を使う。
  - review input bundle には、fixed input、analysis YAML path、必要時の rendered Markdown path、review output path、handoff observations を入れる。
  - 通常 review では rendered Markdown を渡さない。render-focused review の場合だけ渡す。
- **失敗時**:
  - invalid review YAML は schema 違反を列挙して孫レビューエージェントに再出力を求める。
  - review `revise` はデフォルト 1 回まで孫調査エージェントへ修正依頼する。再 review 後も `revise` の場合は `status: review_revise` の result YAML として返す。
  - 孫レビュー agent の spawn failure、thread limit、回収不能、または同じ agent への再出力依頼後も invalid review YAML が続く場合は、`status: review_failed` の result YAML として返す。
  - 子オーケストラは、review agent failure を補うために自分で pass review YAML を作らない。

### Review Result

- **入力**: review YAML。
- **処理**:
  - `python3 tool/check_company_analysis_review.py <review-yaml>` を実行する。
  - verdict が `pass` の場合、rendering へ進む。
  - verdict が `revise` の場合、finding を孫調査エージェントへ戻し、完全な修正版 YAML 再出力を求める。
- **制限**:
  - デフォルトでは、1 成果物につき修正 rerun と rereview は各 1 回までとする。
  - rereview では、新しい review input bundle を同じ孫 review agent に渡し、前回 finding が解消されたかを中心に見る。
  - review が `pass` の場合でも、`pass_rationale` と `residual_risks` を子 result に反映する。

### Rendering

- **入力**: review pass 済み YAML。
- **処理**:
  - Markdown filename は、保存後 YAML と同じ UUID stem の `<uuid>.md` とする。
  - Markdown は `python3 tool/render_company_analysis_md.py --output <markdown-file> <yaml-file>` で生成する。
  - `<markdown-file>` は `artifact_paths.outputs_dir` 配下に置く。
  - default command の `python3 tool/render_company_analysis_md.py <yaml-file>` は accepted report path へ書く可能性があるため、子オーケストラでは使わない。
- **注意**:
  - rendering 前の内容 review を省略しない。
  - 子が rendering-level の不整合を疑う場合だけ render-focused review を追加する。

### Run Output And Revalidation

- **順序**: run-scoped output への copy、保存後 validation、rendering は、同一 artifact について逐次実行する。並列実行しない。
- **保存名**: 受理後 YAML は `artifact_paths.outputs_dir/<uuid>.yaml` へ copy し、Markdown は同じ UUID stem の `artifact_paths.outputs_dir/<uuid>.md` へ render する。
- **正常時**: YAML copy 後に main validator、採用済み孫 review agent の review output に対する review validator、Markdown rendering の順に確認する。
- **失敗時**: 保存済み file の path と直前に成功した step を記録し、未完了 step だけを再実行する。

## 子 Result

子オーケストラは最後に単一 result YAML を返す。
同じ result YAML を `artifact_paths.child_results_dir/<uuid>.yaml` に保存する。

必須 field:

- `target_request`
- `run_id`
- `artifact_paths`
- `fixed_scope`
- `status`: `accepted`、`revise_scope`、`validator_failed`、`review_revise`、`review_failed`、`child_failed`
- `analysis_yaml_path`
- `rendered_markdown_path`
- `review_yaml_path`
- `fixed_input_path`
- `child_result_path`
- `residual_risks`
- `failure_reason`
- `commands_run`
- `unauthorized_outputs`
- `spawned_agents`
- `run_models`

`status: accepted` 以外では、存在しない path を `null` にし、`failure_reason` に停止理由を書く。
`status: accepted` は、main validator、採用済み孫 review agent による valid `pass` review、review validator、rendering、保存後 validation がすべて完了した場合だけ使う。
`target_request` には親から渡された `company_name`、`requested_role`、`applicant_graduation_cohort` を残す。
`artifact_paths` には実際に使った file 生成先 directory 群を残す。
`spawned_agents` には、孫調査と孫 review の agent id、role、status、採用 / 破棄、出力 path、再起動理由を残す。
採用済み孫 review agent は `role: grandchild_review`、`adopted: true`、非 null `agent_id`、valid review output path で識別できるようにする。
`run_models` には `child_orchestrator`、`grandchild_research`、`grandchild_review` を入れ、それぞれ `model` と `reasoning_effort` を持たせる。実際に spawn できなかった role は `spawned: false` と失敗理由を記録し、`status: accepted` にしない。

## Output

- 子は並列衝突を避けるため、受理後 YAML と Markdown を `artifact_paths.outputs_dir` 配下へ保存する。
- 受理後 YAML と Markdown は、schema `slug` ではなく同じ UUID stem の `<uuid>.yaml` と `<uuid>.md` にする。
- review artifact は `artifact_paths.reviews_dir` 配下へ保存する。
- 子は `document/report/company_analysis/` 配下へ直接保存しない。
- scope manifest、比較メモ、test/run note、workflow consideration は `document/` に保存する。
- 中間 handoff、working YAML、review input bundle、review output draft、子 result は `artifact_paths` の該当 directory に保存する。
