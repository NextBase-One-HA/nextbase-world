# NEXTBASE CANONICAL STATE (LATEST)

## ONE LINE
NextBaseは、言語で困る人を助けるためのGLBを出す。今は2.99導線を完成させ、次にSmile Friend Cloudで人と人をつなぐ。

---

## CURRENT GOAL
GLBを“迷わず使える導線”で公開し、2.99課金が成立する状態を作る。

現時点の最優先は、広げることではなく、1人目が迷わず課金・利用・解約確認まで通れること。

---

## CURRENT FLOW (LOCKED)
index.html → index.next.html → 2.99 modal → Stripe → index.2.99.html

Travel:
index.2.99.html → index.premium.html → 14.99 modal → Stripe → index.14.99.html

---

## HARD RULES
- 2.99は必ずmodal経由。直Stripeは禁止。
- 14.99購入入口はindex.premium.htmlのみ。
- premiumはGLB/Core購入者だけが入れる。
- index.14.99.htmlへ通常hrefで直接飛ばさない。
- travel.html参照禁止。
- 解約/管理は必ず説明モーダルを挟む。
- 無料5回を超えたら、UIだけでなくAPI呼び出し前に止める。

---

## UX RULES
ユーザーに難しい言葉を出さない。
子供でも分かる言葉にする。

基本:
- 1秒理解
- 迷いゼロ
- 恐怖ゼロ
- 終わりほど親切にする

課金前:
- 税金が加算される場合があることを短く説明する。
- Stripeへ行く前にワンクッション置く。

解約前:
- いきなりStripeへ飛ばさない。
- メール入力が必要な場合があることを先に伝える。
- メールに届いたボタンから解約ページへ進む場合があることを伝える。
- 最後まで進めないと解約が終わらないことを伝える。
- 解約しても通常は次の支払いの日までは使えることを伝える。

---

## CANCEL MODAL COPY (CANONICAL)
GLB

解約しますか？

このあと、別のページ（Stripe）に行きます。

・メールアドレスを入れることがあります。
・メールに届いたボタンを押すと、解約ページに行けます。
・解約ページで、キャンセルのボタンを押してください。
・最後まで進めないと、解約は終わりません。
・解約しても、次の支払いの日までは使えます。

[解約ページへ進む →]
[やめる（戻る）]

Stripeの画面は、人によって少し違うことがあります。

---

## SYSTEM STRUCTURE
Smile = 入口
Core = 翻訳処理
Friend = 相手・つながり・出口
Cloud = 権利・ID・安全管理

今後は:
端末 = 表示
Cloud = 正本

localStorageだけを正本にしない。
課金・解約・Friend・GLB IDはCloud側を正本にする。

---

## SMILE FRIEND CLOUD (NEXT CANONICAL DIRECTION)
目的:
GLBを、ただの翻訳ページではなく、人と人をつなぐ翻訳基盤にする。

今できる最小土台:
- GLB専用IDをクラウドで発行する。
- 電話番号は使わない。
- 電話帳は使わない。
- GLB ID同士で相手を指定する。
- 相手が承認した場合だけFriendになる。
- 選んだ相手とだけ翻訳チャットできる。
- ブロック/削除を用意する。
- Stripe customer_idとGLB IDを必要最小限で紐づける。
- 解約状態はCloud側で管理する。

最小データ:
users
- user_id
- glb_id
- stripe_customer_id
- status

friends
- from_glb_id
- to_glb_id
- status
- blocked

subscriptions
- user_id
- plan
- active
- current_period_end

---

## GLB CONNECT (FUTURE PRODUCT)
GLBアプリ内だけでつながる翻訳チャット。

ルール:
- 電話番号を使わない。
- 電話帳を使わない。
- GLB IDまたはQRで相手を追加する。
- 承認した相手とだけチャットできる。
- 知らない人から勝手に連絡できない。
- いつでも削除できる。
- いつでもブロックできる。

初回イメージ:
あなたのGLB IDを作ります。
このIDで、相手と翻訳チャットできます。
電話番号や電話帳は使いません。
[GLB IDを作る]

---

## BLACK BOX RULES
表に出す:
- GLBの体験
- 使い方
- 安心説明
- 価格
- 解約の流れ
- ユーザーにとっての価値

表に出さない:
- 内部レイヤー名
- 自己最適化の考え方
- 権利判定の細部
- API構造
- fallback条件
- ブラックボックス化した判断ロジック

顔と責任は出す。
中の守るべき構造は出さない。

---

## DO NOT DO NOW
- いきなり広告を大きく回さない。
- GLB Connectを今すぐ本体に混ぜない。
- ユーザー情報を取りすぎない。
- 電話番号/電話帳連携を入れない。
- 正本にない変更をしない。

---

## NOW DO
1. 2.99導線を実機で完成させる。
2. 無料5回制限をAPI前で止める。
3. 解約モーダルを子供でも分かる説明にする。
4. 1人に渡して、どこで止まったかを見る。
5. その後、Smile Friend Cloudの最小設計に進む。

---

## STATUS
PR #1 merged.
Payment flow mostly stable.
Free quota API hard stop and cancel care modal are in progress.
Smile Friend Cloud is canonical next direction, but not yet implementation priority until 2.99 flow passes real user validation.
