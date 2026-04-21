// template_engine.dart
import 'sqlite_dictionary.dart';

/// Very small template engine:
/// - Pattern format: tokens separated by spaces
/// - Slots: {A}, {B} ...
/// - Example pattern: "{A} は どこ です か"
/// - Rewrite: "Where is {A}?"
///
/// Note: For MVP, tokenizer is "space-based" for template matching.
/// If your language doesn't use spaces, you can:
/// - run a pre-tokenizer for templates
/// - or store templates in a normalized "space tokenized" form.
class TemplateEngine {
  const TemplateEngine();

  Future<String?> tryApply({
    required String input,
    required String from,
    required String to,
    required OfflineDictionary dict,
  }) async {
    final rules = await dict.listTemplates(from: from, to: to);
    if (rules.isEmpty) return null;

    final inTokens = _spaceTokens(input);
    if (inTokens.isEmpty) return null;

    for (final r in rules) {
      final pat = _spaceTokens(r.pattern);
      final match = _match(pat, inTokens);
      if (match == null) continue;

      // Apply rewrite
      var out = r.rewrite;
      for (final e in match.entries) {
        out = out.replaceAll('{${e.key}}', e.value);
      }
      return out;
    }
    return null;
  }

  List<String> _spaceTokens(String s) {
    final t = s.trim();
    if (t.isEmpty) return const [];
    return t.split(RegExp(r'\s+'));
  }

  /// Returns slot map when matched: { "A": "xxx", "B": "yyy" }
  Map<String, String>? _match(List<String> pattern, List<String> input) {
    // Simple greedy slot: slot consumes exactly 1 token (MVP).
    // Extend later to allow multi-token slots.
    if (pattern.length != input.length) return null;

    final slots = <String, String>{};
    for (var i = 0; i < pattern.length; i++) {
      final p = pattern[i];
      final tok = input[i];

      final slotName = _slotName(p);
      if (slotName != null) {
        // store slot
        slots[slotName] = tok;
        continue;
      }
      if (p != tok) return null;
    }
    return slots;
  }

  String? _slotName(String token) {
    final m = RegExp(r'^\{([A-Za-z0-9_]+)\}$').firstMatch(token);
    return m?.group(1);
  }
}