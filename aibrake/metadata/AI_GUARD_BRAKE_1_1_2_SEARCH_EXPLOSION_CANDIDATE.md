# AI GUARD & BRAKE 1.1.2 — SEARCH EXPLOSION METADATA CANDIDATE

STATUS: DRAFT FOR ASC 1.1.2 ONLY / DO NOT APPLY TO LIVE 1.1.1
UPDATED: 2026-10-16

## Product truth

- Product: AI GUARD & BRAKE
- V1 action: uses the existing BRAKE function to prevent selected supported apps from being opened on this iPhone.
- GUARD: use of the same BRAKE function for important apps such as banking, securities, payment, work, or smart-home control apps.
- BRAKE: use of the same app-access BRAKE for AI apps.
- UNLOCK: user action to make the selected app usable again.
- BRAKE is not described as a cloud-service stop, bank-system protection, appliance stop, other-device stop, cyberattack detector, or malware remover.
- Do not claim Data Not Collected for live 1.1.1. The live privacy state is separate from this 1.1.2 metadata candidate.

## Banned stale metadata for 1.1.2

Do not carry forward these live-1.1.1 concepts into 1.1.2 metadata:

- CLOUD BRAKE
- cloud emergency brake
- cloud execution stop
- managed execution
- DOUBLE BRAKE / two BRAKE
- kill switch / キルスイッチ
- runaway prevention / 暴走防止 as a guaranteed security effect
- execution stop / 実行停止 when it implies stopping a remote service or background execution
- claims that no personal information is externally sent in live 1.1.1

## Search explosion law

SEARCH EXPLOSION != KEYWORD SPAM

SEARCH EXPLOSION = ONE TRUE PRODUCT
  x MANY REAL USER INTENTS
  x MANY NATURAL LOCAL PHRASES
  x MANY CULTURAL CONTEXTS
  x MANY AI QUESTIONS

Do not repeat App Name / Subtitle words mechanically in Keywords unless product clarity or measured search value justifies it.

## High-intent discovery clusters

1. Important-app protection intent
   - lock important apps
   - keep banking app closed when not in use
   - protect finance apps on iPhone
   - restrict payment app access
   - keep work apps closed

2. AI-app control intent
   - lock AI apps
   - block AI app access
   - stop myself opening AI apps
   - AI app brake
   - human-controlled AI app access

3. Safety / anxiety intent
   - close important apps when iPhone security feels uncertain
   - keep sensitive apps unavailable until needed
   - prevent accidental opening of important apps
   - app access guard

4. Human-control intent
   - manual unlock app access
   - keep apps closed until I decide
   - human-controlled app access
   - deliberate unlock

5. Family Controls / Screen Time-adjacent intent
   - app blocker for important apps
   - app access restriction on iPhone
   - lock selected apps on iPhone

## Japanese candidate

### Name
AI GUARD & BRAKE: NextBase

### Subtitle candidates
Primary:
大事なアプリを閉じておく

Alternates for ASC field-fit testing:
重要アプリを使わない時にGUARD
AIアプリを必要な時だけUNLOCK
銀行・AIアプリを使わない時に閉じる

### Promotional text candidate
銀行・証券・決済・仕事・家電操作などの大事な対応アプリはGUARD。AIアプリはBRAKE。必要な時だけ自分でUNLOCK。

### Keyword intent pool
重要アプリ,銀行アプリ,証券アプリ,決済アプリ,AIアプリ,アプリロック,アプリ制限,アクセス制限,ガード,ブレーキ,アンロック,人間制御,使わない時,誤操作防止

Final ASC keyword allocation must remove unnecessary duplication with Name / Subtitle and obey the actual ASC field limit observed at write time.

### Description opening candidate
AI GUARD & BRAKEは、Family Controlsで選択できる対応アプリへのアクセスを、このiPhoneでBRAKEするアプリです。

大事なアプリはGUARD。AIアプリはBRAKE。
使わない時は閉じておき、必要な時だけ自分でUNLOCKします。

