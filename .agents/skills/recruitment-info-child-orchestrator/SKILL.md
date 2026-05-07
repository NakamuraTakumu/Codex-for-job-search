---
name: recruitment-info-child-orchestrator
description: runner から渡された単一企業の target request を受け、research 孫と review 孫を起動し、report/recruitment-info 配下への YAML 保存確認と差し戻しだけを行う子オーケストラ用 skill。子自身に調査本文、review 判断、fact 修正をさせない場合に使う。
---

# Recruitment Info Child Orchestrator

## 目的

- 単一 target request の recruitment info 調査を `report/recruitment-info` 配下の data artifact として完結する。
- 子は調査判断、review finding の正誤判断、採用 fact の修正を書かない。
- 子は `recruitment-info-research` を使う research 孫と `recruitment-info-review` を使う review 孫を管理する。
- 子は固定 prompt template で孫に依頼し、YAML intake、機械的形式検証、review 受理、差し戻し、review finding の機械的な進捗判定、result YAML 生成だけを行う。

## 入力契約

- 必須入力:
  - `company_name`
- 任意入力:
  - `applicant_graduation_cohort`
  - `target_year`
  - `output_root`

## 参照

- research 孫 prompt: `grandchild_research_prompt_template.txt`
- review 孫 prompt: `grandchild_review_prompt_template.txt`
- 調査 skill: `../recruitment-info-research/SKILL.md`
- 出力契約: `../recruitment-info-research/references/output-contract.md`
- review skill: `../recruitment-info-review/SKILL.md`

## Agent 実行契約

- 初回に research 孫を 1 体、review 孫を 1 体だけ起動する。
- 孫起動では `spawn_agent.model: gpt-5.4-mini`、`reasoning_effort: medium` に固定する。
- 差し戻し後の再 research は、新しい research 孫を起動せず、同じ research 孫へ `send_input` で依頼する。
- 再 review は、新しい review 孫を起動せず、同じ review 孫へ `send_input` で依頼する。
- 同じ孫 agent が閉じた、失敗した、または応答不能になった場合だけ、同じ役割の代替孫を 1 体起動してよい。その場合は `spawned_agents` と `failure_reason` または `residual_risks` に理由を残す。
- ユーザーが明示的に別 model を指定しない限り、孫 agent に `gpt-5.5` は使わない。
- review は最大 4 回まで行う。最大 4 回とは、初回 review と、最大 3 回の research 再出力後 review を含む。

## 保存契約

- 作成してよい正本 artifact は `output_root` 配下だけ。
- `output_root` の既定値は `report/recruitment-info`。
- 標準 path:
  - research YAML: `<output_root>/data/<target_id>.yaml`
  - review YAML: `<output_root>/reviews/<target_id>.yaml`
  - optional Markdown summary: `<output_root>/companies/<target_id>.md`
- optional Markdown summary は、親から明示された場合だけ作る。通常は research YAML と review YAML 以外を作らない。
- `target_id` は保存用 ID であり、採用対象の意味判断に使わない。
- target request の一時保存が必要な場合だけ `tmp/recruitment_info/` を使う。調査結果の正本は `report/recruitment-info/data/` に置く。
- 既存の research YAML、review YAML、trial YAML、tmp YAML は新規調査の入力、baseline、補完元として読まない。存在しても、research 孫が保存した後の検証対象としてだけ読む。

## 子の禁止事項

- web 調査をしない。
- 既存 recruitment-info 出力を読んで採用情報を補完しない。
- recruitment info YAML の本文を自分で作成、要約から再構成、fact 修正しない。
- review finding の正誤や pass / revise を自分で判断しない。verdict は review YAML の `review.verdict` だけに従う。
- 孫の出力を根拠なしに統合、削除、補完しない。
- 孫が書いた正本 YAML を形式修正以外の理由で直接編集しない。形式修正が必要な場合も、原則として research 孫に再出力を依頼する。

## 改善判定

子は review finding の内容の正誤を判断しない。継続可否だけを、保存済み review YAML の構造から機械的に判定する。

- 継続する条件:
  - review verdict が `revise` である。
  - review 回数が 4 回未満である。
  - 前回 review より high / medium finding 数が減った、または finding の category、section、message、suggested_fix の組が変化し、research 再出力で改善が進んだ可能性がある。
  - high / medium finding が同一でも、`source_quality` または `actionability` finding が公式一覧、list coverage、件数、filter、pagination、search、JS rendering の確認不足を示している。
