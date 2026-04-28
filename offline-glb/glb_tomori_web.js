/**
 * Tomori / オフラインGLB — Web 側の薄い互換層
 * Desktop: ロジック/index.UI系/core_pipeline.dart の _normalize / _postRewrite と同順・同趣旨
 * （完全同一ではないが、キャッシュキーとローカル辞書ヒット率を揃える）
 */
(function (g) {
    function glbTomoriNormalize(s) {
        if (s == null || s === '') return '';
        var t = String(s).trim().replace(/\s+/g, ' ');
        return t.replace(/，/g, ',').replace(/．/g, '.');
    }
    function glbTomoriPostRewrite(s) {
        if (s == null || s === '') return '';
        var t = String(s).trim().replace(/\s+/g, ' ');
        return t.replace(/\s+([,!.?])/g, '$1');
    }
    g.glbTomoriNormalize = glbTomoriNormalize;
    g.glbTomoriPostRewrite = glbTomoriPostRewrite;

    /**
     * FREE HOOK API HARD STOP
     * index.next.html は無料5回導線。UIの残回数表示が0でもAPIが呼ばれる事故を止める。
     * Paid pages（index.2.99.html / Travel）には影響させない。
     */
    (function installFreeQuotaApiGuard() {
        if (!g || !g.location || !/index\.next\.html(?:$|[?#])/.test(g.location.pathname + g.location.search)) return;
        if (g.__glbFreeQuotaApiGuardInstalled) return;
        g.__glbFreeQuotaApiGuardInstalled = true;

        function quotaIsZeroFromDom() {
            try {
                var txt = (document.body && document.body.innerText) ? document.body.innerText : '';
                return /本日\s*残り\s*0/.test(txt) || /0\s*free/i.test(txt) || /remaining\s*0/i.test(txt);
            } catch (e) {
                return false;
            }
        }

        function blockIfQuotaZero() {
            if (!quotaIsZeroFromDom()) return false;
            try {
                var input = document.getElementById('tr-text') || document.querySelector('input, textarea');
                var run = document.getElementById('tr-run');
                var result = document.getElementById('glb-result-text');
                if (input) input.disabled = true;
                if (run) {
                    run.disabled = true;
                    run.setAttribute('aria-disabled', 'true');
                    run.style.opacity = '0.55';
                    run.style.pointerEvents = 'none';
                }
                if (result && !/5回|limit|購読|subscribe/i.test(result.textContent || '')) {
                    result.textContent = '本日の無料回数に達しました。GLB $2.99で無制限に使えます。';
                }
            } catch (e) {}
            return true;
        }

        var originalFetch = g.fetch;
        if (typeof originalFetch === 'function') {
            g.fetch = function glbGuardedFetch(input, init) {
                var url = '';
                try { url = typeof input === 'string' ? input : (input && input.url) || ''; } catch (e) {}
                if (/\/translate(?:$|[?#])/.test(url) && blockIfQuotaZero()) {
                    return Promise.reject(new Error('GLB_FREE_QUOTA_EXHAUSTED'));
                }
                return originalFetch.apply(this, arguments);
            };
        }

        if (typeof document !== 'undefined') {
            document.addEventListener('click', function () { setTimeout(blockIfQuotaZero, 0); }, true);
            document.addEventListener('DOMContentLoaded', function () {
                blockIfQuotaZero();
                try { new MutationObserver(blockIfQuotaZero).observe(document.body, { childList: true, subtree: true, characterData: true }); } catch (e) {}
            });
        }
    })();

    /**
     * CANCEL CARE MODAL
     * 解約/管理リンクは、Stripeへ飛ばす前に必ずワンクッション説明する。
     * 「終わりほど親切に」: 利用期限・追加料金・Stripe上の操作手順を先に見せる。
     */
    (function installCancelCareModal() {
        if (!g || typeof document === 'undefined') return;
        if (g.__glbCancelCareInstalled) return;
        g.__glbCancelCareInstalled = true;

        var fallbackPortal = 'https://billing.stripe.com/p/login/fZuaEZ0oRgd25Vl96fasg00';
        var pendingProceed = null;

        function ensureModal() {
            var existing = document.getElementById('glb-cancel-care-modal');
            if (existing) return existing;

            var style = document.createElement('style');
            style.textContent = '' +
                '#glb-cancel-care-modal{position:fixed;inset:0;z-index:100001;background:rgba(4,4,10,.92);backdrop-filter:blur(16px);display:flex;align-items:center;justify-content:center;padding:24px;opacity:0;pointer-events:none;transition:opacity .22s ease;box-sizing:border-box;}' +
                '#glb-cancel-care-modal.open{opacity:1;pointer-events:all;}' +
                '#glb-cancel-care-card{width:100%;max-width:380px;background:#0f0f1a;border:1px solid rgba(240,201,58,.32);border-radius:18px;padding:26px 22px;text-align:center;color:#f7f1d2;box-sizing:border-box;box-shadow:0 0 40px rgba(240,201,58,.08);}' +
                '#glb-cancel-care-card h2{margin:0 0 6px;font-family:serif;font-size:30px;color:#ffe566;font-weight:400;}' +
                '#glb-cancel-care-card h3{margin:0 0 14px;font-size:15px;color:#fff;font-weight:700;}' +
                '#glb-cancel-care-card p{margin:0 0 14px;font-size:12px;color:#9a98aa;line-height:1.65;}' +
                '#glb-cancel-care-card ul{margin:0 0 18px;padding:0;text-align:left;list-style:none;font-size:12px;color:#d8d2b5;line-height:1.75;}' +
                '#glb-cancel-care-card li{margin:0 0 6px;padding-left:1.2em;position:relative;}' +
                '#glb-cancel-care-card li:before{content:"・";position:absolute;left:0;color:#ffe566;}' +
                '#glb-cancel-care-proceed{display:block;width:100%;box-sizing:border-box;padding:15px;border-radius:999px;border:none;background:linear-gradient(180deg,#fff5a0 0%,#ffe566 50%,#c9960a 100%);color:#07060a;font-size:14px;font-weight:800;text-decoration:none;cursor:pointer;box-shadow:0 0 24px rgba(240,201,58,.28);}' +
                '#glb-cancel-care-close{margin-top:10px;width:100%;padding:12px;border-radius:999px;border:1px solid rgba(255,255,255,.08);background:none;color:#8f8da2;font-size:13px;cursor:pointer;}' +
                '#glb-cancel-care-small{font-size:10px!important;color:#6f6d7f!important;margin-top:12px!important;}';
            document.head.appendChild(style);

            var modal = document.createElement('div');
            modal.id = 'glb-cancel-care-modal';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            modal.innerHTML = '' +
                '<div id="glb-cancel-care-card">' +
                '<h2>GLB</h2>' +
                '<h3>プランの管理・解約へ進みますか？</h3>' +
                '<p>次はStripeの安全な管理ページに移動します。移動前に、解約の流れだけ確認してください。</p>' +
                '<ul>' +
                '<li>解約しても、通常は次の請求日までは利用できます。</li>' +
                '<li>次の請求日前に解約すれば、追加料金は発生しません。</li>' +
                '<li>Stripe画面で「プランをキャンセル」または「サブスクリプションをキャンセル」を選び、最後の確認まで進めてください。</li>' +
                '<li>最後の確認を完了しない限り、解約は確定しません。</li>' +
                '</ul>' +
                '<button id="glb-cancel-care-proceed" type="button">Stripeで管理・解約へ進む →</button>' +
                '<button id="glb-cancel-care-close" type="button">戻る</button>' +
                '<p id="glb-cancel-care-small">表示やボタン名はStripe側の状態・言語設定により少し変わる場合があります。</p>' +
                '</div>';
            document.body.appendChild(modal);

            modal.addEventListener('click', function (ev) {
                if (ev.target === modal) closeModal();
            });
            document.getElementById('glb-cancel-care-close').addEventListener('click', closeModal);
            document.getElementById('glb-cancel-care-proceed').addEventListener('click', function () {
                var fn = pendingProceed;
                pendingProceed = null;
                closeModal();
                if (typeof fn === 'function') {
                    fn();
                } else {
                    g.location.href = fallbackPortal;
                }
            });
            return modal;
        }

        function openModal(proceed) {
            pendingProceed = proceed;
            ensureModal().classList.add('open');
        }

        function closeModal() {
            var modal = document.getElementById('glb-cancel-care-modal');
            if (modal) modal.classList.remove('open');
        }

        function looksLikeCancelManage(el) {
            if (!el) return false;
            var href = '';
            try { href = el.getAttribute && (el.getAttribute('href') || ''); } catch (e) {}
            var txt = '';
            try { txt = (el.innerText || el.textContent || '').trim(); } catch (e) {}
            return /billing\.stripe\.com/i.test(href) || /解約|キャンセル|cancel|manage|subscription|plan/i.test(txt);
        }

        document.addEventListener('click', function (ev) {
            var target = ev.target && ev.target.closest ? ev.target.closest('a,button') : null;
            if (!looksLikeCancelManage(target)) return;

            var href = target.getAttribute && target.getAttribute('href');
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof ev.stopImmediatePropagation === 'function') ev.stopImmediatePropagation();

            openModal(function () {
                if (href && href !== '#' && href !== 'javascript:void(0)') {
                    g.location.href = href;
                    return;
                }
                if (typeof g.openManagePortal === 'function') {
                    g.openManagePortal();
                    return;
                }
                g.location.href = fallbackPortal;
            });
        }, true);

        g.openCancelCareModal = openModal;
    })();
})(typeof window !== 'undefined' ? window : globalThis);
