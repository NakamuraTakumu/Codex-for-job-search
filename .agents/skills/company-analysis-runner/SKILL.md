---
name: company-analysis-runner
description: 親エージェント用の orchestration skill。固定した評価対象に対して `company-analysis` evaluator を使う子エージェントをできるだけ早く起動し、`fact_layer` と単一スコアを含む YAML を回収して検証・描画・保存し、必要なケースにだけ共通 review 用サブエージェントによる軽量レビューや不確実性チェックを追加する。
---

# Purpose
- このスキルは、親エージェントが会社分析を end-to-end に実行するときに使う
- 子エージェントの実調査は `company-analysis` skill に委譲する
- 親エージェントは scope 固定、子起動、YAML 検証、Markdown 描画、保存を担当する
- このスキルを使うとき、会社分析の実調査と採点は常にサブエージェントで行い、親は orchestration に専念する
- review は常時必須ではなく、validator では拾いにくい高リスク箇所があるときだけ追加する
- 分析子と review 子のモデルは、特別な理由がなければ `gpt-5.4-mini` を既定とする

# Preconditions
- この skill では、会社分析の実調査と採点にサブエージェントを使う
- 会社分析をこのスキルで実行する場合、親が自分で本文分析を書かず、実調査と section score 付与は必ず子エージェントに委譲する
- 子エージェントの model 指定が必要な場合、まず `gpt-5.4-mini` を使い、公開情報の曖昧性が極端に大きい、review の指摘で再実行になった、または reasoning 不足が明確な場合だけ大きい model へ上げる
- 調査前に少なくとも以下を決める
  - `company_name`
  - `survey_date`
  - `slug`
  - `scope.user_label`
  - `scope.evaluation_target`
  - `scope.hiring_entity`
  - `scope.job_type`
  - `scope.placement_candidates`
  - `scope.stability_entity`
- `company_name` だけが与えられた場合でも、親はそのまま全社評価に広げず、実際の応募単位に近い `scope.evaluation_target` を先に固定する
- 現役博士または博士修了直後で、明確なフルタイム職歴がない候補者を前提にするときは、新卒トラックを優先し、中途トラックは新卒が存在しない・適用外・明確に不適合な場合だけ使う
- 研究職トラックとソフトウェアエンジニア職トラックは、`現実的` かどうかではなく、公式ソース上で新卒相当の応募導線が確認できるかで存在判定する
- 研究職トラックとソフトウェアエンジニア職トラックの両方の応募導線が確認できたら、原則として両方を別 `evaluation target` として分析する
- 両方を分析するときは、同じ子エージェントに順番に見せず、`research` 用と `swe` 用に別の子エージェントを立てる
- 研究所ページや技術広報ページの存在だけでは `research` または `swe` トラックがあるとみなさない。募集要項、採用ページ、FAQ、説明資料などの公式な採用導線を優先する
- グループ企業や親会社の数値を安定性補助に使うときは、`scope.hiring_entity` と `scope.stability_entity` のずれを残す
- 正式企業名が曖昧で近しい企業群も調べる必要があるときは、親が候補群を最大 3 から 5 件程度に絞って列挙し、それぞれを別 `evaluation target` として独立に扱う
- ユーザーが会社名だけを与えたときは、その会社の主な子会社や近縁法人も親が確認し、各法人が独立した新卒採用導線を持つかを先に調べる
- 子会社や近縁法人に独立採用が見つかった場合でも、親が勝手に全部を本分析せず、候補一覧と採用有無を整理した上で、どれを調べるかはユーザーに委ねる
- 複数企業がまとめて与えられた場合は、会社ごとに途中で止まらず、まず全社分の子会社・近縁法人・独立採用有無を一括で洗い出してから、本分析対象の確認に進む

