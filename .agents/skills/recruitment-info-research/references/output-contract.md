# 出力契約

この file は recruitment-info の YAML schema、status enum、item boundary、source policy、Markdown 要約順序の正本である。各 skill と prompt はこの file を参照し、同じ規則を再定義しない。

## YAML

次の構造に従い、単一の YAML オブジェクトだけを返す。Markdown fence で囲まない。

使用できる status 値:

- `open`: 現在の公式 source で、応募または予約を受け付けていることを確認できる。`official_owned` と `official_platform` は公式 source として扱う。公開一覧や詳細 page の存在だけでは `open` にしない。
- `scheduled`: 現在の公式 source で、将来の応募期間または予約期間を確認できる。`official_owned` と `official_platform` は公式 source として扱う。
- `closed`: 現在の公式 source で、対象の受付期間が終了済み、または公開日程がすべて過去であることを確認できる。
- `unknown`: 現在の公開 source だけでは status を判定できない。
- `open_likely`: 公式の入口は存在し、`third_party` または `user_generated` では受付中と分かるが、公式詳細が MyPage などの内側にある。
- `mypage_required`: 公式公開ページが、status、日程、予約詳細、残枠、応募画面到達可否の確認に MyPage / login を要求している。
- `media_only`: `third_party` または `user_generated` だけが根拠で、かつ公式 source には対応する求人、イベント、応募 route が見つからない。企業が掲載・管理する採用媒体 page は `official_platform` であり、`media_only` にしない。
- `closed_public_but_form_visible`: 公式公開締切は過去だが、公式応募フォーム自体は表示されている。

```yaml
company:
  name: ""
  target:
    applicant_graduation_cohort: null
    target_year: null
  researched_at: "YYYY-MM-DD"
briefings:
  - name: ""
    assignment_entity: null
    status: "open|scheduled|closed|unknown|open_likely|mypage_required|media_only|closed_public_but_form_visible"
    event_type: "company_briefing|role_briefing|internship_briefing|research_open_house|joint_event|other"
    target: ""
    datetime: null
    reservation_deadline: null
    sessions:
      - datetime: null
        reservation_deadline: null
        status: "open|scheduled|closed|unknown|open_likely|mypage_required|media_only|closed_public_but_form_visible"
        format: "online|in_person|hybrid|unknown"
        location: null
        note: null
    format: "online|in_person|hybrid|unknown"
    location: null
    event_url: ""
    selection_linkage: "yes|no|unknown"
    evidence:
      - source_tier: "official|unofficial"
        source_kind: "official_owned|official_platform|official_historical|third_party|user_generated|unknown"
        title: ""
        url: ""
        checked_at: "YYYY-MM-DD"
        note: ""
internships:
  - name: ""
    assignment_entity: null
    status: "open|scheduled|closed|unknown|open_likely|mypage_required|media_only|closed_public_but_form_visible"
    target_roles: []
    target_cohorts: []
    eligibility: ""
    activity_summary: null
    theme_structure: null
    themes: []
    work_model: null
    duration: null
    dates:
      application_start: null
      application_deadline: null
      event_start: null
      event_end: null
      notes: []
    format: "online|in_person|hybrid|unknown"
    location: null
    compensation: null
    selection_required: "yes|no|unknown"
    selection_process: []
    apply_url: ""
    evidence:
      - source_tier: "official|unofficial"
        source_kind: "official_owned|official_platform|official_historical|third_party|user_generated|unknown"
        title: ""
        url: ""
        checked_at: "YYYY-MM-DD"
        note: ""
hiring:
  - route_name: null
    assignment_entity: null
    status: "open|scheduled|closed|unknown|open_likely|mypage_required|media_only|closed_public_but_form_visible"
    application_url: null
    application_deadline: null
    themes:
      - name: ""
        url: null
        assignment_entity: null
        application_deadline: null
        note: null
    steps: []
    required_materials: []
    tests: []
    interviews: []
    research_or_coding_component: null
    online_support: null
    evidence:
      - source_tier: "official|unofficial"
        source_kind: "official_owned|official_platform|official_historical|third_party|user_generated|unknown"
        title: ""
        url: ""
        checked_at: "YYYY-MM-DD"
        note: ""
uncertainties:
  - topic: ""
    detail: ""
    next_check: ""
sources:
  - source_tier: "official|unofficial"
    source_kind: "official_owned|official_platform|official_historical|third_party|user_generated|unknown"
    title: ""
    url: ""
    checked_at: "YYYY-MM-DD"
    used_for: []
```

