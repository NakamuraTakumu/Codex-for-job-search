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
  - 孫調査エージェントへ渡す prompt template。fixed input と handoff path だけを置き、調査・評価・schema 契約は `company-analysis` skill を正本にする。
  - placeholder だけを埋める。
- **孫 review prompt**: `review_prompt_template.txt`
  - 孫レビューエージェントへ渡す prompt template。review input bundle path だけを埋める。

## 実行境界

- scope 固定前は `references/target_scope.md` を正本にする。
- fixed input 作成後の参照境界、読み取り範囲、孫 agent 管理、受理条件、保存先、失敗時対応、子 result 契約は `references/acceptance_pipeline.md` を正本にする。
- 子は孫調査用の `company-analysis` skill、孫 review 用の `company-analysis-review` skill、およびそれらの references を直接読まない。孫には prompt template 経由で必要な入力だけを渡す。

## 入力契約

- target request は、ユーザーがチャットで渡した内容を親が転記したものとして扱う。
- 必須入力:
  - `company_name`: ユーザーが指定した会社名。
  - `requested_role`: ユーザーが指定した職種、職種ファミリー、または応募意図。
  - `applicant_graduation_cohort`: 親がチャットから固定した応募者の卒業・修了見込み cohort。
  - `run_root`: 親が割り当てる file 生成先 root directory。
- 任意入力:
  - `run_id`: 親が割り当てる `[a-z0-9_]+` の保存・照合用 ID。未指定なら子が UUID を `[a-z0-9_]+` に正規化して割り当てる。
- 親から fixed scope が渡されても正本にしない。子は `references/target_scope.md` に従って scope を固定する。
- target request に含まれない値は、親の意図として補完せず、子が調査して固定する。ただし `applicant_graduation_cohort` は親から受け継ぐ必須値であり、子は別 cohort へ置き換えない。
- company-analysis YAML schema 互換で `slug` が必要な場合は、`run_id` を `[a-z0-9_]+` に正規化した機械的識別子を使い、表示用・意味的 slug として扱わない。

## 副作用契約

- 子が作成してよい artifact は `run_root` 配下だけとし、標準 artifact path、保存先、既存 artifact の扱い、共有 final path の禁止は `references/acceptance_pipeline.md` を正本にする。
- 子が直接行う処理は、scope 固定、孫 agent handoff、受理、validation、review、rendering、保存など、判断内容に影響しないオーケストレーションに限る。

## Model 契約

- 子オーケストラ、孫調査、孫 review は、親 prompt の model settings を使う。未指定時の標準は `gpt-5.4-mini`、`reasoning_effort: medium` とする。
- 孫 spawn 時の明示と記録は `references/acceptance_pipeline.md` に従う。

## Workflow

1. **scope 固定**:
   - `references/target_scope.md` を読み、会社実体、応募単位、`role_family`、働く場として評価する entity を固定する。
   - `scope.target_application_unit` は公式応募単位に準拠し、`requested_role` が公式単位より細かい志向の場合は `scope.ambiguity_note` に残す。
   - `applicant_graduation_cohort` は target request の値を fixed input YAML に引き継ぐ。
   - 公式 route が複数あり固定不能な場合は、分析へ進まず `status: revise_scope` の result YAML を返す。
   - fixed input YAML を `run_root` 由来の標準 `child_inputs_dir` へ保存する。

2. **受理 pipeline**:
   - `run_root` から標準 artifact path を導出し、fixed input YAML と handoff path を作る。
   - 以後は `references/acceptance_pipeline.md` に従って孫調査、intake、validation、review、rendering、保存、result YAML 返却を行う。

## 結果契約

子 result の schema、`status` の意味、accepted 条件、`spawned_agents`、`run_models` は `references/acceptance_pipeline.md` の **子 Result** を正本にする。

## 完了条件

- accepted target では、validator、採用済み孫 review agent による内容 review、rendering、保存後 validation が完了している。
- accepted でない target では、status、failure reason、次に必要なユーザー判断が result YAML に入っている。
