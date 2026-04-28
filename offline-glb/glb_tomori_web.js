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
})(typeof window !== 'undefined' ? window : globalThis);
