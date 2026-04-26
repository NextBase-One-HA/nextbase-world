# GLB_DYNAMIC_CANON

## STATE
GLB_REVENUE_FIRST / FINAL_PRODUCT_WIRING

## GOAL
GLBを収益化する。
入口、Core、Travel、Stripe、翻訳導線、オンデバイス辞書、API削減ロジックを一体の商品導線として仕上げる。

## CURRENT_PRIORITY
1. index.htmlをGLB共通入口として安全版リビルドする
2. index.premium.htmlをTravel Pass $14.99説明・購入ページとして安全版リビルドする
3. index.next.htmlは既存Coreロジックを壊さず部分改善する
4. travel.htmlは購入後の本体UIとして既存ロジックを守ってUI改善する
5. Stripe導線を確認する
6. 実機で翻訳、無料枠、Core、Travelの流れを確認する

## URLS
- Entry:
https://nextbase-one-ha.github.io/nextbase-world/index.html

- Core $2.99:
https://nextbase-one-ha.github.io/nextbase-world/index.next.html

- Travel Pass $14.99 LP:
https://nextbase-one-ha.github.io/nextbase-world/index.premium.html

- Travel Pass App:
https://nextbase-one-ha.github.io/nextbase-world/travel.html

## PRODUCT_STRUCTURE
- index.html = 共通入口 / 無料体験 / オンボーディング / 0円入口
- index.next.html = Core $2.99 / 基本翻訳 / 継続利用
- index.premium.html = Travel Pass $14.99 / 説明・購入
- travel.html = Travel Pass購入後の本体UI

## PRICING
- Free = 0円 / 1日10回の試用 / 入口体験
- Core = $2.99 / 月額 / 基本翻訳の継続利用
- Travel Pass = $14.99 / 30日買い切り / 自動更新なし
- 旅行が終わればCoreへ戻る思想
- また旅行が決まればTravel Passを買う

## PRODUCT_FLOW
1. index.htmlで「誰のため」「何ができる」「今すぐ試せる」を伝える
2. 0円無料枠で翻訳体験を出す
3. Core $2.99へ誘導する
4. 旅行時はTravel Pass $14.99へ誘導する
5. Stripe成功後にtravel.htmlへ戻す
6. Travel Pass 30日後はCore思想へ戻す

## TRANSLATION_FLOW
入力は常にユーザー中心。

基本流れ:
1. User input = 音声またはテキスト
2. Source language = ユーザー言語
3. Target language = 相手の言語
4. First check = オンデバイス辞書 / 150系辞書 / 定型文
5. If hit = APIを使わず即表示
6. If miss = API翻訳
7. Result = Friend表示として整える
8. travel.htmlでは見せる、話す、必須カードへ出力

## SMILE_CORE_FRIEND
- Smile = 入口 / index.html / 最初の理解 / 無料体験
- Core = 内部処理 / 課金状態 / 翻訳ロジック / 辞書 / API制御
- Friend = 出口 / ユーザーに見せる翻訳結果 / UI / 使える言葉

ユーザーに見せるのはFriendとして整えた結果のみ。
APIや内部処理を表に出さない。

## SMILE_FRIEND_ENGINE
Smile Friend Engineは翻訳API、system-status、entitlements等のサーバー側中継。
ただしGLBの出口ではない。
出口は常に各HTMLのUI。

役割:
- /translate = API翻訳
- /system-status = maintenance_mode確認
- /entitlements = Stripe後の利用権確認

## BLACK_BOX_RULE
ブラックボックスは内部道具。
ユーザーに見せない。

含むもの:
- APIキー
- 翻訳API呼び出し
- 課金状態確認
- entitlement確認
- メンテナンス状態
- 辞書ヒット判定
- API削減判定

外に出すもの:
- 翻訳結果
- 残り無料回数
- Core / Travel の分かりやすい説明
- 購入後に使える画面

## ON_DEVICE_RULE
オンデバイス優先。
通信が不要なものは先に端末内で処理する。

対象:
- 150系辞書
- よく使う旅行フレーズ
- Emergency / Restaurant / Taxi / Hotel / Airport / Shopping 等の定型文
- 既に翻訳済みの履歴
- 同一セッション内キャッシュ

目的:
- 表示速度を上げる
- APIコストを下げる
- 通信失敗時でも最低限使える状態を作る

## DICTIONARY_150_RULE
150系辞書ロジックはAPI削減の第一層。

流れ:
1. 入力を正規化する
2. カテゴリ辞書を見る
3. 完全一致または近似一致を見る
4. 対応訳があればAPIを使わず表示
5. ヒットしなければAPIへ進む

カテゴリ例:
- Restaurant
- Taxi
- Hotel
- Airport
- Shopping
- Medical / Emergency
- Basic greeting
- Travel essentials

## ZERO_YEN_LOGIC
0円ロジックは入口体験のための無料枠。

