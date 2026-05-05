# 出力契約リファレンス

このファイルは、調査、証拠整理、採点、結論が固まった後にだけ読む。出力 schema を先に埋めるための調査 checklist として使ってはいけない。

## 出力原則

- **返却形式**: 単一の YAML object だけを返す。
- **禁止形式**: Markdown、commentary、見出し、数式説明、総合点、補正後総合点、`run_metadata` を出力 YAML に含めない。
- **正本 schema**: このファイルの **YAML schema** を唯一の正本とする。別 template file は使わない。
- **未充足時の扱い**: schema の項目を証拠で支えられないと分かった場合、追加調査が未実施なら YAML を確定する前に調査と証拠整理へ戻る。追加調査後も欠損が残る場合は `null` とし、欠損理由を `evaluation` または `summary.concerns` に残す。
- **自然言語**: `scope.ambiguity_note`、各 section の文章項目、`summary.*` は通常日本語で書く。固有名詞、学位名、公開職種名、公式用語だけ必要最小限で原語を残してよい。
- **欠損値**: 構造化された値の欠損は型にかかわらず `null` を使う。文字列 `unknown`、日本語 placeholder、非公開 numeric value の `0` は使わない。

## Field Reference

すべての key は必須。構造化された欠損値は `null`、空 list が意味を持つ field は `[]` を使う。

### Top-Level Fields

- **`version`**:
  - **type**: `int`
  - **value**: 常に `1`。
- **`company_name`**:
  - **type**: `str`
  - **meaning**: 子オーケストラが固定した会社名。
- **`survey_date`**:
  - **type**: `YYYY-MM-DD`
  - **meaning**: 調査日。
- **`slug`**:
  - **type**: `[a-z0-9_]+`
  - **meaning**: 子オーケストラが指定した schema 用識別子。`run_id` 由来の場合は保存・照合用であり、応募単位や評価対象の意味を持たない。
- **`applicant_graduation_cohort`**:
  - **type**: `str`
  - **meaning**: 応募者の卒業・修了見込み cohort。
  - **constraint**: 子オーケストラが受け継いだ値を使う。通常は `2028卒` のような4桁年表記。採用年度や `scope.role_family` と混同しない。
- **`scope`**:
  - **type**: `map`
  - **meaning**: 子オーケストラが固定した評価対象。
  - **constraint**: 公開情報とずれても対象をすり替えない。不一致や曖昧さは `scope.ambiguity_note` に記録する。
- **`fact_layer`**:
  - **type**: `map`
  - **meaning**: 公式 / 非公式に分けた構造化 facts。
  - **placement**: 月額初任給、平均年収、3年以内離職率、平均勤続年数、平均年齢、残業、休日、リモート方針、採用導線、応募経路など、機械的に扱いやすい数値・制度 facts だけを入れる。
- **`sections`**:
  - **type**: `map`
  - **meaning**: 6 観点の evidence と評価。
  - **placement**: `fact_layer` の意味づけ、補完的推定、根拠の強弱、評価判断を書く。
- **`summary`**:
  - **type**: `map`
  - **meaning**: 全体結論、向き不向き、懸念。
- **`sources`**:
  - **type**: `list[map]`
  - **meaning**: 実際に証拠として使った URL。
  - **constraint**: 証拠として使わなかった URL は列挙しない。

### `scope` Fields

- **`user_label`**:
  - **type**: `str`
  - **meaning**: 子オーケストラが固定した表示名。
- **`target_application_unit`**:
  - **type**: `str`
  - **meaning**: 応募者が到達したい採用ルート、職種トラック、または application unit。
  - **constraint**: 企業名だけで埋めない。
- **`hiring_entity_name`**:
  - **type**: `str`
  - **meaning**: 採用を行う entity。給与、採用制度、応募経路の確認ではこの entity を優先する。
- **`role_family`**:
  - **type**: `researcher | research_engineer | engineer | consultant | generalist | other`
  - **meaning**: 職種ファミリー。
  - **constraint**: 年度、卒年 cohort、新卒 / 中途区分ではない。
- **`alternative_application_units`**:
  - **type**: `list[str]`
  - **meaning**: `hiring_entity_name` の entity にある他の採用ルート、職種トラック、または application unit。
  - **missing**: 候補がない場合は `[]`。
