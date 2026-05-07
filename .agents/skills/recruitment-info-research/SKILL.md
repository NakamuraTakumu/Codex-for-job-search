---
name: recruitment-info-research
description: 企業ごとのインターン、選考フロー、応募締切、企業説明会・採用イベント情報を、会社名、cohort、対象年度から最新の公開情報で検証して、出典付きの構造化レポートにまとめる skill。新卒応募、イベント参加判断、選考スケジュール確認で使う。
---

# Recruitment Info Research

## 目的

- 会社名、cohort、対象年度を seed として、説明会、インターン、本選考の応募アクション情報を会社単位で集める。
- 企業評価や company-analysis の再解釈は行わず、締切、受付状態、応募・予約 URL、選考 flow、未確認点を公開情報で検証する。
- 正本 artifact は [references/output-contract.md](references/output-contract.md) に従う単一 YAML オブジェクトに固定する。

## 入力契約

- **必須入力**: 会社名。
- **任意入力**: 応募者 cohort、対象年度、出力保存先。
- **不足時**:
  - 会社名がない場合だけ質問する。
  - cohort や対象年度がない場合は、調査時点で応募可能または直近公開の情報を対象にし、年度差を明記する。

## 入力として読まないもの

- 読んではいけない場所:
  - `report/company_analysis/companies/`
  - `report/company_analysis/data/`
  - ユーザーが明示した company-analysis report path
  - `report/recruitment-info/`
  - `document/recruitment_info_trial/`
  - `tmp/recruitment_info/`
- company-analysis report と既存 recruitment-info YAML は、会社情報 seed、応募単位、URL、締切、route、event、internship、未確認点の根拠として使わない。
- `output_yaml_path` が既存 file を指す場合も、保存前に内容を読まない。

## 正本参照

- **YAML schema、field 説明、status enum、item boundary、source policy**: [references/output-contract.md](references/output-contract.md) を正本にする。
- `SKILL.md` には調査手順と副作用条件だけを置く。schema や status 判断の詳細は本文に再定義しない。

## 公式探索 checklist

1 回の調査で次の入口を確認し、見つからないカテゴリは `uncertainties` に確認不能理由を残す。

- 公式採用 site の top、募集要項、応募コース、選考 flow、FAQ、応募者 MyPage / プレエントリー入口。
- 公式 site 内の求人一覧、職種検索、job-theme 一覧、イベント一覧、説明会一覧、インターン一覧、news / event / seminar 一覧。
- 企業掲載の採用媒体。LabBase、マイナビ、リクナビなど、対象企業が掲載・管理する page は `official_platform` として扱う。
- 一覧に pagination、filter、search、tag、category、年度 tab がある場合は、会社単位の新卒、インターン、説明会、本選考 item を落とさない条件で確認する。
- 検索条件、確認できた件数、未確認の一覧条件、JS / login / 掲載終了で開けない item は、evidence note または `uncertainties` に残す。

## 調査原則

- 必ず web で確認し、調査日を `company.researched_at` と source の `checked_at` に入れる。
- 職種、関心領域、company-analysis の応募単位で絞り込まない。職種、コース、テーマ、配属先は item の事実 field に記録する。
- 公開 source から到達できる会社単位の公式 item は、件数削減や要約目的で削らない。
- `source_tier` と `source_kind` を分ける。LabBase、マイナビ、リクナビなどの企業掲載 page は `official_platform` として扱う。
- `open` は公開 page の存在だけでは使わない。公式 source で現在受付中または受付期間内と確認できない場合は、output contract に従って `mypage_required`、`open_likely`、`unknown` などにする。
- グループ会社単独の item、外部企業との共催・登壇イベント、イベント運営会社の item は、調査対象会社本体への応募・予約・確認アクションでない限り正本 section から除外する。
- 応募者向け ToDo、最短締切 summary、run metadata は YAML に保存しない。下流 UI が正本 section から導出する。

## Workflow

1. **対象固定**:
   - 入力から会社名、cohort、対象年度を整理する。
   - company-analysis report path、`report/company_analysis/`、`report/recruitment-info/`、`document/recruitment_info_trial/`、`tmp/recruitment_info/` から既存情報を探さない。
   - 会社名、cohort、対象年度以外の採用事実は補わない。
2. **公式調査**:
   - **公式探索 checklist** の入口を確認する。
   - インターン、選考、説明会の各カテゴリで最低 1 回ずつ公式情報を探す。
   - 公式一覧ページがある場合は、会社単位で公開されている item を全件確認する。
   - 一覧条件、件数、制約を evidence note または `uncertainties` に残す。
3. **補助調査**:
   - 公式で埋まらない action-critical field だけを、`third_party` または `user_generated` で補う。
   - action-critical field は、応募締切、予約締切、応募開始日、受付 status、応募 URL、MyPage 内制約、応募可否に関わる資格条件を指す。
   - `third_party` または `user_generated` が公式情報を言い換えるだけ、または面接形式・体験談などを補足するだけなら、YAML に入れない。
   - `third_party` または `user_generated` は source tier、source kind、何を補ったか、今年度の公式根拠ではない限界を明記する。
   - 公式 source にない別求人、別イベント、別応募 route が `third_party` または `user_generated` だけで確認できる場合だけ、独立 item として `media_only` を使う。
4. **配属先確認**:
   - 配属先企業、研究所、部門、受入先が明示されている場合は、該当 item の `assignment_entity` に残す。
   - グループ会社名、外部主催者、共催企業、イベント運営会社は、応募締切や応募 URL の根拠説明に必要な場合だけ evidence note に自然文で書き、構造化 field としては保存しない。
   - 年度差、配属 entity 差があれば `uncertainties` に残す。
5. **出力整形**:
   - [references/output-contract.md](references/output-contract.md) を読み、単一 YAML オブジェクトだけを返す。
   - `output_yaml_path` が指定された場合は、full YAML artifact をその 1 ファイルへ保存する。
   - runner template から `output_yaml_path` を指定された場合は、chat へ full YAML artifact を出さず、保存 status だけを返す。
   - Markdown fence や説明文を混ぜない。

## 出力契約

- full artifact は [references/output-contract.md](references/output-contract.md) に従う単一 YAML オブジェクトだけにする。
- `output_yaml_path` がない直接実行では、full YAML artifact を chat に返す。
- `output_yaml_path` がある runner 実行では、full YAML artifact を `output_yaml_path` に保存し、chat には compact status YAML だけを返す。
- Markdown fence、説明文、summary、`action_items`、`run_metadata` を full YAML artifact に混ぜない。

## 完了条件

- インターン、選考、説明会の各カテゴリについて、確認済み情報または確認不能理由がある。
- **公式探索 checklist** の主要入口を確認し、一覧の検索条件、確認件数、未確認条件が evidence note または `uncertainties` で追跡できる。
- item boundary、status、source policy、section field が output contract に従っている。
- 変わり得る facts が既存 report や既存 recruitment-info YAML に依存していない。
- source tier、URL、確認日、年度差、配属 entity 差が追跡できる。
