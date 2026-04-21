// sqlite_dictionary.dart — Tomori Public v0.2 辞書インターフェース（正本）
// SqfliteDictionary / InMemoryDictionary が実装する。

/// 定型テンプレ一行（SQLite `templates` 行と対応）。
class TemplateRule {
  const TemplateRule({
    required this.pattern,
    required this.rewrite,
    this.priority = 0,
  });

  final String pattern;
  final String rewrite;
  final int priority;
}

/// オフライン辞書の抽象。`core_pipeline` / `phrase_matcher` / `template_engine` が依存。
abstract class OfflineDictionary {
  Future<void> ensureReady({required String from, required String to});

  Future<String?> lookupPhrase({
    required String src,
    required String from,
    required String to,
  });

  Future<String?> lookupWord({
    required String src,
    required String from,
    required String to,
  });

  Future<List<TemplateRule>> listTemplates({
    required String from,
    required String to,
  });
}

/// テスト・MVP 用のインメモリ実装（備考.txt の最小例と整合）。
class InMemoryDictionary implements OfflineDictionary {
  InMemoryDictionary();

  final Map<String, String> _word = {};
  final Map<String, String> _phrase = {};
  final List<_MemTemplate> _templates = [];

  final Set<String> _ready = {};

  static String _wk(String from, String to, String src, String kind) =>
      '$from|$to|$kind|$src';

  void putWord(String from, String to, String src, String dst) {
    _word[_wk(from, to, src, 'word')] = dst;
  }

  void putPhrase(String from, String to, String src, String dst) {
    _phrase[_wk(from, to, src, 'phrase')] = dst;
  }

  void addTemplate(TemplateRule rule, {required String from, required String to}) {
    _templates.add(_MemTemplate(from: from, to: to, rule: rule));
  }

  @override
  Future<void> ensureReady({required String from, required String to}) async {
    _ready.add('$from>$to');
  }

  @override
  Future<String?> lookupPhrase({
    required String src,
    required String from,
    required String to,
  }) async {
    return _phrase[_wk(from, to, src, 'phrase')];
  }

  @override
  Future<String?> lookupWord({
    required String src,
    required String from,
    required String to,
  }) async {
    return _word[_wk(from, to, src, 'word')];
  }

  @override
  Future<List<TemplateRule>> listTemplates({
    required String from,
    required String to,
  }) async {
    return _templates
        .where((t) => t.from == from && t.to == to)
        .map((t) => t.rule)
        .toList(growable: false);
  }
}

class _MemTemplate {
  _MemTemplate({
    required this.from,
    required this.to,
    required this.rule,
  });

  final String from;
  final String to;
  final TemplateRule rule;
}
