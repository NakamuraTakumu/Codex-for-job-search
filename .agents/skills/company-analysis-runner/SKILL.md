---
name: company-analysis-runner
description: 固定した採用対象について `company-analysis` 評価子を起動し、fact_layer とセクションスコアを含む YAML の検証、レンダリング、必要時の軽量レビューを統括する親エージェント用 skill。
---

# 目的
- 親エージェントが企業分析を最初から最後まで実行するときに使う。
- 実際の調査とセクション採点は、必ず `company-analysis` skill を使う子エージェントへ委譲する。
- 親エージェントは、対象スコープの固定、子エージェント起動、YAML 検証、Markdown レンダリング、保存を担当する。
- レビューは毎回必須ではない。validator だけでは拾いにくい高リスク問題がある場合に追加する。
- 強い理由がない限り、分析子とレビュー子のデフォルト model は `gpt-5.4-mini`、`reasoning_effort` は `medium` とする。

# 前提
- この skill では、企業分析の調査と採点を子エージェントに任せる。親は分析本文を書かない。
- 子 model を明示する必要がある場合は `gpt-5.4-mini` から始める。公開情報が極端に曖昧、レビューで再実行が必要、または推論の弱さが明確な場合だけ大きい model に上げる。
- 子の `reasoning_effort` を明示する必要がある場合は `medium` から始める。同様に、情報の曖昧さ、レビュー再実行、推論の弱さがある場合だけ上げる。
- 調査開始前に少なくとも次を固定する。
  - `company_name`
  - `survey_date`
  - `slug`
  - `scope.user_label`
  - `scope.target_application_unit`
  - `scope.hiring_entity_name`
  - `scope.role_family`: `researcher`, `research_engineer`, `engineer`, `consultant`, `generalist`, `other` のいずれか。採用年度、卒業年度、雇用区分を入れない。
  - `scope.alternative_application_units`: 同じ `hiring_entity_name` 配下の他の採用ルート、職種トラック、応募単位。
  - `scope.stability_entity_name`
- ユーザーが会社名だけを与えた場合でも、全社評価に広げない。実際の応募単位に近い `target_application_unit` を先に固定する。
- 想定候補者が博士課程在籍者、または明確な職歴のない博士新卒・既卒に近い場合は、新卒相当ルートを優先する。経験者採用は、新卒ルートが存在しない、明確に不適用、または明示的に不適切な場合だけ使う。
- 研究トラックやソフトウェアエンジニアリングトラックの有無は、公式の新卒相当応募ルートがあるかで判断する。ラボ紹介、技術 PR、役割としてあり得そう、だけでは判断しない。
- 公式の研究職・研究開発職ルートがある場合、単一対象のデフォルト `target_application_unit` はその研究系ルートにする。
- 研究系ルートの当年採用が未定、停止中、終了済み、または情報不足でも、近接するデータサイエンス職、SWE、コンサル職へ自動で置き換えない。
- 研究系ルートが公式に存在するが応募可否が弱い場合は、その研究系ルートを固定したまま `scope.ambiguity_note`、`summary.concerns`、`hiring_process` に不確実性として残す。
- 近接職種を分析するのは、ユーザーが明示的に求めた場合、または親が研究系ルートとは別対象として明示的に追加する場合だけにする。その場合も、研究系ルートの代替として扱わず、別の `target_application_unit` と別 slug にする。
- ソフトウェアエンジニアリング系ルートをデフォルトにするのは、公式の研究系ルート自体が見つからない場合、またはユーザーが明示的にエンジニアリング系を求めた場合だけ。
- 研究系とエンジニアリング系の両方が公式に確認できる場合、比較が目的、またはユーザーが両方を求めたときは別々の `target_application_unit` として扱う。それ以外では研究系をデフォルトにする。
- 両方を分析するとき、同じ子エージェントに `research` と `swe` を順番に渡さない。対象ごとに別の子を起動する。
- 安定性の根拠に親会社やグループ会社の数値を使う場合、`scope.hiring_entity_name` と `scope.stability_entity_name` の違いを残す。
- 公式の会社実体が曖昧で近接法人も確認すべき場合、親は候補をおおむね 3-5 社に絞り、それぞれを別の `target_application_unit` 候補として扱う。
- 会社名だけが与えられた場合、主要子会社や近接法人を先に確認し、それぞれが独立した新卒採用ルートを持つかを見る。
- 独立した子会社採用が見つかっても、親が自動で全件分析しない。候補と採用状況を要約し、主分析対象をユーザーに選ばせる。
- 複数会社が同時に与えられた場合、各社を途中で止めず、全社について子会社、近接法人、独立採用ルートを一通り確認してから対象確認へ進む。
- 多数の会社または対象がある場合、共有レビュー子の枠を 1 つ残し、残りの子エージェント枠をスキャンまたは分析に使う。
- 多数の会社または対象がある場合、一括起動ではなく、上限付き並列と補充キューを使う。子が完了または修正待ちになったら、次の対象に枠を回す。

