# 出力契約リファレンス

このファイルは、調査と証拠整理が十分進んだ後、最終 YAML を整形し、返却前に点検するときにだけ読む。

## YAML 出力契約
- 単一の YAML オブジェクトのみ返す。
- YAML 内に Markdown、commentary、総合点、補正後総合点、見出し、数式説明を書いてはいけない。
- YAML template を、上から埋めるための調査用チェックリストとして使ってはいけない。調査で十分な証拠を集めてから、最後の整形時にだけ使う。
- 正本の output template は、`assets/yaml_output_template.yaml` である。
- その template の項目をきれいに支えられないと分かった場合は、YAML を確定する前に調査と証拠整理へ戻る。
- `sources` には、実際に証拠として使った URL だけを列挙する。

## グローバルルール
- `scope` は親が固定した厳密な評価対象として扱う。公開情報が異なっていても自分で対象をすり替えず、不一致は `scope.ambiguity_note` に記録する。
- 数値・制度 facts は `fact_layer` に入れ、その意味や解釈は 6 つの section に書く。
- `facts_official` と `facts_unofficial` を混ぜてはいけない。同様に `fact_layer.official` と `fact_layer.unofficial` も混ぜてはいけない。
- `fact_layer.unofficial` は意味のある値がある場合だけ保持する。ただし、重要な欠損が残るときに非公式情報の調査自体を省略してはいけない。
- `facts_unofficial` は、後で見返すための非公式情報メモである。構造化した事実に上げるには弱い情報、値を支えきれなかった情報の系統、軽い食い違いがある情報も、関連があるなら留保付きで残す。
- 出力 YAML 内の自然言語の項目は通常日本語で書く。`scope.ambiguity_note`、section の文章項目、`summary.*` に適用する。
- この skill が返す YAML には `run_metadata` を含めない。`run_metadata` は親が最終 accepted YAML に追加する。子は推測してはいけない。

## 禁止事項
- 必須 key を省略してはいけない。
- 構造化された値の欠損を文字列 `unknown` や日本語 placeholder `不明` で埋めてはいけない。
- 非公開 numeric value を `0` で埋めてはいけない。
- 自然言語の出力欄を英語で書いてはいけない。固有名詞、学位名、公開されている職種名、必要な公式用語の引用だけを必要最小限で残す。
- YAML に総合点を書いてはいけない。
- 非公式情報で `fact_layer.official` の数値や制度上の事実を上書きしてはいけない。

## 返却前 checklist
- 単一の YAML オブジェクトを返している。
- `version = 1`。
- `scope`、`fact_layer`、6 つの section がすべて必須 key を含む。
- `fact_layer.official` が必須 key を含む。
- 自然言語の項目が日本語で書かれている。
- 不明な数値の構造化値は `null` を使っている。
- `remote_work_policy` の unknown のみ `unknown` を使っている。
- `facts_official` と `facts_unofficial` が分離されている。
- すべての section に `score` がある。
- すべての source に `tier` がある。
- 非公式の構造化値が `fact_layer.unofficial` に分離されている。
- 総合点や補正後総合点を YAML に書いていない。
- 重要な欠損が見つかった場合、それらについて追加調査を試みた。
- 重要な欠損が残る場合、少なくとも 1 回は非公式情報の調査を実施した。
- 重要な欠損が残り、なお非公式情報源の数が 0 の場合、確認した情報の系統と不発理由を `facts_unofficial` または `summary.concerns` に記録している。
- 関連する非公式情報を、低信頼という理由だけで `facts_unofficial` から落としていない。
- 多くの `unconfirmed` 項目や `null` 値が残る場合、それらの深刻さを `scope.ambiguity_note`、section の `evaluation`、または `summary.concerns` で明示している。