- **`workplace_entity_name`**:
  - **type**: `str`
  - **meaning**: 実際に働く場として主に評価する entity。
- **`ambiguity_note`**:
  - **type**: `str`
  - **meaning**: 公開情報との不一致、対象の曖昧さ、採用時期の不確実性など。
  - **constraint**: 大きな不一致がない場合も、その旨を明示する。

### `fact_layer.official` And `fact_layer.unofficial` Fields

同じ field set を `official` と `unofficial` の両方に置く。`official` / `unofficial` は source tier だけで分け、相互に上書きしない。公式 source 由来の候補値は `fact_layer.official`、非公式 source 由来の候補値は `fact_layer.unofficial` に入れる。どちらも、低信頼、近接職種、年度差、共通制度、別採用年度、近い応募単位、source 上の推定値を、対象との差を理由に落とさない。

#### Cohort And Recency

- **`applicant_graduation_cohort`**: 応募者条件。`fact_layer` の年度フィルタではない。
- **優先順位**: 調査時点で最も新しく、固定 scope に最も近い fact を優先する。
- **直近年度・近接職種情報**: cohort 向け情報が未公開の場合、直近年度の同一応募単位、同一採用主体、共通制度、近接職種、または近い応募単位として扱える情報を `fact_layer` に入れる。公式情報も非公式情報も、不確実性を理由に落とさない。
- **年度差の記録**: `fact_layer` に source year、適用 cohort、scope distance などの年度メタデータを追加しない。cohort 向け未公開、直近年度情報の利用、適用不確実性は `scope.ambiguity_note`、該当 section、または `summary.concerns` に書く。

- **`starting_salary_yen`**:
  - **type**: `int | null`
  - **meaning**: 評価対象に最も近い月額初任給候補。
  - **constraint**: 直接対応を優先する。直接対応がない場合は、共通給与、直近年度、近接職種、近い応募単位の月額初任給候補を入れ、差分は本文に書く。
- **`starting_salary_bachelor_yen`**:
  - **type**: `int | null`
  - **meaning**: 学士の月額初任給。
  - **constraint**: 月額で示されている値だけを入れる。年額換算や推定年収を入れない。
- **`starting_salary_master_yen`**:
  - **type**: `int | null`
  - **meaning**: 修士の月額初任給。
  - **constraint**: 月額で示されている値だけを入れる。年額換算や推定年収を入れない。
- **`starting_salary_doctor_yen`**:
  - **type**: `int | null`
  - **meaning**: 博士の月額初任給。
  - **constraint**: 月額で示されている値だけを入れる。年額換算や推定年収を入れない。
- **`has_target_job_hiring_track`**:
  - **type**: `bool | null`
  - **meaning**: 評価対象に対する採用導線が存在するか。
  - **constraint**: 区分自体があり、当年採用が未定でも `true` は可。不確実性は `scope.ambiguity_note` または `summary.concerns` に残す。
- **`application_route`**:
  - **type**: `direct | parent_company | group_company | null`
  - **meaning**: 応募者が `target_application_unit` に到達する経路。
  - **missing**: 公開情報で確認不能なら `null`。
- **`average_annual_income_yen`**:
  - **type**: `int | null`
  - **meaning**: 年額の平均年収。
  - **constraint**: 初任給、reference salary、想定年収を入れない。複数候補がある場合は、採用主体に最も近い最新の公式値、特に法定開示を優先する。
- **`new_graduate_turnover_rate_within_3_years_percent`**:
  - **type**: `float | int | null`
  - **meaning**: 新卒 cohort の3年以内離職率。
  - **constraint**: 全社平均離職率や自己推定値を代入しない。3年後定着率しかない場合は自分で換算せず、`sections.stability` で説明する。
- **`average_tenure_years`**:
  - **type**: `float | int | null`
  - **meaning**: 平均勤続年数。
  - **constraint**: 特になし。
- **`average_age_years`**:
  - **type**: `float | int | null`
  - **meaning**: 平均年齢。
  - **constraint**: 特になし。
- **`average_overtime_hours_per_month`**:
  - **type**: `float | int | null`
  - **meaning**: 月平均残業時間。
  - **constraint**: みなし残業や固定残業時間を代入しない。
- **`annual_holidays_days`**:
  - **type**: `int | null`
  - **meaning**: 明示された年間休日数。
  - **constraint**: 週休や休暇制度から自分で合算しない。
