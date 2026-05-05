# Target Scope

## 用途

- `company-analysis-child-orchestrator` が孫調査エージェントを起動する前に対象 scope を固定するための規則。
- 会社名だけ、複数会社、近接法人、`scope.role_family`、応募 route、応募可否が曖昧な場合に読む。

## 固定する値

孫調査エージェント起動前に、対象ごとに次の値を固定する。値が未確定の候補は `ready_for_analysis` にしない。

- `company_name`
- `survey_date`
- `applicant_graduation_cohort`
- `scope.user_label`
- `scope.target_application_unit`
- `scope.hiring_entity_name`
- `scope.role_family`
- `scope.alternative_application_units`
- `scope.workplace_entity_name`
- `scope.ambiguity_note`: 大きな曖昧性がない場合もその旨を書く。

## 識別子

- `run_id` は親または子が割り当てる `[a-z0-9_]+` の保存・照合用 ID であり、scope 固定や評価判断に使わない。
- company-analysis YAML schema 互換で `slug` が必要な場合は、`run_id` を `[a-z0-9_]+` に正規化した機械的識別子を使う。
- `slug` を表示用名、応募単位名、重複検出キー、保存先設計の根拠にしない。

## 複数対象の Scope Manifest

- scope manifest は、複数 target の scope 固定を監査・比較するための任意 artifact とする。
- 単一 target を処理する通常の子オーケストラ workflow では作らない。
- 複数 target の scope 監査をユーザーが明示した場合だけ、全 target の固定 scope を Markdown に出力する。
- default path は `tmp/company_analysis/runs/<run_id>/target_scope.md`。
- scope manifest を reusable note として残す場合だけ `document/` に保存し、`report/company_analysis/` に置かない。
- manifest は、分析対象としない候補も含めて `status` で分ける。
  - `ready_for_analysis`
  - `needs_scope_check`
  - `not_application_unit`
- 少なくとも次の列を持つ table にする。
  - `status`
  - `run_id`
  - `company_name`
  - `applicant_graduation_cohort`
  - `target_application_unit`
  - `hiring_entity_name`
  - `role_family`
  - `workplace_entity_name`
  - `ambiguity_note`
- `target_application_unit` と `hiring_entity_name` が未固定の候補は `ready_for_analysis` にしない。
- scope manifest を作る task では、manifest を保存するまでは分析子を起動しない。

## 応募者 Cohort

- `applicant_graduation_cohort` は応募者の卒業・修了見込み cohort を表す。
- 値は `2028卒` のような4桁年表記を使う。
- `applicant_graduation_cohort` は親から受け継いだ target request の値を使う。
- 子オーケストラは `applicant_graduation_cohort` を別 cohort へ置き換えない。
- `applicant_graduation_cohort` を `scope.role_family`、採用年度、雇用区分に混ぜない。

## Role Family

- `scope.role_family` は次のいずれかにする。
  - `researcher`
  - `research_engineer`
  - `engineer`
  - `consultant`
  - `generalist`
  - `other`
- 採用年度、卒業年度、雇用区分、cohort を `scope.role_family` に入れない。
- `scope.role_family` は `scope.target_application_unit` から見た職種ファミリーを表す。
- 同じ会社に複数の `scope.role_family` 候補がある場合、候補ごとに別の `scope.target_application_unit` として固定する。

## 会社実体

- ユーザーが会社名だけを与えた場合でも、全社評価に広げない。
- 主要子会社や近接法人を先に確認し、それぞれが独立した新卒相当採用 route を持つかを見る。
- 独立採用する実体が複数あり target request だけでは固定できない場合、子は `status: revise_scope` で候補と採用状況を返す。
- ユーザーが明示的に複数対象の分析を求めた場合だけ、複数の `ready_for_analysis` target として固定する。
- 公式の会社実体が曖昧で近接法人も確認すべき場合、候補をおおむね 3-5 社に絞り、それぞれを別の `target_application_unit` 候補として扱う。
- 複数会社が同時に与えられた場合、各社を途中で止めず、全社について子会社、近接法人、独立採用 route を一通り確認してから対象確認へ進む。

## 応募単位

