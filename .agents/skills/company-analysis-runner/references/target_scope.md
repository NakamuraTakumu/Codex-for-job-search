# Target Scope

## 用途

- `company-analysis-runner` が分析子を起動する前に対象 scope を固定するための規則。
- 会社名だけ、複数会社、近接法人、`scope.role_family`、応募 route、応募可否が曖昧な場合に読む。

## 固定する値

- `company_name`
- `survey_date`
- `slug`
- `scope.user_label`
- `scope.target_application_unit`
- `scope.hiring_entity_name`
- `scope.role_family`
- `scope.alternative_application_units`
- `scope.stability_entity_name`
- 必要時のみ `scope.ambiguity_note`

## 複数対象の Scope Manifest

- 複数の target を分析する場合、分析子起動前に全 target の固定 scope を Markdown に出力する。
- default path は `document/<run_slug>_target_scope.md`。
- manifest は、分析対象としない候補も含めて `status` で分ける。
  - `ready_for_analysis`
  - `needs_scope_check`
  - `not_application_unit`
- 少なくとも次の列を持つ table にする。
  - `status`
  - `slug`
  - `company_name`
  - `target_application_unit`
  - `hiring_entity_name`
  - `role_family`
  - `stability_entity_name`
  - `ambiguity_note`
- `target_application_unit` と `hiring_entity_name` が未固定の候補は `ready_for_analysis` にしない。
- manifest を保存するまでは、分析子を起動しない。

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
- 独立採用する実体が複数ある場合、親が自動で全件分析しない。
- 候補と採用状況を要約し、主分析対象をユーザーに選ばせる。
- 公式の会社実体が曖昧で近接法人も確認すべき場合、候補をおおむね 3-5 社に絞り、それぞれを別の `target_application_unit` 候補として扱う。
- 複数会社が同時に与えられた場合、各社を途中で止めず、全社について子会社、近接法人、独立採用 route を一通り確認してから対象確認へ進む。

## 応募単位

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

- 複数の `scope.role_family` を分析するのは、ユーザーが明示的に求めた場合、比較が目的の場合、または親が別 target として明示的に追加する場合だけにする。
- 複数の `scope.role_family` を分析する場合、`scope.role_family` ごとではなく、実際の `scope.target_application_unit` ごとに別 slug、別分析子、別 YAML / Markdown pair として扱う。
- 同じ分析子に複数の `scope.target_application_unit` を順番に渡さない。

## 安定性 Entity

- `scope.hiring_entity_name` は、応募、給与、採用制度、配属、応募経路を見る entity。
- `scope.stability_entity_name` は、売上、上場有無、IR、親会社支援、グループ支援などの安定性を見る entity。
- 親会社やグループ会社の数値を使う場合、採用実体の数値として書かない。
- `scope.hiring_entity_name` と `scope.stability_entity_name` が違う場合、summary と stability で採用実体と安定性根拠 entity の違いを明示する。

## Slug

- 各対象の `slug` は親が決める。
- default は、曖昧でない範囲で最短の安定した対象ベース slug とする。
- 例: `japan_ibm_researcher`, `ntt_data_engineer`
- default では日付を付けない。
- 日付 suffix は、同じ directory 内の複数有効 run を区別する、衝突を避ける、または並列 test 成果物を明示的に残す必要がある場合だけ付ける。
- 複数対象がある場合、`<company_slug>_<target_suffix>` のように決定的に分け、同一 run 内で同じ slug を再利用しない。