- **`remote_work_policy`**:
  - **type**: `full | hybrid | limited | none | null`
  - **meaning**: 評価対象または採用主体に対する広いリモート勤務方針。
  - **constraint**: 条件付きのみなら `limited`。個人の体験談や単一チームの例だけでは埋めない。

### `sections` Fields

`sections` は `phd_value`、`role_fit`、`rd_env`、`compensation`、`hiring_process`、`stability` の 6 key を必ず持つ。各 section は同じ field set を持つ。

- **`score`**:
  - **type**: `float`
  - **meaning**: section の単一最終 score。
  - **constraint**: `1.0` 以上 `5.0` 以下、`0.1` 刻み。総合点は書かない。
- **`facts_official`**:
  - **type**: `str`
  - **meaning**: 評価語を含まない公式 / 一次情報のまとめ。
  - **source**: 公式情報だけ。
  - **constraint**: 非公式情報、解釈、評価判断を混ぜない。
- **`facts_unofficial`**:
  - **type**: `str`
  - **meaning**: 非公式 facts / observations、不発理由、信頼可能性に関する留保。
  - **source**: 非公式情報だけ。
  - **constraint**: 値を支えなかった情報の系統、軽い食い違い、信頼可能性の留保も、後で再判断できるよう残す。非公式 source を検索したが証拠に使わない場合、確認した source family と不発理由をここか `summary.concerns` に残す。
- **`evaluation`**:
  - **type**: `str`
  - **meaning**: 公式 / 非公式 facts を踏まえた最終判断。
  - **constraint**: 似た点を多重投票のように数えない。

### `summary` Fields

- **`conclusion`**:
  - **type**: `str`
  - **meaning**: 評価対象に対する短い結論。
  - **constraint**: 通常 2-4 文。
- **`final_comment`**:
  - **type**: `str`
  - **meaning**: 最終所見。
  - **constraint**: 1 文。
- **`suitable_for`**:
  - **type**: `list[str]`
  - **meaning**: 向いている人。
- **`not_suitable_for`**:
  - **type**: `list[str]`
  - **meaning**: 向いていない人。
- **`concerns`**:
  - **type**: `list[str]`
  - **meaning**: 主な懸念、未解消の曖昧さ、重要な欠損。
  - **placement**: section に閉じない補完的推定、根拠の弱さ、非公式 source family の不発理由を書いてよい。
  - **official source shortage**: 公式 source が 4 件未満、または `recruit` と `company|ir` の必須 kind を満たせない場合は、追加調査後に `公式source不足:` で始まる項目を 1 つ以上置き、不足した件数または kind と、その原因を書く。

### `sources[]` Fields
- **`label`**:
  - **type**: `str`
  - **meaning**: 表示ラベル。
  - **constraint**: 通常は日本語。自然な日本語訳が不自然な場合だけ英語を残す。
- **`url`**:
  - **type**: `http(s) URL`
  - **meaning**: 証拠として使ったページの URL。
- **`tier`**:
  - **type**: `official | unofficial`
  - **meaning**: 情報源 tier。
- **`kind`**:
  - **type**: **Source Kind Enum** の値。
  - **meaning**: 情報源の種類。

## YAML Schema

下の schema は構造、必須 key、型、enum だけを示す。field の意味と制約は **Field Reference** を正とする。最終 YAML では placeholder を消し、YAML alias を使わず各 section を展開する。

