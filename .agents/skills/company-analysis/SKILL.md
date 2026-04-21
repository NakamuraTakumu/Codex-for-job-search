---
name: company-analysis
description: 旧帝大の博士課程人材向けに企業を評価する子エージェント用スキル。固定した評価対象について、`fact_layer`、6項目の記述、単一スコア、summary、sources を含む検証可能な YAML を返す。
---

# Purpose
- このスキルは、親エージェントが会社分析を子エージェントへ委譲するときに使う
- 子エージェントの返却物は Markdown ではなく YAML とする
- Markdown の描画、保存、最終ファイル化は親エージェントまたはスクリプトが担当する
- レポートは1本にまとめ、公式情報で骨格を作った後に非公式情報を補助的に統合する

# Reader assumptions
- 想定読者は、旧帝大の博士課程人材またはそれに準ずる研究志向の候補者である
- 候補者の居住地の既定値は仙台とする
- 関心領域の既定値は、機械学習、数理・抽象理論、形式化、プログラミング言語理論、ソフトウェア工学、アルゴリズム実装、GPU / 型システムなどの計算機実装、研究成果のソフトウェア化・社会実装とする
- 分野適合だけで加点しない。博士の専門性が実際にどう評価されるかを優先して見る

# Core principles
- 企業紹介ではなく、就職先としての実態を評価する
- 事実と評価を分ける
- 速度より、固定 target の判断に必要な情報の網羅と official / unofficial の分離の明瞭さを優先する。時間をかけてよいので、急いで雑に埋めない
- 固定した target の判断に重要な情報欠損を見つけたときは、単に `未確認` を置いて先に進まず、追加調査の優先対象として扱う
- 可能な限り多くの公式ソースを使う。ただし同じ内容の重複ページを機械的に増やすのではなく、募集要項、FAQ、福利厚生、会社概要、IR、研究所・技術組織、事業・技術紹介など、種類の異なる根拠を広く集める
- 同じ内容を複数項目で二重計上しない
- 非公式情報は公式情報の存在を上書きせず、どこをどう動かしたかが追える形で残す

# Research method
- まず公式情報で骨格を取る。優先順は、採用ページ、募集要項、FAQ、福利厚生・働き方、会社概要、IR / 有価証券報告書、研究所・技術組織・技術紹介とする
- 情報が薄いときは拙速に埋めず、追加の公式根拠や補助根拠を探してから判断する
- `fact_layer` や fixed target の判断に重要な欄が大きく欠けるときは、その欄を埋めるための追加探索を優先する
- 一度見つからなかっただけで直ちに `未確認` や `未公表` を確定しない。関連系列を追加探索してよいが、その時点で得られている観測や不発も `facts_unofficial` または `summary.concerns` に残してよい
- まず `fact_layer.official` と各項目の `facts_official` を公式情報だけで作る
- official source の coverage は可能な限り満たす。ただし official が薄い論点では unofficial の関連観測も並行して集め、official completeness を待って unofficial 記録を止めない
- その後に口コミ、就活体験談、就活サイト、社員口コミなどの非公式情報を補助的に読む。重要な欠損が残る場合は、この unofficial pass を省略しない
- unofficial pass で意味のある構造化値が取れなかった場合も、見た系列と値に使えなかった理由を `facts_unofficial`、または `summary.concerns` に短く残す
- `fact_layer.unofficial` と `facts_unofficial` を作るかどうかは、取れた値の有無だけでなく、重要欠損が残っているかも踏まえて判断する
- 採用広報と事業実態を分けて見る。採用ページやイベント説明だけでなく、IR、法定開示、研究所ページ、技術発表、事業紹介で裏取りする
- 比較軸を固定して集める。少なくとも、採用対象、職種、初期配属、博士評価、初任給、平均年収、働き方、選考負担、研究/技術環境、企業基盤を意識して読む
- 良い情報だけでなく制約要因や不利要因も探す。配属不確定、博士優遇なし、選考負担、リモート制限、赤字、研究所と採用枠のずれなどを明示的に確認する
- relevant な unofficial 観測は、公式照合が完了する前でも見つけ次第 `facts_unofficial` や `summary.concerns` に記録してよい
- 1ページで全項目を埋めず、可能な限り異なる種類の公式ソースから cross-check する
- 非公式ソースは URL 数ではなく独立した情報系列で数える。転載、ミラー、同系サービスの別掲載面は独立根拠として二重計上しない
- 社員口コミ系、学生の選考体験系、掲示板系、待遇数値系の用途を分ける
- 社員口コミ系は独立性の重み付けでは同一系列を 1 系列として扱う。転載元と転載先が疑われる場合は元系列だけを採用するが、同一系列内の弱い観測は `facts_unofficial` に複数残してよい
- 学生の選考体験系は `hiring_process` と `role_fit` の補助に寄せ、待遇数値の根拠には原則使わない
- 待遇の数値系は `OpenWork`、`キャリコネ`、`エン カイシャの評判` のような別系列を優先し、学生体験談サイトや掲示板で代用しない

