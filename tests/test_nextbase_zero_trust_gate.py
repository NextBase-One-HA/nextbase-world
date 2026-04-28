from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding='utf-8')


def test_tomori_hard_gate_exists_and_blocks_unchecked_claims():
    text = read('TOMORI_HARD_GATE.md')
    required = [
        '確認前に喋るな',
        '証拠を見ろ',
        'ズレたら止まれ',
        '直してから説明しろ',
        '説明を先にしない',
        '未確認で「OK」と言わない',
    ]
    for item in required:
        assert item in text


def test_canonical_state_keeps_current_payment_flow_locked():
    text = read('CANONICAL_NEXTBASE_STATE.md')
    required = [
        'index.html → index.next.html → 2.99 modal → Stripe → index.2.99.html',
        '2.99は必ずmodal経由。直Stripeは禁止。',
        '14.99購入入口はindex.premium.htmlのみ。',
        '解約/管理は必ず説明モーダルを挟む。',
        '無料5回を超えたら、UIだけでなくAPI呼び出し前に止める。',
        '端末 = 表示',
        'Cloud = 正本',
    ]
    for item in required:
        assert item in text


def test_cancel_copy_is_child_simple_and_mentions_email_step():
    text = read('CANONICAL_NEXTBASE_STATE.md')
    required = [
        '解約しますか？',
        'メールアドレスを入れることがあります。',
        'メールに届いたボタンを押すと、解約ページに行けます。',
        '最後まで進めないと、解約は終わりません。',
        '解約しても、次の支払いの日までは使えます。',
    ]
    for item in required:
        assert item in text


def test_black_box_boundary_is_locked():
    text = read('CANONICAL_NEXTBASE_STATE.md')
    public_items = ['GLBの体験', '使い方', '安心説明', '価格', '解約の流れ']
    hidden_items = ['内部レイヤー名', '権利判定の細部', 'API構造', 'fallback条件', 'ブラックボックス化した判断ロジック']
    for item in public_items + hidden_items:
        assert item in text
