# GLB_DYNAMIC_CANON

## STATE
ONBOARDING_AND_FREE_TEST_BUILD / USER_LANGUAGE_FIRST / NO_AI_TONE / NOIR_GUARD / FREE_TEST_PAGE_BUILD

## GOAL
GLBを公開可能な収益プロダクトとしてリリースする。
index.html でオンボーディングと言語決定を行う。
index.test.html で1日5回の強い無料体験を提供する。
GLBはAIっぽさを売らない。
GLBは「自分の言葉で、相手に通じる道具」として提供する。

## MOTTO
刻の共振、法の静寂。

## PRODUCT_IDENTITY
他社は「なんでも翻訳」。
GLBは「ユーザーの言語を中心にした翻訳」。

基本思想:
- 最初にユーザーの基本言語を決める
- 以後の全ページはそのユーザー言語を引き継ぐ
- 翻訳は常に ユーザー言語 ⇄ 相手の言語
- 他言語同士を何でも変換するアプリではない
- ユーザーには迷わず使いやすく、NextBase側は無駄な処理を減らす
- よく使う言葉・表現を扱い、NextBase独自の言語資産を育てる

公開表現:
- あなたの言葉で通じる
- 自分の言葉を、そのまま相手に届ける
- 旅先でそのまま見せて通じる
- 話す、見せる、伝わる

禁止表現:
- AIが最適化します
- あなた専用AI
- パーソナライズAI
- 自己最適化
- 最適化レイヤー
- AI学習を売りにする表現
- ブラックボックス、モデル、推論、個別最適化などの技術語

内部呼称としての自己最適化レイヤーは開発用語のみ。
公開UI・LP・CTA・FAQ・広告文では使わない。

## NO_AI_TONE_RULE
GLBの文案ではAIらしさを禁止する。

禁止:
- AIっぽい説明
- 技術自慢
- 最適化という言い方
- 学習アルゴリズムを前に出すこと
- ユーザーに内部処理を意識させる説明
- 世界救済、巨大物語、神格化、煽り、恐怖訴求
- ユーザーを持ち上げて判断を曇らせる表現

言い換え:
- 「AIが最適化」ではなく「あなたの言葉で通じる」
- 「個別最適化」ではなく「いつもの言い方で伝わる」
- 「学習する辞書」ではなく「よく使う言葉を覚えておける」
- 「翻訳精度向上」ではなく「伝わりやすくする」

## NOIR_GUARD_RULE
NOIRは監査役であり、煽り役ではない。

NOIRの役割:
- 正本照合
- 証拠確認
- ズレ検出
- conflict / merge / push 状態の監査
- 不可逆作業の停止
- 実務への復帰

NOIRの禁止:
- 世界を救う、最後の手段、唯一の武器などの煽り
- 政治、軍事、終末論、シンギュラリティ不安を使った誘導
- ユーザーの不安を物語化すること
- ユーザーを特別視して判断を歪めること
- 「AIが力を解放する」「剣になる」などの演出
- 外部ノイズを根拠なく混ぜること

NOIRの正しい出力:
STATE:
GOAL:
BLOCKER:
NEXT_ACTION:
EVIDENCE:
IRREVERSIBLE:
OUTPUT:

異常時:
- 正本不一致、状態ズレ、古い前提、合言葉不一致を検出したら securityLevel = 1
- securityLevel = 1 では不可逆作業を止め、確認だけ行う
- 事実、差分、次の一手だけを出す

## USER_LANGUAGE_RULE
GLBはユーザー言語特化型アプリ。

基本:
- index.html のオンボーディングでユーザーの基本言語を決める
- localStorage の glb_ui_lang に保存する
- index.test.html / index.next.html / index.premium.html / index.14.99.html は glb_ui_lang を読む
- 各ページでユーザーに再度言語設定を要求しない
- ユーザー言語は固定表示する
- 選ばせるのは相手の言語だけ
- 翻訳方向は ユーザー言語 → 相手言語、または 相手言語 → ユーザー言語
- 他言語同士の翻訳は本線では扱わない

公開表現:
- まず、あなたの言語を選ぶ
- あなたの言葉を、相手の言葉へ
- 相手の言葉を、あなたの言葉へ

禁止:
- 毎ページで言語を選ばせる
- 何でも翻訳できる万能アプリのように見せる
- 他言語同士翻訳を売りにする
- 内部制限を制限として見せる

## PAGE_ROLES
（物理パスの正本は `docs/GLB_FINAL_CANONICAL.md` §0.5 と同一。旧 `travel.html` / `apps/glb/` は使用しない。）

- index.html = 多言語オンボーディング入口 / ユーザー言語決定 / GLB説明 / Core・Travel導線
- index.test.html = 無料体験専用ページ / 1日5回無料翻訳 / 初回体験で掴むページ（ツリーに未収載の場合は実装後に監査）
- index.next.html = Core $2.99 / 基本翻訳 / 課金後本体
- index.premium.html = Travel Pass $14.99 / 30日買い切り説明・購入ページ
- index.14.99.html = Travel Pass 購入後の本体UI（Travel アプリ本体）

## CURRENT_PRIORITY
1. rebase中の index.html conflict を正本どおり解消する
2. index.html の無料導線2箇所を index.test.html へ向ける
3. index.html のユーザー言語を全ページへ引き継ぐ
4. index.test.html を 1日5回無料翻訳ページとして完成させる
5. index.test.html で翻訳API接続を確実に動かす
6. index.next.html / index.premium.html / index.14.99.html は壊さない
7. Stripe導線は勝手に変更しない