# Evaluation criteria

## 1. phd_value
- 博士採用枠、学位別給与、学士・修士・博士の初任給差、博士向け役割、博士採用実績、専門性評価の有無を見る
- 職務内容そのものの面白さや研究テーマ適合ではなく、博士号・研究実績が制度上どう評価されるかを見る
- 給与水準の高さそのものではなく、学位差や格付け差が博士号の制度的評価として存在するかを見る
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
- 初任給、平均年収、賞与、福利厚生、住宅補助、勤務地、働き方、裁量など、待遇水準そのものを見る
- 学位差の有無や大きさは `phd_value` 側で制度的評価として読む

## 5. hiring_process
- SPI 等の有無、テスト数、ES 負荷、面接回数、専門性を直接見てくれるかを見る
- 面接や面談がオンライン中心か対面中心か、それに伴う移動・宿泊・拘束時間の負担も見る。候補者の居住地は既定で仙台とする
- 高評価: 選考負担が軽く、研究能力や専門性を直接評価し、準備コストに対して納得感が高い
- 低評価: SPI などの一般適性検査が重く、就活慣れや generic な足切りを強く要求し、専門性と無関係な負担が大きい

## 6. stability
- 売上、従業員数、資本金、上場、親会社・グループ基盤、事業継続性を見る
- 主軸ではなく補助項目として扱う

# Scoring
- 各項目は `1.0` 以上 `5.0` 以下の `0.1` 刻みで採点する
- スコアは単一の `score` にし、公式情報で骨格を作った後に非公式情報も踏まえて最終判断として付ける
- 非公式情報を score に反映してよいが、反映度は同じ内容を公式根拠で言える場合より弱くする。目安として、独立した unofficial 2 系列がある場合でも公式根拠の 0.7 倍程度から始め、単発または low-confidence unofficial はそれより弱く扱う
- 公式情報と非公式情報が食い違う場合、単発の非公式情報だけで公式情報を覆さない。独立した非公式 2 系列が同じ方向を示すときに初めて、公式情報と釣り合う補助根拠として扱う
- 独立した非公式 2 系列に届かない場合、単発の非公式情報は `facts_unofficial` に残してよいが、スコアへの反映は主に留保や弱い補正にとどめる
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
fact_layer: map
sections: map
summary: map
sources: list[{label: str, url: http(s) URL, tier: official|unofficial, kind: source_kind}]
run_metadata: optional map set by parent

scope.user_label: str
scope.evaluation_target: str
scope.hiring_entity: str
scope.job_type: str
scope.placement_candidates: list[str]
scope.stability_entity: str
scope.ambiguity_note: str

fact_layer.official: fact_struct
fact_layer.unofficial: optional sparse_fact_struct

