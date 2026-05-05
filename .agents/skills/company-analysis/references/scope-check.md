# Scope Check

このファイルは、調査の最初に子オーケストラが指定した `scope` が分析可能な応募単位として成立しているか確認するときに読む。

## 判定

- **継続**: 軽微な曖昧さは `scope.ambiguity_note` に残して分析を続ける。
- **修正依頼**: 致命的問題がある場合は、通常の company-analysis YAML を作らず、子オーケストラに scope 修正を依頼する YAML だけを返す。

## 確認手順

1. 子オーケストラが与えた `company_name`、`survey_date`、`slug`、`applicant_graduation_cohort`、`scope` を、`../SKILL.md` の **上位オーケストラが渡すデータの読み方** に従って確認する。`slug` は schema 用識別子としてだけ扱う。
2. 子オーケストラが固定した `target_application_unit` と `hiring_entity_name` が分析可能か確認する。
3. 子オーケストラが固定した `target_application_unit` が公開情報と整合しているか確認する。
4. 致命的問題があれば、分析へ進まず **修正依頼 YAML** だけを返す。

## 致命的問題

- field の欠落・型不正・空文字
- `target_application_unit` が会社名、部署名、研究所名、技術領域名、PR ラベルだけで、応募ルートや職種トラックとして固定できない。
- `hiring_entity_name` が採用主体として不明、または対象求人・応募ルートと別 entity になっている。
- `target_application_unit` と `role_family` が明確に矛盾している。
- 複数の応募単位が 1 target に混ざっており、単一 YAML として評価できない。
- internship、経験者採用、新卒相当 route が混在し、子オーケストラがどれを評価対象に固定したか判断できない。

## role_family enum

- `researcher`: 研究職、研究員、Research Scientist。研究所や研究職としての入口が主。
- `research_engineer`: R&D職、AI/Data Research Scientist、研究と実装の中間。事業実装に近い研究開発。
- `engineer`: SWE、SE、開発エンジニア、アプリケーションエンジニア、セキュリティエンジニアなど。
- `consultant`: コンサルタント、サイバーコンサル、技術コンサルなど。実装主体ではなく課題解決・支援・変革が主。
- `generalist`: 技術系総合職など、入社時点で研究開発、設計、生産技術、品質、技術営業などに分かれ得るもの。
- `other`: 上記に安全に分類できない応募単位。使う場合は `scope.ambiguity_note` に分類不能な理由を残す。

## 修正依頼 YAML

```text
scope_check:
  verdict: revise_scope
  slug: <schema 用 slug>
  company_name: <子オーケストラ指定 company_name>
  applicant_graduation_cohort: <子オーケストラ指定 applicant_graduation_cohort>
  target_application_unit: <子オーケストラ指定 target_application_unit>
  hiring_entity_name: <子オーケストラ指定 hiring_entity_name>
  problems:
    - severity: high | medium
      field: target_application_unit | hiring_entity_name | role_family | alternative_application_units | workplace_entity_name | scope
      message: <日本語>
      suggested_fix: <日本語>
  suggested_scope:
    target_application_unit: <候補。分からなければ null>
    hiring_entity_name: <候補。分からなければ null>
    role_family: <候補。分からなければ null>
    alternative_application_units:
      - <候補。候補がなければ空 list []>
    workplace_entity_name: <候補。分からなければ null>
```

## 制約

- `scope_check.verdict: revise_scope` を返す場合も、子オーケストラ指定 handoff path 以外へのファイル作成、保存、Markdown rendering はしない。
- `suggested_scope.alternative_application_units` は list とし、候補がない場合は `[]` を使う。`unknown` や説明文字列で埋めない。
- 孫調査エージェントは scope を勝手に修正して分析を続けてはいけない。修正後の scope は子オーケストラが決める。
