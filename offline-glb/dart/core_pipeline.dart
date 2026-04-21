// core_pipeline.dart
import 'dart:collection';

import 'tokenizer_interface.dart';
import 'sqlite_dictionary.dart';
import 'phrase_matcher.dart';
import 'template_engine.dart';

/// Tomori Public v0.2 - Offline Translation Core Pipeline
///
/// Pipeline (fixed):
/// 1) Normalize
/// 2) Cache (LRU+TTL)
/// 3) Template apply (deterministic)
/// 4) Phrase longest match (Trie)
/// 5) Token translate
/// 6) Post rewrite
class OfflineTranslatePipeline {
  OfflineTranslatePipeline({
    required this.dictionary,
    required this.tokenizer,
    required this.templateEngine,
    required this.phraseMatcher,
    CacheConfig? cache,
  }) : _cache = _LruTtlCache(cache ?? const CacheConfig());

  final OfflineDictionary dictionary;
  final Tokenizer tokenizer;
  final TemplateEngine templateEngine;
  final PhraseMatcher phraseMatcher;
  final _LruTtlCache _cache;

  /// Main entry (single function entrance).
  /// Returns translated text.
  Future<String> translate({
    required String text,
    required String from,
    required String to,
  }) async {
    final normalized = _normalize(text);
    if (normalized.isEmpty) return "";
    if (from == to) return normalized;

    final cacheKey = _makeKey(normalized, from, to);
    final cached = _cache.get(cacheKey);
    if (cached != null) return cached;

    // 0) Load data for this lang pair (lazy).
    await dictionary.ensureReady(from: from, to: to);

    // 1) Templates first (highest precision)
    final templ = await templateEngine.tryApply(
      input: normalized,
      from: from,
      to: to,
      dict: dictionary,
    );
    if (templ != null) {
      final out = _postRewrite(templ);
      _cache.put(cacheKey, out);
      return out;
    }

    // 2) Phrase longest match using trie.
    final phrase = await phraseMatcher.translateByLongestMatch(
      input: normalized,
      from: from,
      to: to,
      dict: dictionary,
    );

    // 3) Token-level translate for remaining parts.
    final tokenOut = await _tokenTranslate(
      input: phrase,
      from: from,
      to: to,
    );

    final finalOut = _postRewrite(tokenOut);

    _cache.put(cacheKey, finalOut);
    return finalOut;
  }

  // -----------------------
  // Internals
  // -----------------------

  String _normalize(String s) {
    // Minimal normalize (safe). Extend later.
    var t = s.trim();
    // collapse spaces
    t = t.replaceAll(RegExp(r'\s+'), ' ');
    // unify some punctuation spacing
    t = t.replaceAll('，', ',').replaceAll('．', '.');
    return t;
  }

  String _postRewrite(String s) {
    // Minimal post rewrite. Extend later (politeness, punctuation, etc.)
    var t = s.trim();
    t = t.replaceAll(RegExp(r'\s+([,!.?])'), r'$1');
    return t;
  }

  String _makeKey(String text, String from, String to) => '$from>$to::$text';

  Future<String> _tokenTranslate({
    required String input,
    required String from,
    required String to,
  }) async {
    final tokens = tokenizer.tokenize(input, lang: from);

    final out = <String>[];
    for (final tok in tokens) {
      if (tok.type == TokenType.whitespace) {
        out.add(tok.text);
        continue;
      }
      if (_isProtected(tok.text)) {
        out.add(tok.text);
        continue;
      }
      final hit = await dictionary.lookupWord(
        src: tok.text,
        from: from,
        to: to,
      );
      out.add(hit ?? tok.text);
    }
    return out.join();
  }

  bool _isProtected(String t) {
    // Protect numbers, units, model codes, symbols-ish tokens.
    if (RegExp(r'^\d+([.,]\d+)?$').hasMatch(t)) return true;
    if (RegExp(r'^[A-Za-z0-9_-]{3,}$').hasMatch(t)) return true; // codes
    if (RegExp(r'^[\p{P}\p{S}]+$', unicode: true).hasMatch(t)) return true;
    return false;
  }
}

class CacheConfig {
  const CacheConfig({
    this.maxEntries = 500,
    this.ttl = const Duration(minutes: 10),
  });

  final int maxEntries;
  final Duration ttl;
}

/// Simple LRU+TTL cache (in-memory).
class _LruTtlCache {
  _LruTtlCache(this.config);

  final CacheConfig config;
  final LinkedHashMap<String, _CacheEntry> _map = LinkedHashMap();

  String? get(String key) {
    final e = _map.remove(key);
    if (e == null) return null;

    if (DateTime.now().isAfter(e.expiresAt)) {
      return null;
    }
    // re-insert to mark as most-recent
    _map[key] = e;
    return e.value;
  }

  void put(String key, String value) {
    _map.remove(key);
    _map[key] = _CacheEntry(
      value: value,
      expiresAt: DateTime.now().add(config.ttl),
    );

    while (_map.length > config.maxEntries) {
      _map.remove(_map.keys.first);
    }
  }
}

class _CacheEntry {
  _CacheEntry({required this.value, required this.expiresAt});
  final String value;
  final DateTime expiresAt;
}