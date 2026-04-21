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
})(typeof window !== 'undefined' ? window : globalThis);
