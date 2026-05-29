# Codex for Job Search

博士課程学生向けの企業分析・採用情報ビューアである。企業分析レポートと採用情報を静的な GitHub Pages で閲覧できるようにまとめている。

この repository には公開用の viewer と暗号化済み Pages artifact を置く。

## Contents

- `index.html`: 企業分析一覧と詳細を表示する静的 viewer。
- `github-pages/report/`: viewer が読む暗号化済み report artifact。
- `.agents/skills/`: 企業分析・採用情報調査に使う Codex skill 定義。

## Data

GitHub Pages 用 artifact は `github-pages/report/` に `.enc` file と manifest として保存する。viewer は入力された合言葉から復号鍵を作り、ブラウザ内で report を復号する。

## Local Use

静的 viewer だけを確認する場合は、repository root で簡易 HTTP server を立てる。

```bash
python3 -m http.server 8000
```

その後、`http://localhost:8000/` を開く。artifact を読むには、別途共有された合言葉が必要である。

## Deploy

`main` branch へ push すると、GitHub Actions が `index.html` と `github-pages/report/` を Pages artifact として deploy する。
