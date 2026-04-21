オフラインGLB（Tomori Public v0.2）— glb-noir への取り込み
================================================

元フォルダ: Mac Desktop/オフラインGLB
  - ロジック/index.UI系/*.dart … オフライン翻訳パイプライン（Flutter/Dart）
  - 指示.txt … 公開向け仕様（レイヤー・パイプライン順）
  - 備考.txt … 最小コード例・Sqflite 差し替えメモ
  - ロジックオフライン1.txt / 2.txt … ロジック　　　コード系 から複製

このディレクトリ
--------------
dart/          … 上記 7 ファイルのコピー（バージョン管理・参照用）
指示.txt / 備考.txt / ロジックオフライン*.txt … 仕様メモ
glb_tomori_web.js … ブラウザ用。core_pipeline の normalize/post と揃えた薄い層

Web（index.next / index.coreflow）では API の前に glbTomoriNormalize を通し、
応答表示前に glbTomoriPostRewrite を通す。

ロジックコード内外装 2.zip
--------------------------
ネストした zip の集合体で、index.UI系 と重複が多い。実体は ロジック/index.UI系 を正とした。

memos_ondevice/ … Desktop/オフラインGLB/オンデバイスロジック系 の .txt 一式（レイヤー・辞書・NE・ゲートウェイ等のメモ）。PDF は未同梱。
memos_translation_app/ … Desktop/オフラインGLB/翻訳アプリ　コード系 のルート直下 .txt 一式（番号メモ・SwiftUI 断片など）。アーカイブフォルダ内は未コピー（重複多いため）。

※ 実行可能コード（.dart/.js）はこの2フォルダには無く、断片は .txt 内に混在。Dart 核は引き続き dart/ を参照。
