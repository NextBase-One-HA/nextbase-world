// phrase_matcher.dart
import 'sqlite_dictionary.dart';

/// Phrase matcher that applies longest match using a Trie.
/// Build/rebuild the Trie per language pair via ensureBuilt().
class PhraseMatcher {
  PhraseMatcher();

  _Trie? _trie;
  String? _builtKey;

  Future<void> ensureBuilt({
    required String from,
    required String to,
    required OfflineDictionary dict,
    required Iterable<String> phraseKeys,
  }) async {
    final key = '$from>$to';
    if (_trie != null && _builtKey == key) return;

    final trie = _Trie();
    for (final p in phraseKeys) {
      final translated = await dict.lookupPhrase(src: p, from: from, to: to);
      if (translated == null) continue;
      trie.insert(p, translated);
    }
    _trie = trie;
    _builtKey = key;
  }

  /// Minimal MVP: We don't have a phrase list in dict interface.
  /// So we support two modes:
  /// - If you have phraseKeys externally, call ensureBuilt(...) and then translate.
  /// - If not, this function will just do "exact phrase" lookup and return input.
  ///
  /// In production, you will preload all phrase keys from SQLite and build Trie.
  Future<String> translateByLongestMatch({
    required String input,
    required String from,
    required String to,
    required OfflineDictionary dict,
  }) async {
    // If trie is not built, fall back to exact phrase only.
    if (_trie == null) {
      final exact = await dict.lookupPhrase(src: input, from: from, to: to);
      return exact ?? input;
    }

    return _trie!.replaceLongestMatches(input);
  }
}

// -----------------
// Trie internals
// -----------------

class _Trie {
  final _TrieNode root = _TrieNode();

  void insert(String key, String value) {
    var node = root;
    for (final rune in key.runes) {
      final c = rune;
      node = node.children.putIfAbsent(c, () => _TrieNode());
    }
    node.value = value;
  }

  String replaceLongestMatches(String input) {
    final runes = input.runes.toList(growable: false);
    final out = StringBuffer();

    int i = 0;
    while (i < runes.length) {
      var node = root;
      int j = i;

      String? bestValue;
      int bestEnd = -1;

      while (j < runes.length) {
        final c = runes[j];
        final next = node.children[c];
        if (next == null) break;
        node = next;
        if (node.value != null) {
          bestValue = node.value;
          bestEnd = j;
        }
        j++;
      }

      if (bestValue != null && bestEnd >= i) {
        out.write(bestValue);
        i = bestEnd + 1;
      } else {
        out.write(String.fromCharCode(runes[i]));
        i++;
      }
    }

    return out.toString();
  }
}

class _TrieNode {
  final Map<int, _TrieNode> children = {};
  String? value;
}