目的:
- ユーザーが買う前に価値を体験する
- いきなり課金させない
- 1日10回で十分に試せる

ルール:
- localStorageで日付と回数を管理
- Free = 1日10回
- Core購入後は制限解除
- Travel Pass中はTravel UIを優先
- 無料枠が尽きたらCore $2.99へ自然誘導

## API_REDUCTION_LOGIC
API削減は収益性のために必須。

優先順:
1. 150系辞書
2. 定型文
3. 履歴キャッシュ
4. セッションキャッシュ
5. 同一入力キャッシュ
6. API翻訳

APIを呼ぶ条件:
- 辞書にない
- 定型文にない
- キャッシュにない
- ユーザーが新規翻訳を要求した

APIを呼ばない条件:
- Essentialsの定型文
- 同じ入力・同じ言語ペア
- 既存履歴から再利用できる
- Emergency等の固定文

## SELF_OPTIMIZATION_LAYER
自己最適化レイヤーはAIを進化させるものではない。
人間の判断を守るための運用レイヤー。

- ORE = 人間最終判断保護
- TOMORI = 構造整理 / 役割分配 / 最短ルート整理
- STELLA = 最新同期 / 正本照合 / ズレ検出
- NOIR = 証拠監査 / ログ監査 / 異常停止
- KURO = 文書 / 仕様 / 比較 / 実務文生成
- Cursor = 実装 / 修正 / 技術作業

AI間の直接対話は禁止。
必ずNORI-sanを唯一のハブにする。

## CURRENT_UI_RULE
- 黒背景
- 白太文字
- 細いゴールド枠
- 大きいボタン
- 説明は最小
- 初期画面は迷わせない
- Claude案はデザイン原案として使う
- Claudeコードはそのまま貼らず安全整形する

## INDEX_HTML_RULE
index.html はGLB共通入口。

必要要素:
- GLBが何かを一言で伝える
- 無料10回体験
- Core $2.99導線
- Travel Pass $14.99導線
- 多言語オンボーディング

禁止:
- Maintenance初期表示
- 壊れたCSS記号
- Markdown記号混入
- 過剰な思想表現

## INDEX_NEXT_RULE
index.next.html はCore $2.99本体。
既存の翻訳・課金・entitlementロジックを壊さない。
丸ごと置換しない。
UI改善は部分適用。

Coreに必要:
- 翻訳入力
- 翻訳結果
- 言語選択
- 音声/TTS
- 履歴/キャッシュ
- Core購入導線
- Travel Pass導線

## INDEX_PREMIUM_RULE
index.premium.html はTravel Pass説明・購入ページ。

必要要素:
- $14.99 / 30日買い切り
- 自動更新なし
- 旅行時だけ買う
- Coreとの違い
- Stripe購入ボタン
- Purchase Help

禁止:
- subscriptionと誤解させる表現
- Cancel Subscription中心の表示
- Maintenance初期表示
- 過剰な緊急訴求

## TRAVEL_HTML_RULE
travel.html は説明ページではない。
購入後に使う本体UI。

初期表示:
- 話す / Speak
- 見せる / Show
- 必須カード / Essentials

必要:
- 大きなボタン
- 相手に見せやすい翻訳結果
- TTS
- Flip / Zoom
- Essentials / 6カテゴリ
- 150系辞書 / 定型文優先
- API削減
- 30日Travel Pass状態

禁止:
- 小さいボタンだらけ
- 旧UIの初期表示
- Maintenance表示
- Survival / 生存 / 命を守る / 守護 / 聖域 / お守り
- nori=admin等の本番バイパス

## MAINTENANCE_RULE
全ページで maintenance overlay は初期非表示。

対象:
- index.html
- index.next.html
- index.premium.html
- travel.html

必須:
- style="display:none;"
- aria-hidden="true"
- hidden
- maintenance_mode=falseなら表示しない

## WORK_ENVIRONMENT
- Mac = GLB本線
- Windows = 後回し検証用
- Claude = 外部レビュー補助 / UI原案 / 文案
- Cursor = 実装
- ChatGPT = 正本整理・監査・GitHub直接更新
- NORI-san = 最終判断

## FORBIDDEN
- 古い前提で進めない
- 未確認の完了宣言をしない
- 正本にない作業を始めない
- Mythosを今GLBへ混ぜない
- Windows成果物をMac本線へ混ぜない
- Stripeを勝手に変更しない
- GitHub反映済みと未確認で断定しない
- Claudeコードをそのまま貼らない
- 3ページ以上を一括で丸ごと置換しない

## STATE_CHECK_TEMPLATE
STATE:
GOAL:
BLOCKER:
NEXT_ACTION:
EVIDENCE:
IRREVERSIBLE:
OUTPUT:

## UPDATE_RULE
このファイルは追記ではなく上書き。
古いSTATEは残さない。
現在の正本だけを書く。
