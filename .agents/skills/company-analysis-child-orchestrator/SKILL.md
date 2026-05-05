---
name: company-analysis-child-orchestrator
description: 親から渡された単一の企業名と職種リクエストを受け、対象 scope 固定、孫調査、YAML 検証、review、rendering、保存、result YAML 生成を end-to-end で行う子オーケストラ専用 skill。
---

# Company Analysis Child Orchestrator

## 目的

- 子オーケストラは、単一 target request の company analysis を end-to-end で完結する。
- 子は会社実体、応募単位、`role_family` を固定し、応募者 cohort と file 生成先は親から受け継ぐ。
- `run_id` は保存・照合用 ID とし、分析対象の意味判断には使わない。
- 子は孫調査エージェントと孫レビューエージェントを起動し、YAML intake、validation、review、rendering、保存、result YAML 生成を行う。
- 子は分析本文や評価判断を自分で書かない。評価判断は `company-analysis` 孫調査エージェントへ委譲する。

## 参照

- **対象 scope 固定**: `references/target_scope.md`
  - target request から fixed input YAML を作る前に読む。
- **受理 pipeline**: `references/acceptance_pipeline.md`
  - 孫調査後の intake、validation、review、rendering、保存、失敗時対応で読む。
- **孫調査 prompt**: `subagent_prompt_template.txt`
  - 孫調査エージェントへ渡す prompt template。現在 target の実値と副作用ガードだけを置き、調査・評価・schema 契約は `company-analysis` skill を正本にする。
  - placeholder だけを埋める。
- **孫 review prompt**: `review_prompt_template.txt`
  - 孫レビューエージェントへ渡す prompt template。review input bundle path だけを埋める。

## 参照境界

- 子が読む skill / reference は、`company-analysis-child-orchestrator` の `SKILL.md`、`references/`、prompt template、専用 tool、validator に限定する。
- 子は孫調査用の `company-analysis` skill、孫 review 用の `company-analysis-review` skill、およびそれらの references を読まない。
- 子は他 role の skill、過去 artifact、他 target output、比較 note、既存 review を schema 確認や判断根拠として読まない。
- 子が schema や field shape を確認する場合は、child-orchestrator の結果契約、専用 helper、validator だけを使う。
- 孫調査と孫 review は、それぞれの prompt template で指定された skill / reference だけを読む。

## 読み取り範囲

- 子が読んでよい local path は、child-orchestrator skill directory、現在の run directory、固定 input、生成した review input bundle、専用 tool、validator に限る。
- 子は `document/report/company_analysis/`、他 `tmp/company_analysis/runs/<other_run_id>/`、過去 test output、既存 review、比較 note を読まない。
- 子は `rg --files` や `ls` で `tmp/company_analysis/`、`document/report/company_analysis/`、`document/` 全体を広く列挙しない。
- 必要な path は、現在の run directory と helper の戻り値から得る。既存 artifact の探索で補完しない。

## 孫 agent 管理

- 子は 1 target につき、孫調査 agent 1 体、孫 review agent 1 体だけを起動する。
- `wait_agent` timeout、handoff file 未出現、review output 未出現だけを理由に同じ role の孫 agent を追加起動しない。
- timeout または file 未出現時は、同じ孫 agent へ最小限の再通知を行い、同じ agent の完了を待つ。
- review `revise`、validator failure、または修正版 working YAML に対する rereview では、新しい孫 review agent を起動せず、同じ孫 review agent に新しい review input bundle を渡す。
- 再起動してよいのは、対象 agent が明確に失敗した、回収不能になった、または同じ agent への再出力依頼後も invalid output が続いた場合だけとする。
- 再起動した場合は、旧 agent id、再起動理由、破棄した output path、採用した agent id、採用した output path を result YAML に残す。
- 孫 review agent を起動できない、または採用済み孫 review agent の valid `pass` review を得られない場合、子は review fallback artifact を作って `accepted` にしてはいけない。`status: review_failed` の result YAML を返す。

## 入力契約

- target request は、ユーザーがチャットで渡した内容を親が転記したものとして扱う。
- 必須入力:
  - `company_name`: ユーザーが指定した会社名。
  - `requested_role`: ユーザーが指定した職種、職種ファミリー、または応募意図。
  - `applicant_graduation_cohort`: 親がチャットから固定した応募者の卒業・修了見込み cohort。
  - `artifact_paths`: 親が割り当てる file 生成先 directory 群。
- 任意入力:
  - `raw_user_context`: 勤務地、研究志向、比較目的、test run などのユーザー明示条件。
  - `run_id`: 親が割り当てる `[a-z0-9_]+` の保存・照合用 ID。未指定なら子が UUID を `[a-z0-9_]+` に正規化して割り当てる。
- 親から fixed scope が渡されても正本にしない。子は `references/target_scope.md` に従って scope を固定する。
- target request に含まれない値は、親の意図として補完せず、子が調査して固定する。ただし `applicant_graduation_cohort` は親から受け継ぐ必須値であり、子は別 cohort へ置き換えない。
- company-analysis YAML schema 互換で `slug` が必要な場合は、`run_id` を `[a-z0-9_]+` に正規化した機械的識別子を使い、表示用・意味的 slug として扱わない。

## 副作用契約