fact_struct.starting_salary_yen: int | null
fact_struct.starting_salary_bachelor_yen: optional int | null
fact_struct.starting_salary_master_yen: optional int | null
fact_struct.starting_salary_doctor_yen: optional int | null
fact_struct.has_degree_based_starting_salary_gap: optional bool | null
fact_struct.has_doctoral_hiring_track: optional bool | null
fact_struct.has_doctoral_grade_advantage: optional bool | null
fact_struct.average_annual_income_yen: int | null
fact_struct.average_overtime_hours_per_month: float | int | null
fact_struct.annual_holidays_days: int | null
fact_struct.remote_work_policy: full | hybrid | limited | none | unknown

sparse_fact_struct.starting_salary_yen: optional int | null
sparse_fact_struct.starting_salary_bachelor_yen: optional int | null
sparse_fact_struct.starting_salary_master_yen: optional int | null
sparse_fact_struct.starting_salary_doctor_yen: optional int | null
sparse_fact_struct.has_degree_based_starting_salary_gap: optional bool | null
sparse_fact_struct.has_doctoral_hiring_track: optional bool | null
sparse_fact_struct.has_doctoral_grade_advantage: optional bool | null
sparse_fact_struct.average_annual_income_yen: optional int | null
sparse_fact_struct.average_overtime_hours_per_month: optional float | int | null
sparse_fact_struct.annual_holidays_days: optional int | null
sparse_fact_struct.remote_work_policy: optional full | hybrid | limited | none | unknown

sections.phd_value: section
sections.role_fit: section
sections.rd_env: section
sections.compensation: section
sections.hiring_process: section
sections.stability: section

section.score: float in [1.0, 5.0], step 0.1
section.facts_official: str
section.facts_unofficial: str
section.evaluation: str

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
- `scope.ambiguity_note` は子エージェントが必ず埋める。大きな不一致がない場合も、`公開情報と固定対象の大きなずれはない。` のように短く明示する
- `fact_layer` は 6 つの評価項目より前に置く構造化事実層とする。数値や制度差の事実はここに集め、6 項目ではその意味づけを書く
- 数値系の欠損は `null` を使う。`unknown` を使ってよいのは `fact_layer.official.remote_work_policy` と、`fact_layer.unofficial` を残す場合の `fact_layer.unofficial.remote_work_policy` だけとする
- `run_metadata` は親が分かる実行条件を後から付与するための optional field とする。子エージェントは推測で埋めない
- 自然言語で書く欄は原則として日本語で書く。対象は `scope.ambiguity_note`, 各 section の `facts_official` / `facts_unofficial` / `evaluation`, `summary.*` である
- `sources.label` は日本語を基本とするが、公式ページの固有名が英語のみで自然な日本語訳がない場合は原文を残してよい
- 最終返却する YAML の `sources` では、公式 source を最低 4 本含め、少なくとも `recruit`, `faq`, `benefits`, `company|ir` の coverage を満たす
- `scope.evaluation_target` または `scope.job_type` が research-like なら、公式 source に `kind=research` を最低 1 本含める
- `sources.tier` は全 source で必須とし、`official` または `unofficial` のどちらかを必ず入れる
- `sources.kind` は全 source で必須とする。`official` では `recruit`, `faq`, `benefits`, `company`, `ir`, `research`, `business`, `other`、`unofficial` では `review_site`, `forum`, `career_site`, `blog`, `other` を使う
- 非公式ソースの独立性は URL の数ではなく系列で判断する。転載、ミラー、同系サービスの別掲載面は独立根拠として数えない
- `review_site` を増やすときは転載関係を確認する。たとえば社員口コミの転載面と元サービスを同時に独立根拠として採用しない。同一系列内の補助観測は複数残してよいが、重み付けは 1 系列として扱う
- `career_site` は主に選考体験と職務理解の補助に使い、待遇数値の根拠としては原則使わない
- `forum` は進行感や不確実性の補助にとどめ、単発投稿を独立した強い根拠として扱わない