## 複数件の扱い

- `briefings`、`internships`、`hiring` は、応募者が別の参加・応募・確認アクションを取る単位で item を分ける。
- 同じ説明会名でも、URL、対象、説明内容、予約導線が異なる場合は別 item にする。同一 URL と同一予約導線で複数日程がある場合は 1 item にまとめ、全日程を `sessions` に列挙する。
- `briefings[].datetime` と `briefings[].reservation_deadline` は summary / ToDo 用の代表値であり、最短の `sessions[].reservation_deadline` と、それに対応する `sessions[].datetime` だけを入れる。複数日時を `/` 区切りで入れない。
- 同じインターン名でも、course、theme、対象職種、応募締切、応募資格、選考有無のいずれかが異なる場合は別 item にする。
- 同じ本選考でも、応募 route、締切、提出物、選考 flow、応募アクションが異なる場合は別 item にする。
- 本選考の差分が job-theme、研究テーマ、職種テーマ、個別テーマ URL だけで、応募 route、締切、提出物、選考 flow、応募アクションが同じ場合は、別 `hiring` item にせず同じ item の `themes` に列挙する。
- 公式求人一覧、職種検索、イベント一覧、インターン一覧、企業掲載の採用媒体検索に会社単位の item が複数ある場合は、代表 item へ丸めず、応募者が別の応募・予約・確認アクションを取る単位で列挙する。
- 公式求人一覧で `JOBマッチングコース（研究所コース）` のような親 route と、`Physical AIの研究開発` のような job-theme が同じ応募 action に属する場合は、親 route を `hiring` item とし、個別テーマを `themes` に入れる。個別求人が締切、提出物、選考 flow、応募 action を別に持つ場合だけ別 item にする。
- 公式一覧で item の存在は分かるが、詳細が JS、MyPage、login、掲載終了、capacity-dependent form で確認できない場合は、存在確認 item または `uncertainties` に名称、URL、確認不能理由、次確認先を残す。
- 公式一覧、職種検索、イベント検索、インターン検索で pagination、filter、search、tag、category、年度 tab を使った場合は、検索条件、確認件数、未確認条件があればその理由を evidence note または `uncertainties` に残す。
- 並び順は、`open`、`scheduled`、`open_likely`、`mypage_required`、`closed_public_but_form_visible`、`unknown`、`media_only`、`closed` の順を優先し、同じ status では締切が早いものを先に置く。締切不明の item は、締切がある item の後に置く。
- 件数が多い場合も、会社単位で公開されている公式 source 付き item は削らない。職種や関心領域を item の採否条件にしない。`official_platform` 付き item は公式 source 付き item として扱う。`third_party` または `user_generated` だけの item は、公式 source にない別求人、別イベント、別応募 route で、応募者が別アクションを取れる場合だけ `media_only` として低順位に置く。
- グループ会社単独の採用、説明会、インターン、外部企業との共催・登壇イベント、イベント運営会社の item は、調査対象会社本体への応募・予約・確認アクションでない限り `briefings`、`internships`、`hiring` に保存しない。除外した item 名を網羅的に `uncertainties` へ残す必要もない。
- 最短締切 summary は YAML に保存しない。UI やレポートで必要な場合は、`briefings[].reservation_deadline`、`internships[].dates.application_deadline`、`hiring[].application_deadline` から導出する。
- 応募者向け ToDo は YAML に保存しない。UI やレポートで必要な場合は、`briefings`、`internships`、`hiring`、`uncertainties` から導出する。

## 項目説明

### `company`

- `name`: 調査対象の正式社名または公式採用ページで使われる会社名。調査入口としての主対象をここに置く。
- `target.applicant_graduation_cohort`: 応募者 cohort。例: `2028卒`、`2027年3月修了予定`。不明なら `null`。
- `target.target_year`: 調査対象年度または採用年度。例: `2027 new graduate`、`2028 internship`。不明なら `null`。
- `researched_at`: 調査日。`YYYY-MM-DD` 形式で書く。

### `internships`

