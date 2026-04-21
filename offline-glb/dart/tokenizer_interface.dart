// tokenizer_interface.dart

/// Token types kept minimal on purpose.
/// Extend later if needed (e.g., punctuation, numbers).
enum TokenType { word, whitespace }

class Token {
  Token(this.text, this.type);

  final String text;
  final TokenType type;

  @override
  String toString() => 'Token($type, "$text")';
}

abstract class Tokenizer {
  /// Tokenize input string for a language.
  /// Must preserve whitespaces as tokens to keep layout.
  List<Token> tokenize(String input, {required String lang});
}