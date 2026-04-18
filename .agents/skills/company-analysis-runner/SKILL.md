---
name: company-analysis-runner
description: 親エージェント用の orchestration skill。固定した評価対象に対して `company-analysis` evaluator を使う子エージェントを起動し、YAML を回収して検証・描画・保存し、必要なら独立レビューや不確実性チェックまで進める。
---

# Purpose
- このスキルは、親エージェントが会社分析を end-to-end に実行するときに使う
- 子エージェントの実調査は `company-analysis` skill に委譲する
- 親エージェントは scope 固定、子起動、YAML 検証、Markdown 描画、保存を担当する
- このスキルを使うとき、会社分析の実調査と採点は常にサブエージェントで行い、親は orchestration に専念する

# Preconditions
- サブエージェント起動は、高優先度指示とユーザー要望が許すときだけ行う
- 会社分析をこのスキルで実行する場合、親が自分で本文分析を書かず、実調査と section score 付与は必ず子エージェントに委譲する
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
8. 固定した各トラックごとに `company-analysis` evaluator を使う子エージェントを 1 本ずつ立てる
9. 子には、完全な YAML オブジェクトのみ返すよう指示する
10. 必要なら「既存レポートや他エージェント結果を読まない」と明示する
11. 1 社 1 子を原則にし、特に `research` と `swe` を同じ子に順番に見せない
12. 子が勝手に別対象へ切り替えないよう、固定した `evaluation target`, `hiring entity`, `job type` をプロンプトに明示する
13. 親が分かる実行条件があれば `run_metadata` を YAML に追記する
14. 返ってきた YAML の保存先は親が決める
15. 親が `python3 tool/check_company_analysis_yaml.py <yaml-file>` を実行して形式検証する
16. validator が落ちたら、親が schema 違反を列挙して子に差し戻し、再出力させる
17. validator を通ったら `python3 tool/render_company_analysis_md.py <yaml-file>` で Markdown を生成する
18. 生成した Markdown の保存先も親が決める
19. 必要なら、作成担当とは別のレビュー用子エージェントで内容の妥当性だけを確認する
20. 回答では、保存した YAML と Markdown の両方を参照する

# Prompt template
子エージェントへ渡すプロンプトは、原則としてこの skill ディレクトリ内の `subagent_prompt_template.txt` を使って固定化する。

- 親はテンプレートの `{{...}}` プレースホルダへ固定スコープを埋めて使う
- `research` 用と `swe` 用を同時に走らせるときも、各子には自分の固定スコープだけを埋めたテンプレートを渡す
- 同じ会社の別トラック情報を比較メモとして混ぜず、必要なら親が後で比較する
- テンプレート本文をその場で毎回書き換えず、変更したい場合はテンプレートファイル自体を更新する

# Validation
- validator は `tool/check_company_analysis_yaml.py`
- renderer は `tool/render_company_analysis_md.py`
- 総合点計算の正本は Python 実装であり、子エージェントに再計算させない
- `run_metadata` は親が知っている場合だけ追記する。少なくとも `executor`, `model`, `reasoning_effort`, `fixed_by_parent` を使う
- テスト結果と本番結果の保存先は親が分けて管理し、この skill には固定しない

# Review workflow
- 内容レビューは、作成した子とは別の子エージェントに行わせる
- 親が validator と renderer を済ませた後にレビューへ回す
- レビュー時は、レビュー対象 YAML、必要なら生成 Markdown、必要最小限の文脈だけを渡す
- レビュー子には YAML 再生成を求めず、 findings / risks / open questions を返させる
- レビュー子には、既存比較結果や intended answer を渡しすぎない
- 親は内容レビューを自分だけで完結させず、レビューを行うなら別の子エージェントを使う

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
- ただし、明らかな保存ミスや一時ファイル名の問題など、内容判断に影響しない機械的修正は親が処理してよい

# Output expectations
- 親エージェントは最終的に YAML と Markdown を残す
- 保存先、命名、テスト/本番の区別は親が決める
- 必要なら不確実性レビューや比較レビューも親が適切な場所へ保存する