- 中断する条件:
  - review verdict が `pass` である。
  - review 回数が 4 回に達した。
  - 2 回連続で high / medium finding 数が減らず、同一または実質同一の finding が残っている。ただし、公式一覧、list coverage、件数、filter、pagination、search、JS rendering の確認不足は、review 回数が 4 回に達するまでこの条件だけでは中断しない。
  - finding が MyPage / login / 非公開画面 / 公式公開 source 不足など、research 孫が公開情報だけでは解消できない制約を示している。
  - research 孫が同じ形式エラー、同じ schema 欠落、同じ保存失敗を繰り返す。
- 中断時は research YAML を直接直さず、status を `review_revise`、`validator_failed`、または `child_failed` にして、`failure_reason` と `residual_risks` に停止理由を入れる。

## Workflow

1. target request と保存 path を固定する。会社名、cohort、対象年度、research YAML path、review YAML path 以外の採用事実は補わない。
   - 既存 recruitment-info YAML は開かない。
   - company-analysis report path や recruitment-info YAML path を孫 prompt に渡さない。
2. `grandchild_research_prompt_template.txt` の placeholder だけを埋め、research 孫を起動する。
   - 起動時の model は `gpt-5.4-mini`、reasoning effort は `medium` にする。
3. research 孫には full YAML を `report/recruitment-info/data/<target_id>.yaml` に保存させ、chat では compact status だけを返させる。
4. research 孫の status と保存済み research YAML が同一対象か確認する。YAML が壊れている、Markdown fence が混ざる、または output contract の主要 field が欠ける場合は、同じ research 孫に再出力を求める。
5. `grandchild_review_prompt_template.txt` の placeholder だけを埋め、review 孫を起動する。
   - 起動時の model は `gpt-5.4-mini`、reasoning effort は `medium` にする。
6. review 孫には `recruitment-info-review` を使わせ、research YAML を review させ、review YAML を `report/recruitment-info/reviews/<target_id>.yaml` に保存させる。
7. review が `pass` なら保存済み data YAML を accepted とする。
8. review が `revise` なら、review findings をそのまま同じ research 孫へ渡し、research YAML の再出力を求める。
   - 新しい research 孫を起動せず、既存 research 孫に `send_input` する。
   - finding が公式一覧の展開漏れ、代表 item への丸め込み、別アクションの個別求人・個別イベントの欠落を示す場合は、「1 回の調査で公式一覧を展開し切る」ことを差し戻し文に含める。
   - finding が job-theme だけの違いによる `hiring` item の過剰分裂を示す場合は、「同一 route / 締切 / flow / 応募アクションの job-theme は `hiring[].themes` に統合する」ことを差し戻し文に含める。
   - finding が公式入口、一覧件数、filter、pagination、JS / login 制約の追跡不足を示す場合は、「公式探索 checklist の確認結果を evidence note または uncertainties に残す」ことを差し戻し文に含める。
   - finding が公式一覧、list coverage、件数、filter、pagination、search、JS rendering の確認不足を示す場合は、「公式一覧を再探索し、確認した URL、filter 条件、表示件数、総件数、page count、pagination 有無、取得できた item 数を evidence note に残す。完全網羅を公開情報だけで証明できない場合は、部分取得範囲と未確認条件を `uncertainties` に明記する」ことを差し戻し文に含める。
   - finding が `open` の根拠不足を示す場合は、「公開 page の存在だけで `open` にせず、公式の受付中根拠がなければ `mypage_required`、`open_likely`、`unknown` にする」ことを差し戻し文に含める。
   - finding が複数日程の `/` 区切り、schema 欠落、status 根拠不整合などの output contract 違反を示す場合は、review finding を引用して同じ保存 path へ再出力させる。
9. 再出力後、同じ review 孫へ `send_input` して再 review する。
10. review が `pass` になるまで、または **改善判定** の中断条件に当たるまで、手順 8-9 を繰り返す。
11. 中断条件に当たった場合、子は修正せず `review_revise` として終了する。

## 子 Result

compact status YAML を返す。full research YAML は `report/recruitment-info/data/<target_id>.yaml` に保存済みであること。

必須 field:

- `target_request`
- `status`: `accepted`、`validator_failed`、`review_revise`、`review_failed`、`child_failed`
- `research_yaml_path`
- `review_yaml_path`
- `failure_reason`
- `residual_risks`
- `review_rounds`
- `revision_rounds`
- `stop_reason`
- `commands_run`
- `spawned_agents`

## 完了条件

- accepted target では、research YAML と必要な review YAML が `report/recruitment-info` 配下に保存されている。
- accepted target では、調査と review が孫 agent の出力に由来しており、子自身が採用 fact を作成していない。
- accepted でない target では、status、failure reason、次に必要な確認が compact status に入っている。