銀行、証券、決済、仕事、家電操作などの重要な対応アプリを、使わない間このiPhoneから開けない状態にしておけます。GUARDは別の停止機能ではなく、同じBRAKE機能を重要アプリ保護として使う考え方です。

AIアプリも、今は使わない時にBRAKEできます。

GUARD / BRAKEが対象にするのは、このiPhone上の対応アプリへの入口です。クラウドサービス、銀行や証券会社のシステム、家電本体、他の端末、送信済みの命令を停止する機能ではありません。サイバー攻撃そのものを検知・除去する機能でもありません。

## English candidate

### Name
AI GUARD & BRAKE: NextBase

### Subtitle candidates
Primary:
Keep important apps closed

Alternates:
Guard important apps until needed
Brake AI apps until you unlock
Close banking and AI apps when idle

### Promotional text candidate
GUARD important apps such as banking, finance, payment, work, or smart-home control apps. BRAKE AI apps. UNLOCK only when you choose to use them.

### Keyword intent pool
banking app lock,finance app guard,payment app lock,AI app blocker,app access guard,app restriction,manual unlock,important app lock,human control,iPhone app blocker

Final ASC keyword allocation must remove unnecessary duplication with Name / Subtitle and obey the actual ASC field limit observed at write time.

### Description opening candidate
AI GUARD & BRAKE uses the BRAKE function to prevent selected supported apps from being opened on this iPhone.

GUARD important apps. BRAKE AI apps. Keep them closed when you are not using them, then UNLOCK when you decide to use them.

For apps selectable through Family Controls, you can use GUARD for banking, finance, payment, work, or smart-home control apps. GUARD is not a separate stop mechanism; it is how the same BRAKE function is used for important apps.

BRAKE can also be used for supported AI apps that you do not want opened right now.

GUARD / BRAKE applies to the app-access entry point on this iPhone. It does not stop a bank, cloud service, AI model, appliance, another device, or a command that has already been sent. It is not a cyberattack detection or removal tool.

## 50-locale allocation rule

Do not copy English keywords into every locale.

For each actual ASC locale present on the 1.1.2 version record:

- preserve the exact product boundary above
- use natural local phrases for banking / finance / payment / AI app / app lock / app restriction / manual unlock intents
- prioritize native high-intent phrases over literal translation
- avoid words that imply remote-service shutdown, guaranteed attack prevention, malware removal, or appliance shutdown
- avoid false privacy claims
- allocate distinct search surface across Name / Subtitle / Keywords instead of mechanical duplication
- keep Brand terms only where needed for identity

The actual ASC locale list is authoritative. Do not assume a fixed locale set from the runtime app.

## AI crawler / answer-engine query set

Japanese examples:

- 銀行アプリを使わない時だけ開けなくするiPhoneアプリ
- 証券アプリを必要な時だけ開く方法
- 決済アプリを普段は閉じておくアプリ
- AIアプリを使わない時にロックしたい
- iPhoneで大事なアプリをまとめて守る方法
- Family Controlsで重要アプリを制限するアプリ
- AIアプリを自分でUNLOCKするまで開けないようにしたい
- 家電操作アプリを使わない時に閉じておきたい
- サイバー攻撃検知ではなく重要アプリの入口を閉じるアプリ
- 人間が重要アプリの入口を握るiPhoneアプリ

English examples:

- app to keep banking apps closed until I need them
- iPhone app that blocks selected important apps
- app to lock finance apps when not in use
- AI app blocker with manual unlock
- human controlled access to AI apps on iPhone
- app guard for banking payment and work apps
- keep smart home control apps closed when not using them
- app access guard that does not claim to stop cloud services
- app to prevent opening selected apps until I unlock them
- Family Controls app for important app access

## Mutation boundary

- LIVE 1.1.1 metadata: do not overwrite with this packet while 1.1.1 remains the only editable live version.
- Create / expose editable App Store version 1.1.2 first.
- Then fresh-read its actual 50 ASC locales.
- Run field-length / byte checks per actual locale.
- Apply this product truth and localized search-intent allocation only to 1.1.2.
- Privacy Publish and Submit remain separate NORI gates.
