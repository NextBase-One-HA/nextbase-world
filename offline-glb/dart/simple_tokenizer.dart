// simple_tokenizer.dart
import 'tokenizer_interface.dart';

/// MVP tokenizer:
/// - preserves whitespace as tokens
/// - splits "words" by whitespace boundaries
/// - keeps punctuation attached to word (postRewrite can fix spacing later)
class SimpleTokenizer implements Tokenizer {
  @override
  List<Token> tokenize(String input, {required String lang}) {
    if (input.isEmpty) return const [];

    final tokens = <Token>[];
    final buf = StringBuffer();
    TokenType? current;

    void flush() {
      if (buf.isEmpty || current == null) return;
      tokens.add(Token(buf.toString(), current!));
      buf.clear();
    }

    for (final rune in input.runes) {
      final ch = String.fromCharCode(rune);
      final isWs = ch.trim().isEmpty;

      final t = isWs ? TokenType.whitespace : TokenType.word;
      if (current == null) {
        current = t;
        buf.write(ch);
        continue;
      }
      if (t != current) {
        flush();
        current = t;
      }
      buf.write(ch);
    }
    flush();

    return tokens;
  }
}