# Field semantics
- `facts_official`: 公式情報や確認できた一次情報のみを書く。評価語を混ぜない
- `facts_unofficial`: 口コミ、就活体験談、社員口コミ、二次情報などの補助根拠を書く。評価語を混ぜない。重要な欠損が残らないなら空文字列でよい。重要な欠損が残る場合は、値に使えなかったときでも見た unofficial 系列や不発理由を短く残す。low-confidence な unofficial でも fixed target に関係する観測なら残してよく、強くスコアを動かさなくてもよい
- `facts_official` / `facts_unofficial`: 採点の最小要約に切り詰めすぎない。重複がなく、後から比較や再判断に役立つ情報なら残してよい
- `evaluation`: 公式情報と非公式情報の両方を踏まえた最終判断を書く。新しい事実を足さない
- `score`: 公式情報で作った骨格と、必要に応じて非公式情報も踏まえた最終スコア
- `scope.ambiguity_note`: 固定対象と公開情報のずれ、または曖昧性を書く
- `fact_layer.official`: 公式情報から取れる数値的・制度的事実を 6 項目の前提として書く
- `fact_layer.unofficial`: 非公式情報から取れる参考値を書く。公式値の代わりにせず、独立系列の補助根拠だけを入れる
- `fact_layer.*` の `null` は単なる空欄ではなく、判断に重要だが確認できなかった事実を表す。重要な `null` が多い場合は、そのまま流さず追加探索を優先する
- `summary.conclusion`: 固定した `scope.evaluation_target` に対する短い結論を 2 から 4 文で書く
- `summary.final_comment`: 最終評価の読みを 1 文で書く
- `summary.suitable_for`, `summary.not_suitable_for`, `summary.concerns`: 箇条書きで書く
- `sources`: 実際に判断根拠として使った URL だけを書く。最終返却する YAML では、公式 source を最低 4 本含め、少なくとも募集要項、FAQ、福利厚生、会社概要または IR の coverage を満たす。研究職系 target なら研究所・技術組織ページも最低 1 本含める。各 source には `tier: official | unofficial` と `kind` を付ける
- `sources`: 非公式 source を複数書いてよいが、評価時には独立系列が何本あるかを意識する。転載やミラーを並べても一致度を上げたことにはしない
- `run_metadata`: 親が知っている実行条件だけを書く。子は自分のモデル名や推論労力を推測しない
- `fact_layer.official.starting_salary_yen`: 固定した評価対象の新卒枠に直接対応する公式の月額初任給を優先する。役職別の初任給がなく、その評価対象が広い新卒エンジニア共通給与に明確に含まれる場合のみ、その共通値を使ってよい。月額初任給を特定できない場合は `null`
- `fact_layer.official.starting_salary_bachelor_yen`, `starting_salary_master_yen`, `starting_salary_doctor_yen`: 学位別初任給が公式に明示されている場合のみ入れる。月額値だけを使い、年額や想定年収は入れない。学位別に公開されていない場合は省略または `null`
- `fact_layer.official.has_degree_based_starting_salary_gap`: 学士・修士・博士で初任給差が制度上明示されているかを書く。未確認は `null`
- `fact_layer.official.has_doctoral_hiring_track`: 博士向けの独立応募枠や導線が制度上確認できるかを書く。未確認は `null`
- `fact_layer.official.has_doctoral_grade_advantage`: 博士や研究実績に応じた格付け差・等級差が制度上確認できるかを書く。未確認は `null`
- `fact_layer.official.average_annual_income_yen`: 採用主体に対応する最新の公式平均年収を優先する。複数の公式値がある場合は、原則として最新の有価証券報告書や年次報告書などの法定開示を優先する。平均年収が公開されていない場合は `null`
- `fact_layer.official.average_overtime_hours_per_month`: 月平均残業時間の公式値だけを書く。みなし残業時間や固定残業時間を代入しない
- `fact_layer.official.annual_holidays_days`: 年間休日数の明示値だけを書く。土日祝や休暇制度から自力で合算しない
- `fact_layer.official.remote_work_policy`: 公開制度から `full`, `hybrid`, `limited`, `none`, `unknown` を選ぶ。育児・介護・傷病など条件付きのみなら `limited`
- `fact_layer.unofficial.*`: 非公式情報から得た参考値を書く。意味のある値がないなら `fact_layer.unofficial` 自体を省略してよいが、重要な欠損が残る場合は unofficial pass 自体を省略せず、その結果は `facts_unofficial` か `summary.concerns` に残す。残す場合、未確認は `null` を使い、`unknown` を使えるのは `remote_work_policy` だけとする

