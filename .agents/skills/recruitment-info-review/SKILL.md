---
name: recruitment-info-review
description: recruitment-info-research が返したインターン、選考、説明会情報 YAML を、固定 target、最新性、source tier、status enum、締切根拠、MyPage 制約、出力契約に照らして確認し、単一 review YAML だけを返す review 用 skill。
---

# Recruitment Info Review

## 目的

- `recruitment-info-child-orchestrator` から起動される review agent で使う。
- review 対象は、指定された recruitment info YAML と target request。
- reviewer は調査 YAML を書き換えない。review YAML だけを返す。

## 入力

- recruitment info YAML path
- target request
- review output path
- 必要に応じて `recruitment-info-research/references/output-contract.md`

## 出力契約

- 単一 YAML オブジェクトだけを返す。
- Markdown fence や説明コメントを混ぜない。
- review output path が指定されている場合は、同じ YAML をその path に保存する。

```yaml
review:
  verdict: "pass|revise"
  findings: []
  passed_checks: []
  pass_rationale: null
  residual_risks: []
```

`finding` schema:

```yaml
severity: "high|medium|low"
category: "output_contract|status_evidence|source_quality|freshness|company_scope|deadline_consistency|mypage_limitation|actionability"
section: "company|briefings|internships|hiring|uncertainties|sources"
message: ""
suggested_fix: ""
```

## レビュー範囲

reviewer は追加 web 調査をしない。保存済み YAML、target request、必要に応じて `recruitment-info-research/references/output-contract.md` だけを根拠にする。

### Contract

- YAML が `recruitment-info-research/references/output-contract.md` の主要 field、section、status enum、source kind、禁止 field に従っているか。
- YAML が `summary`、`run_metadata`、`company.report_used`、`action_items`、`company.recruiting_entities`、item-level `recruiting_entity`、`duration_category` を持っていないか。
- 説明会、インターン、本選考が `briefings`、`internships`、`hiring` に分離されているか。
- 最短締切を `briefings[].reservation_deadline`、`internships[].dates.application_deadline`、`hiring[].application_deadline` から導出できるか。

### Freshness And Status

- 日付、締切、`open` / `closed` status、イベント availability が既存 report や過年度情報に依存していないか。
- `open` が公開一覧や詳細 page の存在だけで付いていないか。公式 source で現在応募・予約受付中、または受付期間内であることが確認できない場合は `mypage_required`、`open_likely`、`unknown` への修正を求める。
- 本選考の今年度情報が未公開の場合に、前年度以前の公式情報で今年度の締切、受付 status、応募可否を埋めていないか。
- `open_likely`、`media_only`、`closed_public_but_form_visible` には説明用 `uncertainties` があるか。
- MyPage / login / JS / capacity-dependent form の制約が `evidence.note` または `uncertainties` で追跡できるか。

### Source Quality

- 公式採用 site top、募集要項、応募コース、選考 flow、FAQ、MyPage 入口、求人一覧、イベント一覧、説明会一覧、インターン一覧、企業掲載の採用媒体を確認したことが、source、evidence note、または `uncertainties` から追跡できるか。
- 公式一覧に pagination、filter、search、tag、category、年度 tab がある場合、検索条件、確認件数、未確認条件が evidence note または `uncertainties` に残っているか。
- 公式一覧の完全網羅を公開情報だけで確認できない場合でも、確認した URL、filter 条件、表示件数、総件数または総件数不明理由、page count または pagination 不明理由、取得できた item 数、未確認条件、次確認先が `evidence.note` または `uncertainties` で追跡でき、YAML が完全網羅を主張していなければ、その制約だけを理由に `revise` にしない。
- `source_tier` と `source_kind` が分離され、企業掲載の LabBase、マイナビ、リクナビ等の採用媒体 page が `official_platform` として扱われているか。
- 前年度以前または対象年度外の企業公式情報が `official_historical` として扱われ、今年度未確認であることが `note`、`used_for`、または `uncertainties` で分かるか。
- `third_party` または `user_generated` source が action-critical field の補足、または公式 source にない別求人・別イベント・別応募 route の根拠にだけ使われているか。
- 公式 source の補足、再掲、言い換えだけの `third_party` または `user_generated` が残っていないか。

### Item Boundary

- 複数件がある場合に、応募者が別アクションを取る単位で item が分かれているか。
- 異なる日程、締切、対象、URL、route、予約導線、応募 action が 1 item に混ざっていないか。
- 説明会の同一 URL / 同一予約導線に複数日程がある場合、全日程が `briefings[].sessions` に分かれ、top-level の `datetime` と `reservation_deadline` が最短予約締切に対応する 1 件だけになっているか。
- 公式一覧、職種検索、イベント一覧、インターン一覧、採用媒体検索に複数 item があるのに、応募者の別アクションを代表 item だけへ丸めていないか。
- 本選考で job-theme、研究テーマ、職種テーマ、個別テーマ URL だけが異なり、応募 route、締切、提出物、選考 flow、応募アクションが同じ item が多数に分裂している場合は、`hiring[].themes` への統合を求める。
- 公式一覧で詳細確認不能な item を削る場合、`uncertainties` に名称、URL、確認不能理由、次確認先が残っているか。

### Company Scope

- 会社単位で公開されている公式 item を、件数削減、職種指定、関心領域、要約目的で削っていないか。
- グループ会社単独の item、外部企業との共催・登壇イベント、イベント運営会社の item が、調査対象会社本体への応募・予約・確認アクションではないのに `briefings`、`internships`、`hiring` に残っていないか。
- 配属先企業、研究所、部門、受入先が明示されている item で、`assignment_entity` または `uncertainties` から違いを追跡できるか。

### Internship Detail

- インターンについて、締切だけでなく `activity_summary`、`theme_structure`、`themes`、`work_model`、`duration` が公開情報から埋められているか。
- 公開情報で不明なインターン内容は推測せず、確認先が `uncertainties` にあるか。
- インターン締切確認の依頼では、選考詳細より締切、応募開始日、応募 URL、status 根拠が優先されているか。

## Verdict

- `pass`: 修正要求がない場合。`findings: []` とし、`passed_checks`、`pass_rationale`、`residual_risks` を埋める。
- `revise`: 修正要求が 1 件以上ある場合。`findings` を 1 件以上含め、`pass_rationale: null` とする。

## 禁止事項

- recruitment info YAML を書き換えない。
- 追加 web 調査をしない。
- 指定された review output path 以外へ保存しない。
