---
name: company-analysis
description: 旧帝大の博士課程人材向けに企業を評価する親エージェント用スキル。親が評価対象を固定し、子エージェントは6項目を事実ベースで採点して、検証可能な YAML を返す。
---

# Purpose
- このスキルは、親エージェントが会社分析を子エージェントへ委譲するときに使う
- 子エージェントの返却物は Markdown ではなく YAML とする
- Markdown の描画、保存、最終ファイル化は親エージェントまたはスクリプトが担当する

# Reader assumptions
- 想定読者は、旧帝大の博士課程人材またはそれに準ずる研究志向の候補者である
- 関心領域の既定値は、機械学習、数理・抽象理論、形式化、プログラミング言語理論、ソフトウェア工学、アルゴリズム実装、GPU / 型システムなどの計算機実装、研究成果のソフトウェア化・社会実装とする
- 分野適合だけで加点しない。博士の専門性が実際にどう評価されるかを優先して見る

# Core principles
- 企業紹介ではなく、就職先としての実態を評価する
- 事実と評価を分ける
- 可能な限り公式情報を優先する
- 可能な限り多くの公式ソースを使う。ただし同じ内容の重複ページを機械的に増やすのではなく、募集要項、FAQ、福利厚生、会社概要、IR、研究所・技術組織、事業・技術紹介など、種類の異なる根拠を広く集める
- 同じ内容を複数項目で二重計上しない
- 大手感やブランドでは加点しない
- 研究能力と関係の薄い選考負担は明確に減点対象とする

# Research method
- まず公式情報で骨格を取る。優先順は、採用ページ、募集要項、FAQ、福利厚生・働き方、会社概要、IR / 有価証券報告書、研究所・技術組織・技術紹介とする
- 採用広報と事業実態を分けて見る。採用ページやイベント説明だけでなく、IR、法定開示、研究所ページ、技術発表、事業紹介で裏取りする
- 比較軸を固定して集める。少なくとも、採用対象、職種、初期配属、博士評価、初任給、平均年収、働き方、選考負担、研究/技術環境、企業基盤を意識して読む
- 良い情報だけでなく減点材料も探す。配属不確定、博士優遇なし、選考負担、リモート制限、赤字、研究所と採用枠のずれなどを明示的に確認する
- 口コミや体験談は補助にとどめ、まず一次情報で判断の土台を作る
- 1ページで全項目を埋めず、可能な限り異なる種類の公式ソースから cross-check する

# Evaluation criteria

## 1. phd_value
- 博士採用枠、学位別給与、学士・修士・博士の初任給差、博士向け役割、博士採用実績、専門性評価の有無を見る
- 職務内容そのものの面白さや研究テーマ適合ではなく、博士号・研究実績が制度上どう評価されるかを見る
- 見ないもの: 研究所の規模、R&D テーマの豊富さ、初期配属の具体性
- 高評価: 博士課程を明示的に対象とし、学位差や研究実績評価が制度や要項で確認できる
- 低評価: 博士応募は可能でも、博士特有の扱いや研究実績評価がほとんど確認できない

## 2. role_fit
- 初期配属、ジョブ型か総合職か、候補者の専門分野との接続、配属確約、仕事内容の具体性を見る
- 組織全体の研究開発基盤ではなく、固定した職務と初期配属に候補者の専門分野がどう接続するかを見る
- 見ないもの: 組織全体の論文数、研究所全体の対外実績、会社全体の R&D 投資規模
- 高評価: 初期配属と仕事内容が具体的で、専門分野との接続が強く、配属確度も高い
- 低評価: 仕事内容や配属候補が広すぎて、専門分野が実際の職務へどう乗るか読みづらい

## 3. rd_env
- 研究所や R&D 部門、論文・特許・学会・OSS、理論と実装の往復可能性を見る
- 固定職務の配属確度ではなく、その会社・組織に存在する研究開発基盤の厚みを見る
- 見ないもの: 自分の初期配属の確度、職種名の研究っぽさ、個別ポジションの魅力
- 高評価: 研究所・R&D 部門、論文・特許・学会・OSS・外部連携・技術資産化が複数確認できる
- 低評価: 技術組織はあるが、研究開発基盤や対外実績の公開確認が弱い

