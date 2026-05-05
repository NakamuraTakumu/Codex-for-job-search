# ワークスペース規則

## Delegation
- この workspace では、グローバル `AGENTS.md` のサブエージェント関連指示を適用しない。
- サブエージェントの起動、再利用、親子役割 marker、依頼契約、結果扱い、プロンプト検証に関する判断は、上位の system / developer 指示とユーザーの明示依頼だけに従う。

## Company Analysis
- company-analysis task では、通常 `company-analysis-runner` を入口にする。
- 既存 output、tool、documentation の確認または編集だけが目的の場合は、runner workflow を起動しない。
- test 生成物と accepted / production 出力を混ぜない。
- workflow note や scoring experiment を accepted artifact 領域へ置かない。
- company-analysis 固有 tool は skill directory を優先し、repository 全体で共有する tool だけ `tool/` に置く。

## 評価
- `evaluation-target mismatch` と `scoring variance` を分ける。