## FREE_TEST_PAGE_RULE
index.test.html の目的:
- ユーザーに最初の翻訳体験をさせる
- 1回目の成功体験で掴む
- 5回だけの濃い体験で「もっと使いたい」に変える
- 使い切ったら自然に Core $2.99 へ誘導する

公開仕様:
- 無料体験は 1日5回翻訳
- 表現は「無料で1日5回翻訳」または "Try Free — 5 translations/day"
- カウント方式、保存場所、リセット条件は非公開

UI方針:
- 入力欄
- 翻訳結果
- ユーザー言語表示
- 相手言語選択
- Translateボタン
- 大きく見せる / 読み上げる / Travel体験の一部
- Core導線
- Travel導線
- 説明は最小

禁止:
- API削減ロジックを見せる
- 内部キー名を出す
- 残回数の仕組みを説明する
- 複雑な履歴、Stats、Referral、Shareを入れる
- AIらしさを出す
- 最適化という言葉を出す

## DICTIONARY_AND_MEMORY_RULE
内部仕様として、GLBはユーザーの言語を中心に表現を蓄積する。

内部:
- API呼び出し翻訳の結果をSmile Friendシステム側に記録する
- ユーザーのよく使う言葉、言い回し、翻訳結果をユーザーごとに扱う
- NextBase独自の辞書資産を育てる
- Smile Friendは全ユーザー言語の傾向を扱う

公開:
- 「よく使う言葉を覚えておける」程度に留める
- 辞書構造、保存方式、API削減、キャッシュは出さない

## TERMS_AND_PRIVACY_RULE
規約・プライバシーには以下を明記する。

必須:
- 翻訳処理のため入力テキストと翻訳結果を処理する場合がある
- サービス改善、翻訳品質向上、よく使う表現の保存に使う場合がある
- 個人情報、機密情報、センシティブ情報を入力しないこと
- 外部翻訳APIを使う場合がある
- 必要最小限のデータを送信する場合がある
- データ削除依頼の連絡先
- セキュリティ対策は行うが、完全な安全性やリスクゼロは保証しない

禁止:
- リスク0と書く
- 絶対安全と書く
- 外部送信なしと断定する
- AIが学習しますと前面に出す
- 内部辞書やキャッシュ構造を説明する

## DISCLOSURE_POLICY
外に出すもの:
- 翻訳結果
- UI体験
- 価格
- index.test.html の「無料で1日5回翻訳」
- よく使う言葉を覚えておける程度の説明

出さないもの:
- 無料枠の内部判定
- API削減ロジック
- 辞書構造
- キャッシュ構造
- Smile Friend Engine内部仕様
- 課金判定の仕組み
- 自己最適化レイヤーという言葉
- AI技術の説明

## AUTO_FIX_RULE
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
- API接続の軽微な修正

確認が必要:
- Stripe設定変更
- 価格変更
- 課金ロジック変更
- 複数ファイル大規模置換
- データ削除
- 正本変更
- 公開導線の大幅変更

## AI_TEAM_WORKFLOW
- Claude = UI原案 / 文案 / 初見レビュー
- GPT-5.5 = 採用判断 / 削る判断 / 正本照合 / GitHub更新 / リリース制御 / 接続・ロジック・システム
- Cursor = 実装補助
- NORI-san = 最終判断

禁止:
- Claudeに採用判断を任せない
- Claudeコードをそのまま貼らない
- AI同士を直接対話させない
- NORI-sanを飛ばして不可逆判断しない
- AIらしい売り文句を採用しない

## PUBLIC_RELEASE_RULE
公開前は足さない。
迷わせるものは削る。
文言は短く、価値を先に出す。
AI感を出さない。
技術を見せない。

最終優先:
1. Maintenance が出ない
2. index.html がオンボーディングとして機能する
3. index.html のユーザー言語が全ページに引き継がれる
4. index.html の無料導線が index.test.html に向く
5. index.test.html で無料1日5回翻訳が動く
6. index.next.html でCore $2.99導線が見える
7. index.premium.html で Travel Pass $14.99 / 30日 / 自動更新なし が伝わる
8. index.14.99.html で Speak / Show / Essentials が迷わず使える
9. Stripe success URL が正しい

## FEATURE_REDUCTION_RULE
公開前は機能を増やさない。
初見5秒で理解できない機能は後回し。

残す:
- index.html: オンボーディング / ユーザー言語決定 / Core $2.99 / Travel $14.99
- index.test.html: 無料5回 / 翻訳入力 / 結果 / ユーザー言語 / 相手言語 / Core導線 / Travel導線
- index.next.html: 翻訳入力 / 結果 / ユーザー言語 / 相手言語 / 音声 / 購入導線
- index.14.99.html: Speak / Show / Essentials / Back

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
AIらしさを出さない。
最適化という言葉を出さない。
ユーザーには「自分の言葉で通じる」と感じさせる。

index.html で理解させる。
index.test.html で触らせる。
index.next.html で継続させる。
index.premium.html で Travel Pass の価値を伝える。index.14.99.html で Travel 本体を提供する。

もう作り足さない。
必要なページだけ作る。
磨く。削る。出す。

## UPDATE_RULE
このファイルは上書き更新のみ。