- `name`: インターンまたは仕事体験 program の公式名称。媒体名ではなく program 名を書く。
- `assignment_entity`: 実施部門、受入会社、配属先、職場受入先、研究所など、参加先が別に明示されている場合に書く。不明または共通募集だけなら `null`。グループ会社名やイベント運営会社名を記録する目的では使わない。
- `status`: その program の受付状態。企業掲載の採用媒体で受付中なら公式根拠として扱う。`third_party` または `user_generated` でしか受付中と分からない場合は `open_likely` または `media_only` を使う。
- `target_roles`: 対象職種、テーマ、部門。研究開発、AI、データサイエンスなど、応募判断に効く粒度で書く。
- `target_cohorts`: 対象 cohort。例: `2028卒`、`博士課程`、`修士1年`。公開情報にない場合は `[]`。
- `eligibility`: 応募資格。学年、専攻、国籍・居住条件、勤務可能場所など、応募可否に関わる条件を短くまとめる。
- `activity_summary`: 実施内容の要約。研究業務、開発業務、職場受入、講義、ワークショップ、グループワーク、成果発表など、参加者が何をするかを書く。不明なら `null`。
- `theme_structure`: テーマの決まり方。例: `応募開始後にテーマ一覧公開`、`複数テーマから選択`、`全員が同一プロダクトを開発`、`配属部署ごとに個別課題`。不明なら `null`。
- `themes`: 公開されているテーマ一覧。研究テーマ、開発テーマ、業務テーマを応募判断に効く粒度で列挙する。テーマが未公開なら `[]` にし、確認先を `uncertainties` に書く。
- `work_model`: 参加者の作業モデル。例: `職場受入で個別配属`、`全員が同一プロダクトを開発`、`チームで共通課題に取り組む`、`研究テーマごとに配属`。不明なら `null`。
- `duration`: 実施期間の自然言語表現。例: `1か月から3か月程度`、`2日間`、`半日`。不明なら `null`。
- `dates.application_start`: 応募開始日時。不明なら `null`。
- `dates.application_deadline`: 応募締切日時。不明なら `null`。時刻がある場合は必ず含める。
- `dates.event_start`: 実施開始日。不明なら `null`。
- `dates.event_end`: 実施終了日。不明なら `null`。
- `dates.notes`: 日付に関する補足。例: `テーマにより日程が異なる`、`定員到達で締切`。
- `format`: `online`、`in_person`、`hybrid`、`unknown` のいずれか。複数形式がテーマ依存なら `hybrid` とし、補足を `dates.notes` または `location` に書く。
- `location`: 実施場所。オンラインのみなら `null` でもよい。拠点名が複数ある場合は短く列挙する。
- `compensation`: 報酬、日当、時給、交通費、宿泊補助。未確認なら `null`。
- `selection_required`: 選考が明示されていれば `yes`、不要と明示されていれば `no`、不明なら `unknown`。
- `selection_process`: ES、適性検査、書類選考、面接、課題など。順序が分かる場合は順序通りに書く。
- `apply_url`: 応募または詳細確認 URL。MyPage 内限定の場合は公開入口 URL を入れる。
- `evidence`: program の status、締切、対象、選考を支える source。最低 1 件は入れる。

### `briefings`

- `briefings` は説明会、セミナー、open house、合同イベントだけを入れる section。
- `name`: 説明会、セミナー、open house、合同イベントの名称。
- `assignment_entity`: 説明対象の配属先企業、研究所、部門が明示されている場合に書く。不明または全社説明なら `null`。グループ会社名、外部主催者、共催企業、イベント運営会社名を記録する目的では使わない。
- `status`: 予約可能性。公開日程がすべて過去なら `closed`、MyPage 内確認なら `mypage_required`。
- `event_type`: もっとも近い分類を使う。
  - `company_briefing`: 会社全体説明会。
  - `role_briefing`: 職種別説明会。
  - `internship_briefing`: インターン説明会。
  - `research_open_house`: 研究所見学会、研究 open house。
  - `joint_event`: 合同説明会、グループ会社合同イベント。
  - `other`: 上記以外。
