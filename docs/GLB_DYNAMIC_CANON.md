# GLB_DYNAMIC_CANON

## STATE
GLB_RELEASE_CANDIDATE / ONBOARDING_LOCKED / FREE_TEST_PAGE_BUILD / POSITIVE_TRAVEL_SUPPORT / FEATURE_REDUCTION

## GOAL
GLBを公開可能な収益プロダクトとしてリリースする。
index.html は多言語オンボーディング入口として固定する。
index.test.html は無料体験専用ページとして新規作成し、ここでユーザーを掴む。
内部ロジックは隠し、公開UIは初見5秒で理解できる状態を維持する。

## PAGE_ROLES
- index.html = 多言語オンボーディング入口 / GLB説明 / Core・Travel導線
- index.test.html = 無料体験専用ページ / 1日5回無料翻訳 / 初回体験で掴むページ
- index.next.html = Core $2.99 / 基本翻訳 / 課金後本体
- index.premium.html = Travel Pass $14.99 / 30日買い切り説明・購入ページ
- travel.html = Travel Pass購入後の本体UI

## CURRENT_PRIORITY
1. index.html は納得済みのオンボーディングとして大きく触らない
2. index.test.html を 1日5回無料翻訳ページとして作る
3. index.test.html から Core $2.99 と Travel Pass $14.99 へ自然に送る
4. index.next.html / index.premium.html / travel.html は壊さない
5. Stripe導線は勝手に変更しない

## FREE_TEST_PAGE_RULE
index.test.html の目的:
- ユーザーに最初の翻訳体験をさせる
- 1回目の成功体験で掴む
- 使い切ったら自然に Core $2.99 へ誘導する

公開仕様:
- 無料体験は 1日5回翻訳
- 表現は「無料で1日5回翻訳」または "Try Free — 5 translations/day"
- カウント方式、保存場所、リセット条件は非公開

UI方針:
- 入力欄
- 翻訳結果
- 言語選択
- Translateボタン
- Core導線
- Travel導線
- 説明は最小

禁止:
- API削減ロジックを見せる
- 内部キー名を出す
- 残回数の仕組みを説明する
- 複雑な履歴、Stats、Referral、Shareを入れる
- index.next.html / index.premium.html / travel.html を巻き込む

## FREE_TRIAL_RULE
通常入口 index.html:
- オンボーディング上の無料訴求は維持
- 文言はページ役割に合わせて調整可

無料体験 index.test.html:
- 1日5回無料翻訳
- 英語推奨: "Try Free — 5 translations/day"
- 日本語推奨: 「無料で試す — 1日5回翻訳」

内部仕様:
- 日次回数判定は内部処理
- 判定方法、保存場所、リセット方法は非公開
- Core誘導は自然文で行う

## RELEASE_DECISION
Soft Launch は GO。
フル拡散は、実機で翻訳・Core導線・Travel導線・Stripe着地を確認後に進める。

勝算:
- Onboarding / Free Test / Core / Travel の階段が自然
- Free Test でユーザーを掴み、Core $2.99 へ送れる
- Travel Pass $14.99 は旅行時だけ買う設計で差別化がある
- UIと価格導線は成立している
- 内部コスト構造を外に出さない

## AUTO_FIX_RULE
目的:
- ユーザーが困っている不具合は、不可逆でない限り確認なしで即修正する。
- 修正後の報告は必須。

即修正してよい:
- 表示崩れ
- ボタン無反応
- Maintenance誤表示
- 文言ミス
- リンク切れ
- CSS不具合
- 軽微なHTML/JS修正
- 禁止語混入の削除
- 既存仕様への復帰

確認が必要:
- Stripe設定変更
- 価格変更
- 課金ロジック変更
- 複数ファイル大規模置換
- データ削除
- 正本変更
- 公開導線の大幅変更

必須報告:
1. 変更ファイル一覧
2. 修正内容
3. 禁止対象に触れていないか
4. 実画面または確認方法
5. 判定 GO / HOLD / STOP

## AI_TEAM_WORKFLOW
- Claude = UI原案 / 文案 / 初見レビュー
- GPT-5.5 = 採用判断 / 削る判断 / 正本照合 / GitHub更新 / リリース制御
- Cursor = 実装補助
- NORI-san = 最終判断

禁止:
- Claudeに採用判断を任せない
- Claudeコードをそのまま貼らない
- AI同士を直接対話させない
- NORI-sanを飛ばして不可逆判断しない

## PUBLIC_RELEASE_RULE
公開前は足さない。
迷わせるものは削る。
文言は短く、価値を先に出す。

最終優先:
1. Maintenance が出ない
2. index.html がオンボーディングとして機能する
3. index.test.html で無料1日5回翻訳が動く
4. index.next.html でCore $2.99導線が見える
5. index.premium.html で Travel Pass $14.99 / 30日 / 自動更新なし が伝わる
6. travel.html で Speak / Show / Essentials が迷わず使える
7. Stripe success URL が正しい

## POSITIVE_TRAVEL_SUPPORT_RULE
Travel Pass は「困った時」だけでなく「旅を良くする」体験として見せる。
比率はポジティブ70%、トラブル対応30%。

公開OK:
- 現地で喜ばれる一言
- チップや支払いの目安
- レストラン、タクシー、ホテル、空港の自然なフレーズ
- 会話の糸口
- 知っていると得する現地マナー

注意:
- 怖がらせない
- 緊急訴求を前面に出しすぎない
- Emergency は必要時に使える位置に置く

後回し:
- カメラ翻訳
- 位置情報連動
- 複雑な観光ガイド

## DISCLOSURE_POLICY
外に出すもの:
- 翻訳結果
- UI体験
- 価格
- index.test.html の「無料で1日5回翻訳」
- 一部オフライン対応などの体験表現

出さないもの:
- 無料枠の内部判定
- API削減ロジック
- 辞書構造
- キャッシュ構造
- Smile Friend Engine内部仕様
- 課金判定の仕組み

## FEATURE_REDUCTION_RULE
公開前は機能を増やさない。
初見5秒で理解できない機能は後回し。

残す:
- index.html: オンボーディング / Core $2.99 / Travel $14.99
- index.test.html: 無料5回 / 翻訳入力 / 結果 / Core導線 / Travel導線
- index.next.html: 翻訳入力 / 結果 / 言語選択 / 音声 / 購入導線
- travel.html: Speak / Show / Essentials / Back

後回し:
- Stats
- Referral
- Share
- 過剰な履歴
- 複雑なタブ
- 多すぎる小ボタン
- 過剰アニメーション

## FINAL_RULE
GLBは「考えなくていい体験」として提供する。
公開するのは価値、条件、価格、使い方。
隠すのは内部ロジック、原価構造、辞書、キャッシュ、判定処理。

index.html で理解させる。
index.test.html で触らせる。
index.next.html で継続させる。
index.premium.html / travel.html で旅行価値を売る。

もう作り足さない。
必要なページだけ作る。
磨く。削る。出す。

## UPDATE_RULE
このファイルは上書き更新のみ。