# メインワークフロー
1. 複数会社が与えられた場合、まず各社の公式情報を見て、主要子会社や近接法人を全体から集める。件数が多い場合、この一次スキャンは可能な範囲で並列化する。
2. 各会社・候補法人について、独立した新卒採用ルートがあるか確認する。
3. 会社ごとに候補を要約する。独立採用する実体が複数ある場合、どれを主分析対象にするかユーザーに選ばせる。
4. 会社が 1 社だけの場合も同じ手順をその会社に対して行う。
5. 対象実体が固定されたら、公式採用ルートを確認し、研究系とソフトウェアエンジニアリング系の応募ルートがあるか見る。
6. 研究系ルートが公式に存在する場合、募集状態が未定または情報不足でも、デフォルトはその研究系ルートのまま固定する。近接職種へ置き換えず、応募可否の弱さを不確実性として記録する。
7. `research` と `swe` の両方が見つかった場合、親が扱いを決める。デフォルトは `research` のみ。ユーザーが両方を求める、または比較が目的なら、それぞれ別の `target_application_unit` として固定する。
8. `target_application_unit` がまだ曖昧なら、応募単位、採用実体名、`role_family`、必要に応じて `alternative_application_units` を分析前に固定する。
9. runner 開始直後に、レビュー専用の共有子エージェントを 1 つ起動して待機させる。
10. 固定済み対象ごとに、`company-analysis` 評価子を 1 つ起動する。ファイル名やレビュー payload の詳細で子起動を遅らせない。
   - 原則として model は `gpt-5.4-mini` を指定する。
   - 原則として `reasoning_effort` は `medium` を指定する。
   - 子プロンプトは `subagent_prompt_template.txt` の placeholder だけを埋めて作る。テンプレート自体を意図的に変更しない限り、言い換え、並べ替え、削除、場当たり的な追記をしない。
   - 固定済み対象が多い場合、空き枠を補充キューから埋め続ける。ある分析子が検証・レビュー引き渡しを終える、または修正待ちになったら、次の対象を起動する。
11. 各子には、完全な YAML オブジェクトだけを返すよう指示する。
12. 子には、まず公式情報から `fact_layer.official` と `facts_official` を埋め、その後に補助的な非公式情報として `fact_layer.unofficial` と `facts_unofficial` を追加し、最後に単一の最終 `score` を付けさせる。
13. 公式情報確認後も重要な空白が残る場合、子に少なくとも 1 回の非公式情報確認を要求する。使える値が見つからない場合でも、調べた非公式 lineage と失敗理由を記録させる。
14. 非公式観測を記録するために、公式情報が完全に揃う必要はない。関連する非公式観測は、見つかり次第 `facts_unofficial` または `summary.concerns` に残してよい。
15. 公式情報と非公式情報を同じ field に混ぜないよう明示する。
16. 非公式根拠は URL 数ではなく独立 lineage 数で数えるよう明示する。転載、ミラー、同一サービスの別表示を独立根拠として扱わせない。
17. 必要に応じて、既存レポートや他エージェント出力を読まないよう明示する。
18. デフォルトは対象ごとに 1 子。`research` と `swe` を同じ子に順番に渡さない。
19. 固定した `target_application_unit`、`hiring_entity_name`、`role_family` をプロンプト内で明示し、子が対象を黙って切り替えたり、`role_family` に `2028新卒` のような cohort を入れたりしないようにする。
20. 各対象の `slug` は親が決める。デフォルトは、曖昧でない範囲で最短の安定した対象ベース slug とする。例: `japan_ibm_research`, `ntt_data_swe`。
   - デフォルトでは日付を付けない。
   - 日付 suffix は、同じディレクトリ内の複数有効 run を区別する、衝突を避ける、または並列テスト成果物を明示的に残す必要がある場合だけ付ける。
   - 複数対象がある場合、`<company_slug>_<target_suffix>` のように決定的に分け、同一 run 内で同じ slug を再利用しない。
