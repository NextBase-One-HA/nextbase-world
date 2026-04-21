// sqflite_dictionary.dart
import 'dart:async';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import 'sqlite_dictionary.dart';

/// SQLite-backed dictionary for Tomori Public v0.2.
/// Tables expected:
/// - entries: (lang_from TEXT, lang_to TEXT, src TEXT, dst TEXT, kind TEXT, priority INTEGER)
///     kind = 'word' | 'phrase'
/// - templates: (lang_from TEXT, lang_to TEXT, pattern TEXT, rewrite TEXT, priority INTEGER)
///
/// Index recommended:
/// - CREATE INDEX idx_entries_pair_src ON entries(lang_from, lang_to, src);
/// - CREATE INDEX idx_templates_pair_pri ON templates(lang_from, lang_to, priority DESC);
class SqfliteDictionary implements OfflineDictionary {
  SqfliteDictionary({
    this.dbFileName = 'glb_offline_dict.db',
    this.onCreateSeed,
  });

  final String dbFileName;

  /// Optional: seed initial data on first DB creation.
  /// Use to insert minimal phrase/word/templates for MVP.
  final Future<void> Function(Database db)? onCreateSeed;

  Database? _db;
  final Set<String> _readyPairs = {};

  Future<Database> _open() async {
    if (_db != null) return _db!;
    final base = await getDatabasesPath();
    final path = p.join(base, dbFileName);

    _db = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await _createSchema(db);
        if (onCreateSeed != null) {
          await onCreateSeed!(db);
        }
      },
    );
    return _db!;
  }

  Future<void> close() async {
    final db = _db;
    _db = null;
    _readyPairs.clear();
    if (db != null) await db.close();
  }

  Future<void> _createSchema(Database db) async {
    await db.execute('''
CREATE TABLE IF NOT EXISTS entries(
  lang_from TEXT NOT NULL,
  lang_to   TEXT NOT NULL,
  src       TEXT NOT NULL,
  dst       TEXT NOT NULL,
  kind      TEXT NOT NULL,   -- 'word' or 'phrase'
  priority  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (lang_from, lang_to, src, kind)
);
''');

    await db.execute('''
CREATE TABLE IF NOT EXISTS templates(
  lang_from TEXT NOT NULL,
  lang_to   TEXT NOT NULL,
  pattern   TEXT NOT NULL,
  rewrite   TEXT NOT NULL,
  priority  INTEGER NOT NULL DEFAULT 0
);
''');

    await db.execute('''
CREATE INDEX IF NOT EXISTS idx_entries_pair_src
ON entries(lang_from, lang_to, src);
''');

    await db.execute('''
CREATE INDEX IF NOT EXISTS idx_templates_pair_pri
ON templates(lang_from, lang_to, priority DESC);
''');
  }

  @override
  Future<void> ensureReady({required String from, required String to}) async {
    await _open();
    final key = '$from>$to';
    if (_readyPairs.contains(key)) return;

    // Hook for future: load phrase list / build trie cache outside.
    _readyPairs.add(key);
  }

  @override
  Future<String?> lookupPhrase({
    required String src,
    required String from,
    required String to,
  }) async {
    final db = await _open();
    final rows = await db.query(
      'entries',
      columns: ['dst'],
      where: 'lang_from=? AND lang_to=? AND src=? AND kind=?',
      whereArgs: [from, to, src, 'phrase'],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return rows.first['dst'] as String?;
  }

  @override
  Future<String?> lookupWord({
    required String src,
    required String from,
    required String to,
  }) async {
    final db = await _open();
    final rows = await db.query(
      'entries',
      columns: ['dst'],
      where: 'lang_from=? AND lang_to=? AND src=? AND kind=?',
      whereArgs: [from, to, src, 'word'],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return rows.first['dst'] as String?;
  }

  @override
  Future<List<TemplateRule>> listTemplates({
    required String from,
    required String to,
  }) async {
    final db = await _open();
    final rows = await db.query(
      'templates',
      columns: ['pattern', 'rewrite', 'priority'],
      where: 'lang_from=? AND lang_to=?',
      whereArgs: [from, to],
      orderBy: 'priority DESC',
    );

    return rows
        .map((r) => TemplateRule(
              pattern: r['pattern'] as String,
              rewrite: r['rewrite'] as String,
              priority: (r['priority'] as int?) ?? 0,
            ))
        .toList(growable: false);
  }

  // ---------------------------
  // Utilities for seeding / update
  // ---------------------------

  Future<void> upsertWord({
    required String from,
    required String to,
    required String src,
    required String dst,
    int priority = 0,
  }) async {
    final db = await _open();
    await db.insert(
      'entries',
      {
        'lang_from': from,
        'lang_to': to,
        'src': src,
        'dst': dst,
        'kind': 'word',
        'priority': priority,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> upsertPhrase({
    required String from,
    required String to,
    required String src,
    required String dst,
    int priority = 0,
  }) async {
    final db = await _open();
    await db.insert(
      'entries',
      {
        'lang_from': from,
        'lang_to': to,
        'src': src,
        'dst': dst,
        'kind': 'phrase',
        'priority': priority,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> insertTemplate({
    required String from,
    required String to,
    required String pattern,
    required String rewrite,
    int priority = 0,
  }) async {
    final db = await _open();
    await db.insert(
      'templates',
      {
        'lang_from': from,
        'lang_to': to,
        'pattern': pattern,
        'rewrite': rewrite,
        'priority': priority,
      },
      conflictAlgorithm: ConflictAlgorithm.abort,
    );
  }

  /// For building Trie: list all phrase keys for a lang pair.
  Future<List<String>> listPhraseKeys({
    required String from,
    required String to,
    int? limit,
  }) async {
    final db = await _open();
    final rows = await db.query(
      'entries',
      columns: ['src'],
      where: 'lang_from=? AND lang_to=? AND kind=?',
      whereArgs: [from, to, 'phrase'],
      orderBy: 'length(src) DESC', // helps building longest-first lists
      limit: limit,
    );
    return rows.map((r) => r['src'] as String).toList(growable: false);
  }
}