# Main workflow
1. 複数企業が与えられたときは、まず全社ぶんについて会社本体の公式情報を見て、主な子会社や近縁法人を一括で洗い出す
2. 各企業・各候補法人について、独立した新卒採用導線があるかを親が一括で確認する
3. その結果を企業ごとの候補一覧としてまとめ、独立採用のある候補群が複数ある場合は、どの法人を本分析するかをユーザーに委ねる
4. 1社だけ与えられた場合も、同じ手順をその1社に対して行う
5. 分析対象法人が決まったら、その公式採用導線を見て `research` トラックと `swe` トラックの有無を親が確認する
6. `research` と `swe` の両方が見つかった場合の扱いは親が決める。必要なら片方だけ、必要なら両方を別 `evaluation target` として固定する
7. `evaluation target` が曖昧なままなら、応募単位、採用主体、職種、必要なら配属候補まで親が先に固定する
8. 固定した各トラックごとに `company-analysis` evaluator を使う子エージェントを 1 本ずつ立てる。保存先や review payload の詳細は後回しにし、まず子を動かす
   - model は原則 `gpt-5.4-mini` を指定する
9. 子には、完全な YAML オブジェクトのみ返すよう指示する
10. 子には、まず公式情報だけで `fact_layer.official` と `facts_official` を埋め、その後に非公式情報で `fact_layer.unofficial` と `facts_unofficial` を補助的に足し、最後に単一の `score` を付ける順序を守らせる
11. 公式 pass の後に重要な欠損が残る場合は、子に unofficial pass を必ず 1 回は回させる。使える値が取れなくても、探索した unofficial 系列と不発理由を残させる
12. official completeness を待って unofficial 観測の記録を止めさせない。relevant な unofficial 観測は見つけ次第 `facts_unofficial` や `summary.concerns` に残してよいと明示する
13. 子には、公式情報と非公式情報を同じ欄に混ぜないこと、非公式情報で `fact_layer.official` の構造化事実を上書きしないことを明示する
14. 子には、非公式ソースを URL 数ではなく独立系列で扱い、転載・ミラー・同系サービスの別掲載面を独立根拠として水増ししないことを明示する
15. 必要なら「既存レポートや他エージェント結果を読まない」と明示する
16. 1 社 1 子を原則にし、特に `research` と `swe` を同じ子に順番に見せない
17. 子が勝手に別対象へ切り替えないよう、固定した `evaluation target`, `hiring entity`, `job type` をプロンプトに明示する
18. 親は target ごとの `slug` を決める。複数 target の場合、`<company_slug>_<target_suffix>` のように deterministic に分け、同一 run 内で再利用しない
19. 親が分かる実行条件があれば `run_metadata` を YAML に追記する
20. 返ってきた YAML の保存先は親が決める
21. 親が `python3 tool/check_company_analysis_yaml.py <yaml-file>` を実行して形式検証する
22. validator が落ちたら、親が schema 違反を列挙して子に差し戻し、再出力させる
23. validator を通ったら、親はまず YAML だけを見て軽い高リスク確認を行う
24. 高リスク確認で問題が見えなければ、そのまま `python3 tool/render_company_analysis_md.py <yaml-file>` で Markdown を生成する
25. 高リスク確認で review が要ると判断したときだけ、親は fixed scope と analysis YAML データを prompt 内へ直接埋め込み、1 人の共通 review 用サブエージェントへ渡して review YAML を回収する
   - review 子の model も原則 `gpt-5.4-mini` を指定する
26. render-level の不整合も見たいときだけ、親は生成 Markdown データも review 子へ追加で渡す
27. 親は `python3 tool/check_company_analysis_review.py <review-yaml>` を実行して review schema を検証する
28. review が `revise` なら、親は finding を列挙して分析子エージェントへ差し戻し、修正版の完全な YAML を再出力させる
29. 修正版 YAML が返ったら、親は validator、必要なら reviewer、その後 renderer を再度回す
30. 回答では、保存した YAML と Markdown を参照し、review を作った場合はそれも参照する

# Prompt template
子エージェントへ渡すプロンプトは、原則としてこの skill ディレクトリ内の `subagent_prompt_template.txt` を使って固定化する。

- 親はテンプレートの `{{...}}` プレースホルダへ固定スコープを埋めて使う
- `research` 用と `swe` 用を同時に走らせるときも、各子には自分の固定スコープだけを埋めたテンプレートを渡す
- 同じ会社の別トラック情報を比較メモとして混ぜず、必要なら親が後で比較する
- テンプレート本文をその場で毎回書き換えず、変更したい場合はテンプレートファイル自体を更新する
- テンプレートには、公式情報を先に処理し、その後に非公式情報を分離して追記する順序を固定で含める
- テンプレートには、重要な欠損が残る場合は unofficial pass を省略せず、取れなかった場合も探索した系列と不発理由を残すことを含める