21. YAML を final として受け入れる前に `run_metadata` を追加する。最低限 `executor`, `model`, `reasoning_effort`, `fixed_by_parent` を入れる。
22. 返却 YAML の保存先は親が決める。子は自分で保存、更新、生成をしてはならず、メッセージで YAML だけを返す。
23. 子が YAML を返したらすぐ処理する。複数子が動いている場合、全員の完了を待たず検証やレビューに進む。
24. `python3 tool/check_company_analysis_yaml.py <yaml-file>` で形式を検証する。
25. validator が失敗した場合、schema 違反を列挙し、完全な YAML 再出力を子に求める。
26. validator 通過後、親がその YAML に軽い高リスク確認を行い、レンダリング前の内容レビューが必要か判断する。
27. レンダリング前レビューが必要な場合だけ、固定スコープと分析 YAML を prompt に直接埋め込み、待機中の共有レビュー子へ渡して review YAML を得る。
   - レビュー子も原則として model は `gpt-5.4-mini`、`reasoning_effort` は `medium` とする。
   - 会社や対象ごとにレビュー子を作り直さない。明確に reset が必要でない限り、同じ親 run 内では共有レビュー子を再利用する。
   - 毎回のレビュー引き渡しで、過去の review payload、slug、finding、rendered output を無視し、現在 prompt に埋め込まれた inline payload だけで判断するよう明示する。
   - 毎回のレビュー引き渡しで、現在意図している `slug` を明示し、それが scope error ではないと伝える。
28. `python3 tool/check_company_analysis_review.py <review-yaml>` でレビュー schema を検証する。
29. 内容レビューの verdict が `revise` の場合、finding を列挙して分析子へ戻し、完全な修正版 YAML 再出力を求める。
30. YAML がレンダリング可能として受理されたら、`python3 tool/render_company_analysis_md.py <yaml-file>` で Markdown を生成する。
31. レンダリング結果の確認が必要な場合だけ、固定スコープ、分析 YAML、rendered Markdown をレビュー子へ渡し、render-focused review を行う。
32. render-focused review でも `python3 tool/check_company_analysis_review.py <review-yaml>` を実行する。
33. render-focused review が `revise` を返した場合、finding を解消し、必要に応じて renderer または reviewer を再実行してから成果物を確定する。
34. 最終回答では、保存した YAML と Markdown を示す。レビュー成果物を生成した場合はそれも示す。

# プロンプトテンプレート
分析子には、この skill ディレクトリの `subagent_prompt_template.txt` をデフォルトテンプレートとして使う。

- 親は `{{...}}` placeholder に固定スコープを入れる。
- `research` と `swe` を並列実行する場合でも、各子には自身の固定スコープだけを埋めたテンプレートを渡す。
- 同じ会社の別トラック情報を比較メモとして混ぜない。必要な比較は後で親が行う。
- 会社間の公平性のため、placeholder 置換後のテンプレート本文をそのまま渡す。言い換え、並べ替え、削除、テンプレート外の追加指示をしない。
- run ごとにテンプレートを場当たり的に書き換えない。プロンプト変更が必要ならテンプレートファイル自体を編集する。
- 分析子を複数会社・複数対象で再利用する場合でも、テンプレート内の reset 指示を残し、各引き渡しを独立した新規対象として扱わせる。
- 毎回の分析引き渡しで、現在意図している `slug` を明示し、現在の固定スコープと現在対象の source だけから YAML を埋めるよう求める。
- テンプレート内の順序、つまり公式情報を先に、非公式情報を別枠で後に記録する流れを維持する。
- 重要な空白が残る場合に非公式確認を省かないこと、失敗した検索でも確認した lineage と理由を記録することをテンプレートに残す。

レビュー子には、この skill ディレクトリの `review_prompt_template.txt` をデフォルトテンプレートとして使う。

- 親は固定スコープ、分析 YAML 全文、必要時は rendered Markdown 全文をテンプレートに埋める。
- 親は、ユーザーが明示または強く示唆した対象、scope 固定理由、調査対象にしなかった近接職種・代替応募単位もテンプレートに埋める。
- ユーザーが研究職・Research・研究所・R&D を求めたのに、親が近接するデータサイエンス職、SWE、コンサル職、広い技術職を固定した場合、レビュー子に scope intent mismatch として確認させる。
- デフォルトのレビュー入力は分析 YAML だけとする。
- rendered Markdown は、レンダリングレベルの確認が必要な場合だけ追加する。
- レビュー子は `company-analysis-review` skill を使う。
- レビュー子への引き渡しに repository file path を使わない。
- inline 引き渡しでは Markdown fence を使わず、明示的 delimiter 付きの plain-text block として埋め込む。
- 共有レビュー子を再利用する場合でも、テンプレート内の reset 指示を残し、各レビューを独立した新規対象として扱わせる。
- 会社間の公平性のため、placeholder 置換後のレビューテンプレート本文をそのまま渡す。言い換え、並べ替え、削除、テンプレート外の追加指示をしない。
- run ごとにレビューテンプレートを場当たり的に書き換えない。プロンプト変更が必要ならテンプレートファイル自体を編集する。