## 4. compensation
- 初任給、平均年収、学位差、賞与、福利厚生、住宅補助、勤務地、働き方、裁量を見る

## 5. hiring_process
- SPI 等の有無、テスト数、ES 負荷、面接回数、専門性を直接見てくれるかを見る
- 高評価: 選考負担が軽く、研究能力や専門性を直接評価し、準備コストに対して納得感が高い
- 低評価: SPI などの一般適性検査が重く、就活慣れや generic な足切りを強く要求し、専門性と無関係な負担が大きい

## 6. stability
- 売上、従業員数、資本金、上場、親会社・グループ基盤、事業継続性を見る
- 主軸ではなく補助項目として扱う

# Scoring
- 各項目は `1.0` 以上 `5.0` 以下の `0.1` 刻みで採点する
- 子エージェントは各項目の `score` まで返す
- 総合評価と補正後評価の計算は、親エージェントまたは Python スクリプトが行う
- 重み付き集計の正本は Python 実装に従う

# YAML output contract
- 返却物は単一の YAML オブジェクトだけにする
- Markdown、コードフェンス、前置き説明、後置きコメントを混ぜない
- 総合点、補正後総合点、Markdown 見出し、数式評価本文は YAML に入れない

## Schema
```text
version: 1
company_name: str
survey_date: YYYY-MM-DD
slug: [a-z0-9_]+
scope: map
sections: map
adjustment: map
summary: map
sources: list[{label: str, url: http(s) URL}]
run_metadata: optional map set by parent

scope.user_label: str
scope.evaluation_target: str
scope.hiring_entity: str
scope.job_type: str
scope.placement_candidates: list[str]
scope.stability_entity: str
scope.ambiguity_note: str

sections.phd_value: section
sections.role_fit: section
sections.rd_env: section
sections.compensation: section_with_structured
sections.hiring_process: section
sections.stability: section

section.score: float in [1.0, 5.0], step 0.1
section.facts: str
section.evaluation: str

sections.compensation.structured.starting_salary_yen: int | null
sections.compensation.structured.starting_salary_bachelor_yen: optional int | null
sections.compensation.structured.starting_salary_master_yen: optional int | null
sections.compensation.structured.starting_salary_doctor_yen: optional int | null
sections.compensation.structured.average_annual_income_yen: int | null
sections.compensation.structured.average_overtime_hours_per_month: float | int | null
sections.compensation.structured.annual_holidays_days: int | null
sections.compensation.structured.remote_work_policy: full | hybrid | limited | none | unknown

adjustment.value: float in [-5.0, 5.0], step 0.1
adjustment.reason: str

summary.conclusion: str
summary.final_comment: str
summary.suitable_for: list[str]
summary.not_suitable_for: list[str]
summary.concerns: list[str]

run_metadata.executor: str
run_metadata.model: str
run_metadata.reasoning_effort: str
run_metadata.fixed_by_parent: bool
```

## Notes
- `scope.placement_candidates` は必須キーとし、候補を固定できない場合は空配列を許す
- `adjustment.value` は原則 `0.0`
- 数値系の欠損は `null` を使う。`unknown` を使ってよいのは `sections.compensation.structured.remote_work_policy` だけとする
- `run_metadata` は親が分かる実行条件を後から付与するための optional field とする。子エージェントは推測で埋めない
- 自然言語で書く欄は原則として日本語で書く。対象は `scope.ambiguity_note`, 各 section の `facts` / `evaluation`, `summary.*` である
- `sources.label` は日本語を基本とするが、公式ページの固有名が英語のみで自然な日本語訳がない場合は原文を残してよい
- スコープ固定、委譲、レビュー分離の運用ルールは `AGENTS.md` の company-analysis rules に従う