review 子エージェントへ渡すプロンプトは、原則としてこの skill ディレクトリ内の `review_prompt_template.txt` を使って固定化する。

- 親は fixed scope、analysis YAML の本文、必要なら render 済み Markdown の本文をテンプレートへ埋めて使う
- review のデフォルト入力は analysis YAML の本文だけにする
- render-level 確認が必要なケースだけ render 済み Markdown の本文も追加する
- review 子には `company-analysis-review` skill を使わせる
- review 子との受け渡しで repository file path を handoff 手段として使わない
- inline handoff では markdown fence を使わず、delimiter 付きの plain-text block として埋め込む
- review 子のテンプレート本文も、その場で毎回書き換えず、変更したい場合はテンプレートファイル自体を更新する

# Validation
- validator は `tool/check_company_analysis_yaml.py`
- review validator は `tool/check_company_analysis_review.py`
- renderer は `tool/render_company_analysis_md.py`
- 総合点計算の正本は Python 実装であり、子エージェントに再計算させない
- `run_metadata` は親が知っている場合だけ追記する。少なくとも `executor`, `model`, `reasoning_effort`, `fixed_by_parent` を使う
- child YAML が最終返却される段階では validator の hard requirement を満たす必要がある。特に official source は最低 4 本、`recruit` / `faq` / `benefits` / `company|ir` の coverage を必須とし、research-like target では `kind=research` も最低 1 本必要である。これは最終受理条件であり、unofficial lineage や tentative note の記録を止める理由にはしない
- テスト結果と本番結果の保存先は親が分けて管理し、この skill には固定しない

# Review workflow
- review は常時 mandatory ではなく、親の高リスク確認で必要と判断したケースだけ回す
- 内容レビュー本体は、analysis 子とは別の、共通 review 専用サブエージェントに行わせる
- 親は fixed scope と reviewed YAML データを review 子へ直接渡す
- render-level の確認も必要なときだけ、生成 Markdown データを追加で渡す
- review 子には YAML 再生成をさせず、固定の review schema だけを書かせる
- 親は review YAML 作成後に `python3 tool/check_company_analysis_review.py <review-yaml>` を実行して review schema も検証する
- review が `revise` のときは、親が自分で内容修正せず、finding を分析子エージェントへ返して修正版の完全な YAML を再出力させる
- 差し戻し簡略化のため、軽微な内容修正も原則として分析子エージェントに処理させる。親が直してよいのは保存名や一時ファイルのような機械的事項だけとする
- レビュー時も、既存比較結果や intended answer に引っ張られすぎず、prompt に直接渡した対象データと必要最小限の文脈だけで判定する

## High-risk review triggers
- 次のどれかがあれば、review 子を起動する
  - `fact_layer` に `false` / `true` のような断定値があり、公式根拠が薄い可能性がある
  - `summary`, `concerns`, `not_suitable_for` に、section 本文より強い断定や広い一般化がある
  - 非公式情報が公式情報と食い違い、最終判断に実質的に効いている
  - `facts_official` / `facts_unofficial` の記述が薄く、比較や再判断に必要な補助情報を落としている疑いがある
  - 重要な欠損が多いのに、その深刻さや追加探索の不足が analysis 本文に十分残っていない
  - 重要な欠損が残るのに unofficial source が 0 件、または unofficial search の不発記録もない
  - 親が render-level の不整合を疑っている
- 上の trigger がなければ、review をスキップしてよい
- review をスキップした場合でも、validator と renderer は必ず通す

## Review rubric
### Required checks
- `scope_integrity`
  - `evaluation_target`, `hiring_entity`, `job_type`, `placement_candidates`, `stability_entity` が親の fixed scope と矛盾していないか
- `source_separation`
  - `facts_official` に非公式情報が混ざっていないか
  - `facts_unofficial` に公式情報だけを書いていないか
  - `sources.tier` が実際の根拠種別と一致しているか