- `target`: 対象者。例: `2028卒`、`博士課程`、`技術系志望者`。
- `datetime`: 開催日時。複数日程がある場合は、最短予約締切に対応する開催日時だけを入れる。不明なら `null`。複数日時を `/` 区切りで入れない。
- `reservation_deadline`: 予約締切。時刻がある場合は含める。不明なら `null`。複数日程がある場合は最短の予約締切だけを入れ、全日程は `sessions` に列挙する。複数締切を `/` 区切りで入れない。
- `sessions`: 同一説明会・同一 URL・同一予約導線に複数日程がある場合の全日程。日程が 1 件だけでも、日程と締切の対応が重要な場合は 1 件入れてよい。
  - `sessions[].datetime`: その回の開催日時。不明なら `null`。
  - `sessions[].reservation_deadline`: その回の予約締切。不明なら `null`。
  - `sessions[].status`: その回の受付状態。日程別 status が不明で item 全体と同じなら item の `status` と同じ値を入れる。
  - `sessions[].format`: その回の開催形式。item 全体と同じなら item の `format` と同じ値を入れる。
  - `sessions[].location`: その回の開催場所。item 全体と同じまたはオンラインなら `null` でもよい。
  - `sessions[].note`: 日程別の補足。不明または不要なら `null`。
- `format`: `online`、`in_person`、`hybrid`、`unknown`。
- `location`: 現地開催場所。オンラインのみなら `null`。
- `event_url`: 詳細または予約 URL。
- `selection_linkage`: 選考連動が明示されていれば `yes`、選考と無関係と明示されていれば `no`、不明なら `unknown`。
- `evidence`: 日程、予約締切、選考連動を支える source。

### `hiring`

- `hiring` は本選考・採用 route だけを入れる section。route ごとに 1 item とし、インターン選考や説明会予約はここに混ぜない。
- `assignment_entity`: 配属先企業、事業会社、研究所、部門など、配属先が明示されている場合に書く。不明なら `null`。採用主体、求人掲載主体、採用媒体運営者を記録する目的では使わない。
- `status`: 本選考または採用 route の受付状態。締切が MyPage 依存なら `mypage_required` を使う。今年度の本選考情報が未公開で、前年度以前の情報しかない場合は `unknown` とし、過年度情報だけを根拠に `open`、`scheduled`、`closed` にしない。
- `route_name`: 応募 route 名。例: `研究職`、`JOBマッチングコース（研究所コース）`、`Engineer / Researcher`。
- `application_url`: 応募または MyPage 入口 URL。不明なら `null`。
- `application_deadline`: 本選考または採用 route の応募締切。公開情報で不明なら `null` とし、MyPage 依存や今年度未公開などの理由を `uncertainties` に書く。前年度以前の締切で今年度の値を埋めない。
- `themes`: 同一応募 route、同一締切、同一提出物、同一選考 flow、同一応募アクション内で選べる job-theme、研究テーマ、職種テーマの一覧。個別テーマ URL があれば `themes[].url` に入れる。テーマ別の配属先や締切が補足として出ているが route を分けるほどではない場合は、`themes[].assignment_entity`、`themes[].application_deadline`、`themes[].note` に残す。テーマ別に締切、提出物、選考 flow、応募アクションが本当に異なる場合は別 `hiring` item にする。
- `steps`: 公開されている選考 step。例: `ES`、`適性検査`、`書類選考`、`研究発表`、`面接`。前年度以前の公式情報を使う場合は、`evidence.source_tier: official`、`evidence.source_kind: official_historical` とし、`evidence.note` に過年度公式情報であることを書く。
- `required_materials`: 提出物。例: `履歴書`、`研究概要`、`成績証明書`、`発表リスト`、`GitHub URL`。前年度以前の公式情報を使う場合は、今年度で未確認であることを `uncertainties` または `evidence.note` に残す。
- `tests`: SPI、適性検査、coding test、技術課題など。
- `interviews`: 面接回数、形式、online / in person、研究所面談など。分からなければ `[]`。
- `research_or_coding_component`: 研究発表、研究概要、論文リスト、coding test、技術課題など、研究志向者に特に関係する要素。不明なら `null`。
- `online_support`: online 対応の有無。例: `一次面接はオンライン`、`MyPage上で予約`。不明なら `null`。
- `evidence`: 選考 flow と応募資格を支える source。

### `uncertainties`

