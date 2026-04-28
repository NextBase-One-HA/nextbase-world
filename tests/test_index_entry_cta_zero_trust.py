from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding='utf-8')


def test_bottom_cta_must_not_show_free_when_linking_to_body_or_hook_mismatch():
    html = read('index.html')
    forbidden = [
        'id="fc-btn">Try GLB Free',
        'id="fc-btn">Try Free',
        'id="fc-btn">無料で試す',
    ]
    for bad in forbidden:
        assert bad not in html, f'bottom CTA wording is misleading: {bad}'


def test_bottom_cta_must_be_open_glb():
    html = read('index.html')
    assert 'id="fc-btn">Open GLB' in html or 'id="fc-btn">GLBを開く' in html


def test_bottom_cta_must_go_to_paid_body():
    html = read('index.html')
    marker = 'id="fc-btn"'
    assert marker in html
    before = html[max(0, html.find(marker) - 220): html.find(marker) + 220]
    assert 'index.2.99.html' in before
    assert 'index.next.html#glb-core-subscribe-block' not in before


def test_hero_free_trial_can_still_go_to_free_hook():
    html = read('index.html')
    marker = 'id="h-cta1"'
    assert marker in html
    before = html[max(0, html.find(marker) - 220): html.find(marker) + 220]
    assert 'index.next.html#glb-core-subscribe-block' in before