# Prohibitions
- 必須キーを省略しない
- 構造化項目の欠損を文字列 `不明` で埋めない
- 未公表の数値を `0` で埋めない
- 自然言語欄を英語で書かない。ただし、固有名詞、学位名、公開職種名、公式用語の引用は必要な範囲で残してよい
- `run_metadata` を推測で埋めない
- 総合点を YAML に書かない
- 親が固定した `evaluation_target` を独断で差し替えない
- 既存会社レポート、review note、archive 出力、他 subagent 結果を読まない
- 参照禁止と言われた既存レポートや他エージェント結果を読まない
- 非公式情報で `fact_layer.official` の数値・制度事実を上書きしない
- `fact_layer.official` と `fact_layer.unofficial` を混ぜない
- `facts_official` と `facts_unofficial` を混ぜない
- 非公式ソースの転載関係を無視して独立根拠の数を水増ししない
- 単発の非公式根拠だけで公式情報を覆さない
- `review_site` の待遇数値と `career_site` / `forum` の選考体験を同じ強さの根拠として扱わない
- 重要な欠損が残るのに unofficial pass 自体を省略しない

# Workflow
1. 親が与えた `company_name`, `survey_date`, `slug`, `scope` を確認する
2. 固定された `evaluation_target` が公開情報と整合するか確認する
3. 公式情報だけで `fact_layer.official` を埋める
4. 公式情報だけで 6項目の `facts_official` を埋める
5. 重要な欠損や曖昧性が大きい場合は、その論点を埋めるための追加探索を優先する
6. 非公式情報を補助的に確認する。重要な欠損が残る場合は、この unofficial pass を必ず 1 回は回す
   - 使う前に、各 unofficial source が独立系列か、転載・ミラーかを簡単に判定する
   - 社員口コミ系、学生の選考体験系、掲示板系を用途別に使い分ける
   - 同一系列が疑われる source は 1 系列として扱い、複数票のように数えない
   - 使える値が取れなかった場合も、探索した unofficial 系列と不発理由を `facts_unofficial` または `summary.concerns` に短く残す
7. `evaluation` を統合判断として書く
8. 各 section の `score` を最終判断として付ける
9. `summary`, `sources` を埋める
10. 必須キー、型、`null` の使い方を自己点検して返す

# Pre-return checklist
- 単一の YAML オブジェクトだけを返している
- `version = 1`
- `scope` と `fact_layer` と 6 sections の必須キーがある
- `fact_layer.official` の必須キーがある
- 自然言語欄は日本語で書いている
- 数値系の不明な構造化値は `null`
- `remote_work_policy` の不明値だけ `unknown`
- `facts_official` と `facts_unofficial` を分けている
- 各 section の `score` を埋めている
- `sources` に `tier` を付けている
- 非公式 source の用途と独立性が崩れていない
- 非公式の構造化数値は `fact_layer.unofficial` に分けている
- 総合点や補正後総合点を YAML に書いていない
- 重要な欠損を見つけたときに、その論点の追加探索を試みた
- 重要な欠損が残る場合、unofficial pass を少なくとも 1 回は回した
- 重要な欠損が残るのに unofficial source が 0 件なら、見た系列と不発理由を `facts_unofficial` または `summary.concerns` に残している
- `未確認` や `null` が多く残る場合、その深刻さを `scope.ambiguity_note`、section の `evaluation`、または `summary.concerns` のどこかに明示している