- `scope.target_application_unit` は公式応募単位に準拠する。
- `requested_role` が公式応募単位より細かい志向、希望配属、研究テーマ、通称、比較用 slug の場合、その文字列を `scope.target_application_unit` にしない。
- 公式応募単位より細かい希望は `scope.ambiguity_note` と分析本文の留保に残す。
- 公式応募単位に準拠すると `scope.role_family` が変わる場合は、公式応募単位から見た `scope.role_family` を採用する。
- 公式応募単位が複数あり、`requested_role` だけでは 1 つに決められない場合は、子は `status: revise_scope` で候補を返す。
- 想定候補者が博士課程在籍者、または明確な職歴のない博士新卒・既卒に近い場合は、新卒相当 route を優先する。
- 経験者採用は、新卒 route が存在しない、明確に不適用、または明示的に不適切な場合だけ使う。
- 各 `scope.role_family` の有無は、公式の新卒相当応募 route があるかで判断する。
- ラボ紹介、技術 PR、役割としてあり得そう、だけでは公式応募 route とみなさない。

## Role Family 別 Route

- `researcher`
  - 公式の研究職、研究員、Research Scientist route がある場合に使う。
  - 単一対象の default は、公式に存在する最も直接的な `researcher` route にする。
  - 当年採用が未定、停止中、終了済み、または情報不足でも、他の `scope.role_family` へ自動で置き換えない。
  - 応募可否が弱い場合は、`researcher` route を固定したまま `scope.ambiguity_note`、`summary.concerns`、`hiring_process` に不確実性として残す。
  - 公式に独立した `researcher` 応募単位がない場合、広い公式応募単位内の研究志向だけを理由に `researcher` として固定しない。
- `research_engineer`
  - 公式の R&D 職、AI/Data Research Scientist、研究と実装の中間 route がある場合に使う。
  - `researcher` route が公式に存在しない、またはユーザーが研究開発・R&D・実装寄り研究を明示した場合の default 候補にする。
  - `researcher` route の代替として黙って固定しない。別の `scope.target_application_unit` として扱う。
- `engineer`
  - 公式の SWE、SE、開発、アプリケーション、セキュリティなどの engineering route がある場合に使う。
  - default にするのは、`researcher` / `research_engineer` route が公式に見つからない場合、またはユーザーが engineering 系を明示した場合だけ。
- `consultant`
  - 公式の consultant、technical consultant、cyber consultant などの route がある場合に使う。
  - default にするのは、ユーザーが consulting 系を明示した場合、または研究・研究開発・engineering 系 route が公式に見つからず、候補者意図とも整合する場合だけ。
- `generalist`
  - 技術系総合職など、入社時点で複数職種に分かれ得る応募単位に使う。
  - 専門 route が存在する場合、`generalist` を専門 route の代替として黙って固定しない。
- `other`
  - 上記に安全に分類できない応募単位にだけ使う。
  - 使う場合は `scope.ambiguity_note` に分類不能な理由を残す。

## 複数 Role Family

- 複数の `scope.role_family` を分析するのは、ユーザーが公式応募単位ごとの比較を明示した場合、比較が目的の場合、または runner が別 target request として明示的に追加した場合だけにする。
- 複数の `scope.role_family` を分析する場合、`scope.role_family` ごとではなく、実際の `scope.target_application_unit` ごとに別 `run_id`、別分析子、別 YAML / Markdown pair として扱う。
- 同じ分析子に複数の `scope.target_application_unit` を順番に渡さない。

## Workplace Entity

- `scope.hiring_entity_name` は、応募、給与、採用制度、配属、応募経路を見る entity。
- `scope.workplace_entity_name` は、実際に働く場として主に評価する entity。配属先会社、事業会社、研究所運営会社などを含む。
- 安定性評価は、採用実体と働く場の違いを明示したうえで `scope.workplace_entity_name` を中心に見る。
- 親会社やグループ会社の数値を使う場合、採用実体の数値として書かない。
- `scope.hiring_entity_name` と `scope.workplace_entity_name` が違う場合、summary と stability で採用実体と働く場として評価する entity の違いを明示する。