- `topic`: 未確認点の短い名前。例: `MyPage内締切`、`研究職残枠`。
- `detail`: 何が未確認で、なぜ公開情報だけでは確定できないか。
- `next_check`: 次に確認すべき場所または行動。例: `公式MyPageでテーマ別締切を確認`。

### `sources`

- `source_tier`: `official` または `unofficial`。対象企業が出している情報は、企業自社 site でも採用媒体掲載でも `official` とする。記事、就活メディア編集部、口コミ、体験談、まとめ、SNS、掲示板は `unofficial` とする。
- `source_kind`: source の媒体種別。
  - `official_owned`: 対象企業の自社採用 site、公式 MyPage 入口、公式 PDF、企業ドメインの求人・イベント page。
  - `official_platform`: LabBase、マイナビ、リクナビなどの採用媒体上で、対象企業が掲載・管理している求人、インターン、イベント page。
  - `official_historical`: 対象企業が出した前年度以前または対象年度外の公式情報。選考 flow や提出物の参考に使えるが、今年度の締切、受付 status、応募可否の根拠にしない。
  - `third_party`: 記事、就活メディア編集部、まとめ、イベント運営元の独自告知など、対象企業が直接出していない情報。
  - `user_generated`: 口コミ、掲示板、SNS、選考体験投稿など投稿者ベースの情報。
  - `unknown`: 発行主体を判定できない場合。
- `title`: source のページ名または資料名。
- `url`: source URL。
- `checked_at`: その source を確認した日。`YYYY-MM-DD`。
- `used_for`: その source を何に使ったか。例: `internship_deadline`、`selection_flow`、`event_schedule`。

## Markdown

chat 向け要約も求められた場合は、YAML から次の順序で要約を作る。

1. **最短締切**: 説明会申込、インターン申込、本選考申込の最短締切を並べる。
2. **説明会・イベント**: 日時、形式、予約締切、URL。
3. **インターン**: status、締切、対象、URL、根拠。
4. **本選考**: route、申込締切、step、test、interview、特殊な選考要素。
5. **未確認点**: 年度差、配属先の不明点、ログイン必須など。
6. **Sources**: `source_tier` と `source_kind` を分ける。

## 根拠ルール

- `official`: 対象企業が出している情報。`official_owned`、`official_platform`、`official_historical` を含む。
- `official_platform`: LabBase、マイナビ、リクナビなどの採用媒体上で対象企業が掲載・管理している求人、インターン、イベント page。企業自社 site と矛盾する場合は `official_owned` を優先するが、矛盾がなければ公式根拠として扱う。
- `official_historical`: 前年度以前または対象年度外の企業公式情報。`source_tier` は `official` だが、今年度の締切、受付 status、応募可否の根拠には使わない。
- `unofficial`: 対象企業が直接出していない情報。`third_party` と `user_generated` を含む。
- 現在の日程、締切、status、イベント availability の唯一の根拠として既存 report を引用しない。
- `third_party` と `user_generated` は、公式 source で埋まらない action-critical field を補う場合、または公式 source にない別求人、別イベント、別応募 route を示す場合だけ YAML に入れる。
- action-critical field は、応募締切、予約締切、応募開始日、受付 status、応募 URL、MyPage 内制約、応募可否に関わる資格条件を指す。
- `third_party` または `user_generated` が公式情報を補足、再掲、言い換えするだけなら、`evidence`、`sources`、`uncertainties`、`media_only` item のいずれにも入れない。
- 公式 source で存在が確認できる item に対して `third_party` または `user_generated` から締切や受付 status を補う場合は、item は `media_only` にせず、該当 `evidence.note` と `sources[].used_for` に `third_party_deadline`、`user_generated_status` などの用途を明記する。
- 今年度の本選考情報が未公開の場合は、`hiring[].application_deadline` を `null` にする。前年度以前の公式情報は選考 flow、提出物、研究発表有無の参考としてのみ使い、今年度の締切、受付 status、応募可否の根拠にしない。
- 前年度以前の公式情報を使う場合は、該当 source entry の `source_tier` を `official`、`source_kind` を `official_historical` にし、`note` または `used_for` に対象年度と今年度未確認であることを書く。
- 複数 source から推論した値は、推論内容を `note` に書き、根拠になった source entry を残す。
- `open_likely`、`media_only`、`closed_public_but_form_visible` を使う場合は、説明用の `uncertainties` entry を必ず入れる。