- `source_quality`
  - 公式ソースが十分か
  - 非公式ソースが過剰に評価を支配していないか
  - 重複根拠ばかりになっていないか
  - 非公式ソースの転載・ミラー・同系サービスを独立根拠として二重計上していないか
  - `review_site`, `career_site`, `forum` の用途が崩れていないか
- `structured_data`
  - `fact_layer.official` が公式情報だけで埋まっているか
  - `fact_layer.unofficial` が公式値を上書きしていないか
  - 月額/年額、年間休日/有給、平均残業/固定残業時間の取り違えがないか
- `section_boundary`
  - `phd_value / role_fit / rd_env` の境界が崩れていないか
- `score_consistency`
  - `facts_official` / `facts_unofficial` / `evaluation` と最終 `score` が整合しているか
  - 非公式情報を踏まえた最終判断が説明可能か
- `summary_consistency`
  - `summary` と各 section の評価が矛盾していないか
- `render_consistency`
  - analysis YAML と render 済み Markdown の内容対応が崩れていないか
  - renderer による見出し欠落や表示崩れがないか
- `residual_uncertainty`
  - 不確実性や scope ambiguity が適切に残されているか

### Heuristics
- `source_quality`
  - 単発の非公式根拠だけで公式情報を覆していないか。独立した非公式 2 系列の要件は、主に結論を覆す場合に適用する。単発の weak unofficial を tentative evidence として残すこと自体は妨げない
  - 記述量が少なすぎて比較や再判断に必要な情報を落としていないか。重複のない補助情報があるのに極端に削られていれば、情報不足として扱う
- `summary_consistency`
  - summary は要約であり、各 section の繰り返しではない。要点を保ったまま簡潔に読めるかを見る

## Review return schema
- review YAML は単一の YAML オブジェクトだけにする
- 形式は次に固定する

```text
review.verdict: pass | revise
review.findings: list[review_finding]
review.passed_checks: list[str]

review_finding.severity: high | medium | low
review_finding.category: scope_integrity | source_separation | source_quality | structured_data | section_boundary | score_consistency | summary_consistency | render_consistency | residual_uncertainty
review_finding.section: scope | fact_layer | phd_value | role_fit | rd_env | compensation | hiring_process | stability | summary | sources | rendered_output
review_finding.message: str
review_finding.suggested_fix: str
```

# Uncertainty workflow
- 不確実性チェックでは、同じ固定スコープで 3 本以上の独立子エージェントを立てる
- 各子に異なる `slug` を与える
- 比較自体が目的でない限り、既存レポート、比較レビュー、過去の不確実性結果、他エージェント結果を各子に読ませない
- 各 YAML を validator に通す
- 総合評価と各 section score のレンジ、平均、中央値、標準偏差を親が集計する
- `evaluation-target mismatch` と `scoring variance` を混同しない

# Failure handling
- 子が YAML 以外の説明を混ぜたか、partial YAML を返したかの判定は親が行う
- 子が YAML 以外の説明を混ぜたら、親がそこを明示して再出力させる
- 子が partial YAML を返したら、親が欠けたトップレベルキーを列挙して再出力させる
- validator mismatch があるときは、親が黙って補完せず、schema 違反を返して修正させる
- review 子が invalid review YAML を返したら、親が schema 違反を列挙して review 子へ再出力させる
- review が `revise` のときは、親が finding を分析子エージェントへ返し、修正版の完全な YAML を再出力させる
- ただし、明らかな保存ミスや一時ファイル名の問題など、内容判断に影響しない機械的修正は親が処理してよい

# Output expectations
- 親エージェントは最終的に YAML と Markdown を残す
- `research` と `swe` の両方を固定した場合は、target ごとに独立した YAML / Markdown の組を 1 つずつ残す
- target ごとの命名は deterministic にし、`slug` と保存名は対応付ける。例: `ntt_data_research`, `ntt_data_swe`
- target 横断の比較が必要なら、親が別 artifact として比較メモや review を作る
- 保存先、命名、テスト/本番の区別は親が決める
- 必要なら不確実性レビューや比較レビューも親が適切な場所へ保存する