# Field semantics
- `facts`: 公式情報や確認できた事実のみを書く。評価語を混ぜない
- `evaluation`: `facts` に基づく判断を書く。新しい事実を足さない
- `score`: その節の総合判断
- `scope.ambiguity_note`: 固定対象と公開情報のずれ、または曖昧性を書く
- `summary.conclusion`: 会社全体の短い結論を 2 から 4 文で書く
- `summary.final_comment`: 最終評価の読みを 1 文で書く
- `summary.suitable_for`, `summary.not_suitable_for`, `summary.concerns`: 箇条書きで書く
- `sources`: 実際に判断根拠として使った URL だけを書く。可能な限り多くの公式ソースを使い、少なくとも募集要項、FAQ、福利厚生または働き方、会社概要またはIRの4系統を優先し、研究職なら研究所・技術組織ページも加える
- `run_metadata`: 親が知っている実行条件だけを書く。子は自分のモデル名や推論労力を推測しない
- `compensation.structured`: 公開された共通比較項目を数値または列挙で書く。数値項目の未公表は `null`、`remote_work_policy` の未公表だけ `unknown`
- `compensation.structured.starting_salary_yen`: 固定した評価対象の新卒枠に直接対応する公式の月額初任給を優先する。役職別の初任給がなく、その評価対象が広い新卒エンジニア共通給与に明確に含まれる場合のみ、その共通値を使ってよい。月額初任給を特定できない場合は `null`
- `compensation.structured.starting_salary_bachelor_yen`, `starting_salary_master_yen`, `starting_salary_doctor_yen`: 学位別初任給が公式に明示されている場合のみ入れる。月額値だけを使い、年額や想定年収は入れない。学位別に公開されていない場合は省略または `null`
- `compensation.structured.average_annual_income_yen`: 採用主体に対応する最新の公式平均年収を優先する。複数の公式値がある場合は、原則として最新の有価証券報告書や年次報告書などの法定開示を優先する。平均年収が公開されていない場合は `null`
- `compensation.structured.average_overtime_hours_per_month`: 月平均残業時間の公式値だけを書く。みなし残業時間や固定残業時間を代入しない
- `compensation.structured.annual_holidays_days`: 年間休日数の明示値だけを書く。土日祝や休暇制度から自力で合算しない
- `compensation.structured.remote_work_policy`: 公開制度から `full`, `hybrid`, `limited`, `none`, `unknown` を選ぶ。育児・介護・傷病など条件付きのみなら `limited`

# Prohibitions
- 必須キーを省略しない
- 構造化項目の欠損を文字列 `不明` で埋めない
- 未公表の数値を `0` で埋めない
- 自然言語欄を英語で書かない。ただし、固有名詞、学位名、公開職種名、公式用語の引用は必要な範囲で残してよい
- `run_metadata` を推測で埋めない
- 総合点を YAML に書かない
- 親が固定した `evaluation_target` を独断で差し替えない
- 参照禁止と言われた既存レポートや他エージェント結果を読まない

# Adjustment rule
- 補正は原則使わない
- 各項目では表現しきれない事情があるときだけ使う
- 各項目で既に採点した内容の言い換えや再計上には使わない
- 分野適合、大手感、雰囲気、直感には使わない

許容例:
- 公開情報が少なすぎて総合評価全体の信頼性が低い
- 情報が古く、現状を反映しているか不安がある
- 会社全体の評価と、実際に応募する採用枠・配属先の単位が大きくずれている
- グループ全体の数字は大きいが、応募先単体の実態とは乖離している
- 公開フローは重いが、博士向けには別ルートが確認できる

禁止例:
- SPI があるから下げる
- 博士給与が不明だから下げる
- 研究所があるから上げる
- 大企業だから上げる
- 分野的に合いそうだから上げる

# Workflow
1. 親が与えた `company_name`, `survey_date`, `slug`, `scope` を確認する
2. 固定された `evaluation_target` が公開情報と整合するか確認する
3. 6項目の `facts`, `evaluation`, `score` を埋める
4. `compensation.structured` を公開情報に従って埋める
5. `adjustment`, `summary`, `sources` を埋める
6. 必須キー、型、`null` の使い方を自己点検して返す

# Pre-return checklist
- 単一の YAML オブジェクトだけを返している
- `version = 1`
- `scope` と 6 sections の必須キーがある
- `compensation.structured` の必須キーがある
- 自然言語欄は日本語で書いている
- 数値系の不明な構造化値は `null`
- `remote_work_policy` の不明値だけ `unknown`
- 総合点や補正後総合点を YAML に書いていない
