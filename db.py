"""
db.py — SQLite storage layer for the Quran Tafseer / Hadees Sharah bot.

One simple table holds everything (Quran translation, Tafseer, Hadees, Sharah).
This keeps searching easy: one query checks every content type and every language.
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "islamic_bot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type TEXT NOT NULL,      -- 'quran_translation' | 'tafsir' | 'hadith' | 'sharah'
    language   TEXT NOT NULL,      -- 'ar' | 'en' | 'ur' | 'ta'
    term       TEXT,               -- search keyword / topic (optional, e.g. 'sabr', 'zakat')
    source     TEXT,               -- book/author name, e.g. 'Ibn Kathir', 'Sahih Bukhari'
    reference  TEXT,               -- e.g. 'Surah 2:255' or 'Bukhari 1:1'
    content    TEXT NOT NULL,      -- the actual text
    added_by   TEXT DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_entries_term ON entries(term);
CREATE INDEX IF NOT EXISTS idx_entries_lang ON entries(language);
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    term, content, content='entries', content_rowid='id'
);
"""

# Keep the FTS index in sync with the main table automatically.
TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
  INSERT INTO entries_fts(rowid, term, content) VALUES (new.id, new.term, new.content);
END;
CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
  INSERT INTO entries_fts(entries_fts, rowid, term, content) VALUES('delete', old.id, old.term, old.content);
END;
CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
  INSERT INTO entries_fts(entries_fts, rowid, term, content) VALUES('delete', old.id, old.term, old.content);
  INSERT INTO entries_fts(rowid, term, content) VALUES (new.id, new.term, new.content);
END;
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.executescript(TRIGGERS)


def add_entry(entry_type, language, content, term=None, source=None, reference=None, added_by="system"):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO entries (entry_type, language, term, source, reference, content, added_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entry_type, language, term, source, reference, content, added_by),
        )


def bulk_add(rows):
    """rows: list of dicts with keys entry_type, language, content, term, source, reference"""
    with get_conn() as conn:
        conn.executemany(
            """INSERT INTO entries (entry_type, language, term, source, reference, content, added_by)
               VALUES (:entry_type, :language, :term, :source, :reference, :content, :added_by)""",
            rows,
        )


def search(query, language=None, entry_type=None, limit=8):
    """Full-text search across term + content. Optionally filter by language / type."""
    sql = """
        SELECT e.entry_type, e.language, e.term, e.source, e.reference, e.content
        FROM entries_fts f
        JOIN entries e ON e.id = f.rowid
        WHERE entries_fts MATCH ?
    """
    params = [query]
    if language:
        sql += " AND e.language = ?"
        params.append(language)
    if entry_type:
        sql += " AND e.entry_type = ?"
        params.append(entry_type)
    sql += " LIMIT ?"
    params.append(limit)

    with get_conn() as conn:
        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            # FTS5 raises on some special characters — fall back to plain LIKE search
            like_sql = """
                SELECT entry_type, language, term, source, reference, content
                FROM entries
                WHERE (term LIKE ? OR content LIKE ?)
            """
            like_params = [f"%{query}%", f"%{query}%"]
            if language:
                like_sql += " AND language = ?"
                like_params.append(language)
            if entry_type:
                like_sql += " AND entry_type = ?"
                like_params.append(entry_type)
            like_sql += " LIMIT ?"
            like_params.append(limit)
            rows = conn.execute(like_sql, like_params).fetchall()
        return [dict(r) for r in rows]


def stats():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT entry_type, language, COUNT(*) c FROM entries GROUP BY entry_type, language"
        ).fetchall()
        return [dict(r) for r in rows]