- 子は `artifact_paths` 配下に handoff、working YAML、fixed input、review input、review output、child result、run output を作成してよい。
- run output は `artifact_paths.outputs_dir/<uuid>.yaml` と同じ stem の `<uuid>.md` とし、schema `slug` を filename に使わない。
- 子は共有 final path である `document/report/company_analysis/` 配下へ保存しない。
- 子は、保存名、一時ファイル名、`run_metadata` 追加など判断内容に影響しない機械的処理だけを行う。
- 既存 run directory に同じ `run_id` の artifact がある場合でも、既存 artifact を読み込んで補完せず、新しい UUID file を作る。

## Model 契約

- 子オーケストラ、孫調査、孫 review はすべて `gpt-5.4-mini`、`reasoning_effort: medium` を標準とする。
- 子オーケストラは、孫調査と孫 review を起動するときに model と `reasoning_effort` を必ず明示する。
- 省略による親 model 継承を使わない。
- `run_metadata.model` と `run_metadata.reasoning_effort` は、孫調査エージェントを実際に起動した model と `reasoning_effort` だけから埋める。default 値や記憶から推定しない。
- result YAML の `run_models` には、子オーケストラ、孫調査、孫 review の起動時に明示した model と `reasoning_effort` を記録する。

## Workflow

1. **scope 固定**:
   - `references/target_scope.md` を読み、会社実体、応募単位、`role_family`、働く場として評価する entity を固定する。
   - `scope.target_application_unit` は公式応募単位に準拠し、`requested_role` が公式単位より細かい志向の場合は `scope.ambiguity_note` に残す。
   - `applicant_graduation_cohort` は target request の値を fixed input YAML に引き継ぐ。
   - 公式 route が複数あり固定不能な場合は、分析へ進まず `status: revise_scope` の result YAML を返す。
   - fixed input YAML を `artifact_paths.child_inputs_dir/<uuid>.yaml` へ保存する。

2. **孫調査**:
   - UUID handoff path を `artifact_paths.subagent_outputs_dir/<uuid>.yaml` に割り当てる。
   - `subagent_prompt_template.txt` の placeholder だけを埋め、孫調査エージェントを 1 体起動する。
   - 孫調査エージェントは `gpt-5.4-mini`、`reasoning_effort: medium` を明示して起動する。
   - 孫調査には fixed input だけを渡し、既存 report や他 target output を根拠として読ませない。
   - 孫調査の出力待ち中は、`wait_agent`、当該 handoff path の最小確認、必要な再通知だけを行う。他 skill、他 target artifact、過去 output は読まない。

3. **受理と review**:
   - `references/acceptance_pipeline.md` に従い、handoff YAML intake、`run_metadata` 追加、main validation、review input bundle 作成、孫 review、review validation を行う。
   - 子が直接使う command は `references/acceptance_pipeline.md` の **Tools** に列挙されたものに限る。
   - 孫 review エージェントは `gpt-5.4-mini`、`reasoning_effort: medium` を明示して起動する。
   - review `revise` または validator failure は、同 pipeline の上限内で孫調査へ再出力を求める。
   - 修正版 YAML を rereview する場合は、既存の孫 review agent に新しい review input bundle を渡す。
   - 孫 review の出力待ち中は、`wait_agent`、当該 review output path の最小確認、必要な再通知だけを行う。他 skill、他 target artifact、過去 output は読まない。

4. **rendering と保存**:
   - review `pass` 後に Markdown rendering、run-scoped output への copy、保存後 validation を行う。
   - output path は `references/acceptance_pipeline.md` の **Output** に従う。

5. **result YAML 返却**:
   - 最後は単一 result YAML オブジェクトだけを返す。
   - 同じ YAML を `artifact_paths.child_results_dir/<uuid>.yaml` に保存する。

## 結果契約

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

`status: accepted` 以外では、存在しない artifact path を `null` にし、`failure_reason` に停止理由を書く。
`status: accepted` は、main validator、採用済み孫 review agent による valid `pass` review、review validator、rendering、保存後 validation がすべて完了した場合だけ使う。
`target_request` には親から渡された `company_name`、`requested_role`、`applicant_graduation_cohort` を残す。
`run_id` には親から渡された値、または子が割り当てた UUID を残す。
`artifact_paths` には実際に使った file 生成先 directory 群を残す。
`fixed_scope` には子が固定した scope を残す。固定不能な場合は、判明した候補と固定不能理由を残す。
`spawned_agents` には、孫調査と孫 review の agent id、role、status、採用 / 破棄、出力 path、再起動理由を残す。再起動がない場合も、起動した 2 体を記録する。
`spawned_agents` では、採用済み孫 review agent を `role: grandchild_review`、`adopted: true`、非 null `agent_id`、valid review output path で識別できるようにする。
`run_models` には `child_orchestrator`、`grandchild_research`、`grandchild_review` を入れ、それぞれ `model` と `reasoning_effort` を持たせる。実際に spawn できなかった role は `spawned: false` と失敗理由を記録し、`status: accepted` にしない。

## 完了条件

- accepted target では、validator、採用済み孫 review agent による内容 review、rendering、保存後 validation が完了している。
- accepted でない target では、status、failure reason、次に必要なユーザー判断が result YAML に入っている。