```yaml
version: 1
company_name: "<str>"
survey_date: "<YYYY-MM-DD>"
slug: "<[a-z0-9_]+>"
applicant_graduation_cohort: "<str>"
scope:
  user_label: "<str>"
  target_application_unit: "<str>"
  hiring_entity_name: "<str>"
  role_family: "<researcher|research_engineer|engineer|consultant|generalist|other>"
  alternative_application_units:
    - "<str>"
  workplace_entity_name: "<str>"
  ambiguity_note: "<str>"
fact_layer:
  official:
    starting_salary_yen: "<int|null>"
    starting_salary_bachelor_yen: "<int|null>"
    starting_salary_master_yen: "<int|null>"
    starting_salary_doctor_yen: "<int|null>"
    has_target_job_hiring_track: "<bool|null>"
    application_route: "<direct|parent_company|group_company|null>"
    average_annual_income_yen: "<int|null>"
    new_graduate_turnover_rate_within_3_years_percent: "<float|int|null>"
    average_tenure_years: "<float|int|null>"
    average_age_years: "<float|int|null>"
    average_overtime_hours_per_month: "<float|int|null>"
    annual_holidays_days: "<int|null>"
    remote_work_policy: "<full|hybrid|limited|none|null>"
  unofficial:
    starting_salary_yen: "<int|null>"
    starting_salary_bachelor_yen: "<int|null>"
    starting_salary_master_yen: "<int|null>"
    starting_salary_doctor_yen: "<int|null>"
    has_target_job_hiring_track: "<bool|null>"
    application_route: "<direct|parent_company|group_company|null>"
    average_annual_income_yen: "<int|null>"
    new_graduate_turnover_rate_within_3_years_percent: "<float|int|null>"
    average_tenure_years: "<float|int|null>"
    average_age_years: "<float|int|null>"
    average_overtime_hours_per_month: "<float|int|null>"
    annual_holidays_days: "<int|null>"
    remote_work_policy: "<full|hybrid|limited|none|null>"
sections:
  phd_value:
    score: "<float>"
    facts_official: "<str>"
    facts_unofficial: "<str>"
    evaluation: "<str>"
  role_fit:
    score: "<float>"
    facts_official: "<str>"
    facts_unofficial: "<str>"
    evaluation: "<str>"
  rd_env:
    score: "<float>"
    facts_official: "<str>"
    facts_unofficial: "<str>"
    evaluation: "<str>"
  compensation:
    score: "<float>"
    facts_official: "<str>"
    facts_unofficial: "<str>"
    evaluation: "<str>"
  hiring_process:
    score: "<float>"
    facts_official: "<str>"
    facts_unofficial: "<str>"
    evaluation: "<str>"
  stability:
    score: "<float>"
    facts_official: "<str>"
    facts_unofficial: "<str>"
    evaluation: "<str>"
summary:
  conclusion: "<str>"
  final_comment: "<str>"
  suitable_for:
    - "<str>"
  not_suitable_for:
    - "<str>"
  concerns:
    - "<str>"
sources:
  - label: "<str>"
    url: "<http(s) URL>"
    tier: "<official|unofficial>"
    kind: "<source kind>"
```

## Source Kind Enum

- **official**: `recruit`、`faq`、`benefits`、`company`、`ir`、`research`、`business`、`other`
- **unofficial**: `review_site`、`forum`、`career_site`、`blog`、`tech_blog`、`profile`、`university`、`event`、`presentation`、`oss`、`github`、`personal_site`、`other`

## 返却前 Checklist

- 単一の YAML object だけを返している。
- `version` が `1`。
- `scope`、`fact_layer.official`、`fact_layer.unofficial`、6 つの section が必須 key をすべて含む。
- 不明な構造化値に `null` を使い、`unknown`、日本語 placeholder、非公開 numeric value の `0` を使っていない。
- `facts_official` と `facts_unofficial`、`fact_layer.official` と `fact_layer.unofficial` が分離されている。
- 各 section に `score` があり、総合点や補正後総合点を書いていない。
- 初任給候補が見つかっているのに、対応する `starting_salary_yen` または `starting_salary_*_yen` を不必要に `null` のままにしていない。
- cohort 向け情報が未公開でも、直近年度の同一応募単位、同一採用主体、共通制度、または近接職種として扱える情報を探し、structured fact を不必要に `null` のままにしていない。
- `../SKILL.md` の **非公式情報** 節に照らして記録対象となる非公式データを、`fact_layer.unofficial` や `facts_unofficial` から落としていない。
- 重要な欠損が残る場合、追加調査と非公式情報調査を少なくとも一度試みている。
- 典型的な非公式 source family を検索し、証拠に使わない場合は不発理由を記録している。
- 公式 source が 4 件未満、または `recruit` と `company|ir` の必須 kind を満たせない場合、`summary.concerns` に `公式source不足:` で始まる不足原因を書いている。
- 公式 source に候補値がある場合、対象年度・対象職種への直接一致がなくても `fact_layer.official` に入れている。
- 公式 source に候補値がなく、自己計算または根拠なし推定しかできない場合、`fact_layer.official` の該当 field を `null` のままにしている。
- 多くの `null` 値が残る場合、その深刻さを `scope.ambiguity_note`、section の `evaluation`、または `summary.concerns` に明示している。
