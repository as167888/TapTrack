import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games.db")


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            app_id      TEXT    NOT NULL,
            detail_url  TEXT    NOT NULL UNIQUE,
            category    TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.commit()
    conn.close()


def insert_game(name, app_id, detail_url, category=""):
    """Insert a game if not exists. Returns True if inserted, False if already present."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO games (name, app_id, detail_url, category) VALUES (?, ?, ?, ?)",
            (name, app_id, detail_url, category),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_stats():
    """Return total game count in database."""
    conn = _connect()
    row = conn.execute("SELECT COUNT(*) FROM games").fetchone()
    conn.close()
    return row[0]


def get_all_games():
    """Return all games as list of (name, detail_url)."""
    conn = _connect()
    rows = conn.execute(
        "SELECT name, detail_url FROM games ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def get_all_games_full():
    """Return all games as list of (id, name, app_id, detail_url, category, created_at)."""
    conn = _connect()
    rows = conn.execute(
        "SELECT id, name, app_id, detail_url, category, created_at FROM games ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def get_games_by_category(category):
    """Return games filtered by category."""
    conn = _connect()
    rows = conn.execute(
        "SELECT id, name, app_id, detail_url, category, created_at FROM games WHERE category=? ORDER BY id",
        (category,),
    ).fetchall()
    conn.close()
    return rows


def get_game_count_by_category():
    """Return list of (category, count) tuples."""
    conn = _connect()
    rows = conn.execute(
        "SELECT category, COUNT(*) FROM games GROUP BY category ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()
    return rows


def get_recent_games(limit=50):
    """Return the most recently added games."""
    conn = _connect()
    rows = conn.execute(
        "SELECT id, name, app_id, detail_url, category, created_at FROM games ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def search_games(keyword):
    """Search games by name (fuzzy match)."""
    conn = _connect()
    rows = conn.execute(
        "SELECT id, name, app_id, detail_url, category, created_at FROM games WHERE name LIKE ? ORDER BY id",
        (f"%{keyword}%",),
    ).fetchall()
    conn.close()
    return rows


def delete_game(game_id):
    """Delete a game by id. Returns True if deleted."""
    conn = _connect()
    cursor = conn.execute("DELETE FROM games WHERE id=?", (game_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_all_categories():
    """Return distinct category names."""
    conn = _connect()
    rows = conn.execute(
        "SELECT DISTINCT category FROM games ORDER BY category"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_paginated_games(offset=0, limit=50):
    """Return paginated games and total count. Returns (rows, total)."""
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    rows = conn.execute(
        "SELECT id, name, app_id, detail_url, category, created_at FROM games ORDER BY id LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    conn.close()
    return rows, total