# 検証
- メイン validator は `tool/check_company_analysis_yaml.py`。
- レビュー validator は `tool/check_company_analysis_review.py`。
- renderer は `tool/render_company_analysis_md.py`。
- 合計スコア計算の正は Python 実装。子エージェントに合計を再計算させない。
- final として受け入れる YAML には `run_metadata` が必須。最低限 `executor`, `model`, `reasoning_effort`, `fixed_by_parent` を入れる。
- 親は実際に子起動で使った設定を追記する。final YAML で `model` や `reasoning_effort` を暗黙にしない。
- 子 YAML を final として受け入れる時点で、validator の hard requirement を満たしている必要がある。特に公式 source は 4 件以上で、`recruit` と `company|ir` を含むこと。`faq`、`benefits`、公式 `kind=research` source は優先探索対象だが、公開されていない場合は自動失敗ではなく、欠落または公開情報の薄さとして記録する。
- これらの final acceptance 条件は、非公式 lineage や暫定メモの記録を止める理由にはならない。
- test と production の保存場所の分離は親が管理する。この skill では固定しない。

# レビューワークフロー
- レビューは毎回必須ではない。親の高リスク確認が必要と判断した場合だけ使う。
- 内容レビューは、分析子とは別のレビュー専用共有子エージェントが行う。
- runner 開始直後に、最初の review payload がまだなくても共有レビュー専用子を起動する。
- デフォルトでは会社ごとにレビュー子を作り直さない。同じ親セッション内では、実用上可能なら 1 つの共有レビュー子を会社・対象をまたいで再利用する。
- 複数の分析子が動いている場合、完了したものをまとめず、最初に完了した子からすぐレビューへ渡す。
- 親は固定スコープと review 対象 YAML をレビュー子へ直接渡す。
- rendered Markdown は別経路の post-render review 用。レンダリングレベルの確認が必要な場合だけ追加する。
- レビュー子は分析 YAML を再生成しない。固定 review schema だけを返す。
- review YAML を得たら、`python3 tool/check_company_analysis_review.py <review-yaml>` で schema を検証する。
- レンダリング前内容レビューが `revise` を返した場合、親が分析内容を自分で直さない。finding を分析子へ戻し、完全な修正版 YAML 再出力を求める。
- デフォルトでは、1 成果物につき修正 rerun と rereview は各 1 回までとする。validator failure または新しい high severity issue が出ない限り、同じ成果物を無期限レビューにしない。
- rereview では、前回 finding が解消されたかを中心に見る。新しい high severity issue が見える場合を除き、完全な新規レビューに広げない。
- retry loop を単純にするため、軽い内容修正でも通常は分析子に任せる。親が直してよいのは保存名や一時ファイル処理など、判断内容に影響しない機械的問題だけ。
- レビュー中は、過去の比較結果や期待する結論に合わせない。inline target data と必要最小限の文脈から判断する。

## レンダリング前内容レビューのトリガー
- 次のいずれかに当てはまる場合、レンダリング前に内容レビュー子を起動する。
  - ユーザーが求めた対象と、親が固定した `scope.target_application_unit` の意味単位がずれている可能性がある。
  - 研究職・Research・研究所・R&D の意図に対して、近接するデータサイエンス職、SWE、コンサル職、広い技術職を固定した可能性がある。
  - `fact_layer` に `true` や `false` など断定的な値があり、公式根拠が薄い可能性がある。
  - `summary`、`concerns`、`not_suitable_for` が、各セクション本文より広い、または強い主張をしている。
  - 非公式情報が公式情報と矛盾し、最終判断に重要な影響を与えている。
  - `facts_official` または `facts_unofficial` が薄すぎ、比較や再判断に必要な情報が残っていない。
  - 重要な空白が残っているのに、その重大さや追加調査不足が分析文に十分残っていない。
  - 重要な空白が残っているのに、非公式 source が 0 件で、非公式確認の失敗記録もない。
- いずれにも当てはまらない場合、レンダリング前内容レビューは省略してよい。

## レンダリング後レビューのトリガー
- Markdown 生成後、次のいずれかに当てはまる場合、render-focused review を起動する。
  - 親がレンダリングレベルの不整合を疑っている。
  - 受理済み YAML と rendered Markdown が一致していることを明示的に確認したい。
- すべてのレビューを省略する場合でも、validator と rendering は必ず実行する。

