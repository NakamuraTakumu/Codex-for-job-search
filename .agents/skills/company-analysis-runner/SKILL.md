---
name: company-analysis-runner
description: 企業名と職種リクエストだけを対象ごとに子オーケストラへ渡し、複数の company analysis 子を並列起動して子 result を集約する親専用 skill。
---

# Company Analysis Runner

## 目的

- 親エージェントは、ユーザー入力から company analysis の target request を切り出し、`company-analysis-child-orchestrator` 子を並列起動する。
- 親は会社実体、応募単位、`role_family`、scope、score、根拠、report を判断しない。
- 親が付ける識別子は `run_id` だけとし、分析対象の意味判断には使わない。
- 親は YAML 受理、review、rendering、子 result 生成を行わない。これらは子オーケストラの責務とする。
- 親は runner 実行中に accepted report path へ昇格しない。昇格は、ユーザーが child result を指定して明示的に依頼した場合だけ別操作として行う。

## 入力契約

- target request の入力元は、ユーザーがこのチャットで渡した内容だけとする。
- target request は、最低限 `company_name`、`requested_role`、`applicant_graduation_cohort` を持つ。
- 1 つの `requested_role` が複数会社に共通する場合、各会社へ同じ `requested_role` を渡す。
- 1 つの `applicant_graduation_cohort` が複数会社に共通する場合、各会社へ同じ `applicant_graduation_cohort` を渡す。
- `applicant_graduation_cohort` は応募者の卒業・修了見込み cohort を表し、`2028卒` のような4桁年表記に正規化する。
- 会社名、職種リクエスト、または応募者 cohort が不足している場合だけ、親がユーザーに確認する。
- 親はチャット外の manifest、既存 report、公式情報調査から target request を補完しない。
- 応募 route、正式職種名、採用実体、研究職か研究開発職かの固定は子に任せる。
- 親は target request ごとに `run_id` を付ける。`run_id` は同一親 run 内で一意な `[a-z0-9_]+` の保存・照合用 ID であり、公式応募単位、scope、score、根拠判断に使わない。
- 親は target request ごとに `run_root` を割り当てる。`run_root` は file 生成先だけを表し、分析対象の意味判断には使わない。

`run_root`:

- `tmp/company_analysis/runs/<run_id>`

## 副作用契約

- 親は子オーケストラを起動し、子の最終 result YAML を受け取る。
- 親は runner 実行中、子 artifact を `document/report/company_analysis/` へ copy しない。
- 親が書いてよいのは、ユーザーが明示的に求めた比較 note または run summary だけとする。
- accepted report path への昇格は runner workflow から分離する。ユーザーが child result path を指定して昇格を依頼した場合だけ、`.agents/skills/company-analysis-runner/tool/promote_child_result.py <child-result-yaml>` を使う。
- 親は子の artifact を書き換えない。失敗時も子 result の status と failure reason をそのまま扱う。

## 参照境界

- 親が読む skill は `company-analysis-runner` と、その workflow で直接参照する子 prompt template だけにする。
- 親は `company-analysis-child-orchestrator`、`company-analysis`、`company-analysis-review` の skill 本文や references を読まない。
- 親は既存 report、他 target output、比較 note、過去 review を target request 作成や子 result 解釈の根拠として読まない。
- 子 result が invalid YAML の場合も、親は子 result schema を他 artifact から推測せず、同じ子に result YAML の再出力だけを求める。

## 並列実行

- 子は target request ごとに 1 体起動する。
- `spawn_agent.fork_context` は `false` にする。
- 子オーケストラの model は `gpt-5.4-mini`、`reasoning_effort` は `medium` を標準とする。
- 子オーケストラ起動時は、model と `reasoning_effort` を必ず明示する。省略による親 model 継承を使わない。
- ユーザーが別 model を明示した場合だけ、標準 model から変更する。
- 同時起動は最大 4 体にする。5 件以上は補充キューで処理する。
- 子 prompt は `child_orchestrator_prompt_template.txt` の placeholder だけを埋める。
- 完了済みの子は、子 result の機械的確認が終わり、同じ子へ再出力や protocol violation 対応を求める必要がない terminal 状態になった時点で、次の子起動前に `close_agent` で終了する。

## Workflow

1. **target request 作成**:
   - チャット本文から `company_name`、`requested_role`、`applicant_graduation_cohort` の組を作る。
   - 各 target request に同一親 run 内で一意な `run_id` を割り当てる。
   - 各 target request に `run_root` を割り当てる。
   - 親は公式情報調査や scope 固定を行わない。

2. **子起動**:
   - 各 target request について `company-analysis-child-orchestrator` を使う子を起動する。
   - 子には企業名、職種リクエスト、応募者 cohort、`run_id`、`run_root`、model settings だけを渡す。

3. **結果集約**:
   - 子が返した単一 result YAML を集める。
   - 子の出力待ち中に、他 target の artifact、既存 report、過去 review、子や孫の skill を読まない。
   - 子 result の `run_models.child_orchestrator` が、親の spawn 設定と一致するか確認する。
   - 子 result が `status: accepted` の場合、`spawned_agents` に非 null `agent_id` を持つ採用済み `grandchild_review` があり、`review_yaml_path` が非 null であることを確認する。
   - `status: accepted` なのに採用済み `grandchild_review` がない、`grandchild_review.spawned: false`、または review spawn failure が記録されている場合は、子 result の protocol violation として扱い、同じ子に result YAML の修正ではなく `status: review_failed` への再出力を求める。
   - 子 result が invalid YAML の場合だけ、同じ子に result YAML の再出力を求める。
   - 子 result が YAML として読め、親が見る field、model 設定、accepted 時の `grandchild_review` 記録、主要 path の存在に問題がなく、同じ子への追加依頼が不要になったら、その子を `close_agent` で直ちに終了する。
   - invalid YAML、protocol violation、主要 path 欠落などで同じ子へ再出力を求める場合は、再出力結果の機械的確認が終わるまで閉じない。

4. **結果報告**:
   - runner 実行では昇格せず、run-scoped artifact path だけを最終回答に並べる。
   - `status: accepted` は review と validation を通過した run-scoped result を表し、production 昇格の指示ではない。

## 子 Result 期待

親は子 result の schema を再定義しない。`company-analysis-child-orchestrator` の **結果契約** を正とする。

親が見る field:

- `target_request`
- `run_id`
- `status`
- `analysis_yaml_path`
- `rendered_markdown_path`
- `review_yaml_path`
- `residual_risks`
- `failure_reason`
- `spawned_agents`
- `run_models`

## 完了条件

- 起動したすべての子について result YAML を受け取っている。
- final response では、run-scoped path と、accepted でない target または protocol violation がある target の status / failure reason だけを示す。