## レビュー観点
### 必須チェック
- `scope_integrity`
  - `target_application_unit`、`hiring_entity_name`、`role_family`、`alternative_application_units`、`stability_entity_name` が親固定スコープと一致しているか。
  - 固定 scope が、ユーザーが明示または強く示唆した対象と意味的に整合しているか。
  - 研究系 target が、ユーザー承認なしに近接職種へ置換されていないか。
- `source_separation`
  - 非公式情報が `facts_official` に混入していないか。
  - 公式情報が `facts_unofficial` に混入していないか。
  - `sources.tier` が実際の根拠 tier と一致しているか。
- `source_quality`
  - 公式 source が十分か。
  - 非公式 source が評価を過度に支配していないか。
  - 根拠が過度に重複していないか。
  - 転載、ミラー、同一非公式サービスの別表示を独立根拠として二重計上していないか。
  - `review_site`、`career_site`、`forum` が意図した役割で使われているか。
- `structured_data`
  - `fact_layer.official` が公式情報だけで埋められているか。
  - `fact_layer.unofficial` が公式値を上書きしていないか。
  - 月給と年収、年間休日と有給、平均残業と固定残業が混同されていないか。
- `section_boundary`
  - `phd_value`、`role_fit`、`rd_env` の境界が崩れていないか。
- `score_consistency`
  - `facts_official`、`facts_unofficial`、`evaluation`、最終 `score` が整合しているか。
  - 非公式情報も踏まえたうえで、最終判断が説明可能か。
- `summary_consistency`
  - `summary` がセクション別判断と整合しているか。
- `render_consistency`
  - 分析 YAML と rendered Markdown が一致しているか。
  - renderer による heading 欠落や表示問題がないか。
- `residual_uncertainty`
  - 不確実性やスコープ曖昧性が適切に残されているか。

### ヒューリスティック
- `source_quality`
  - 単一の非公式 lineage だけで公式情報を覆さない。「2 つの独立非公式 lineage」ルールは主に結論を覆すときに重要。単一の弱い非公式 lineage を暫定根拠として残すことは許容される。
  - 比較や再判断に必要な情報が失われるほど説明を短くしない。重複していない補助情報があるのに削りすぎている場合は、情報欠落として扱う。
- `summary_consistency`
  - `summary` は要約であり、セクション別の逐次再掲ではない。重要点を保ちながら簡潔かを確認する。

## レビュー返却 schema
- review output は単一の YAML オブジェクトだけにする。
- 形式は必ず次に合わせる。

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

# 不確実性確認
- 不確実性確認では、同じ固定スコープに対して少なくとも 3 つの独立した子エージェントを起動する。
- 各子には異なる `slug` を与える。
- 比較自体が目的でない限り、子に既存レポート、比較レビュー、過去の不確実性確認結果、他エージェント出力を読ませない。
- 各 YAML に validator を実行する。
- 親は総合評価とセクションスコアについて、範囲、平均、中央値、標準偏差を集計する。
- `evaluation-target mismatch` と `scoring variance` を混同しない。

# 失敗時の扱い
- 子が YAML 外に説明を混ぜたか、部分 YAML だけを返したかは親が判断する。
- YAML 外の説明が混ざった場合、その点を明示して再出力を求める。
- 部分 YAML の場合、不足 top-level key を列挙して再出力を求める。
- 子が成果物を自分で作成、変更、保存した場合、それらは unauthorized output とみなす。final artifact として扱わず、必要に応じて削除または隔離し、メッセージで返された YAML から続行する。
- validator mismatch がある場合、親が黙って修正しない。schema 違反を返して修正を求める。
- レビュー子が invalid review YAML を返した場合、schema 違反を列挙してレビュー子に再出力を求める。
- review verdict が `revise` の場合、finding を分析子へ戻し、完全な修正版 YAML 再出力を求める。
- 親は、保存名ミスや一時ファイル名など、内容判断に影響しない明らかな機械的問題だけを直してよい。

# 出力期待
- 親エージェントは YAML と Markdown の両方を残す。
- `research` と `swe` の両方を固定した場合、対象ごとに独立した YAML / Markdown pair を残す。
- 対象名は決定的にし、`slug` と保存ファイル名を合わせる。
- デフォルトは日付なしの簡潔な対象ベース名とする。例: `ntt_data_research`, `ntt_data_swe`。
- 日付は、曖昧性解消または複数 run の明示的保存に必要な場合だけ付ける。
- cross-target comparison が必要な場合、親は別の comparison note または review artifact を作る。
- 保存先、命名、test と production の分離は親が決める。
- 必要に応じて、不確実性レビューや比較レビューも適切な場所に保存する。
