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


# ============================================================
#  详情表：crawl_sessions + crawl_records
# ============================================================

def init_detail_tables():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crawl_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            crawled_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crawl_records (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    INTEGER NOT NULL,
            game_id       INTEGER,
            detail_url    TEXT NOT NULL,
            game_name     TEXT,
            publish_date  TEXT,
            downloads     TEXT,
            followers     TEXT,
            rating        REAL,
            rating_count  TEXT,
            crawled_at    TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (session_id) REFERENCES crawl_sessions(id)
        )
    """)
    conn.commit()
    conn.close()


def create_crawl_session():
    conn = _connect()
    cursor = conn.execute("INSERT INTO crawl_sessions (crawled_at) VALUES (datetime('now','localtime'))")
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def insert_crawl_record(session_id, game_id, detail_url, game_name,
                        publish_date, downloads, followers, rating, rating_count):
    conn = _connect()
    conn.execute(
        """INSERT INTO crawl_records
           (session_id, game_id, detail_url, game_name, publish_date,
            downloads, followers, rating, rating_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, game_id, detail_url, game_name, publish_date,
         str(downloads) if downloads else "", str(followers) if followers else "",
         float(rating) if rating else None,
         str(rating_count) if rating_count else ""),
    )
    conn.commit()
    conn.close()


def get_detail_summary():
    conn = _connect()
    total_records = conn.execute("SELECT COUNT(*) FROM crawl_records").fetchone()[0]
    distinct_games = conn.execute(
        "SELECT COUNT(DISTINCT game_id) FROM crawl_records WHERE game_id IS NOT NULL"
    ).fetchone()[0]
    latest_session = conn.execute(
        "SELECT id, crawled_at FROM crawl_sessions ORDER BY id DESC LIMIT 1"
    ).fetchone()
    session_count = conn.execute("SELECT COUNT(*) FROM crawl_sessions").fetchone()[0]
    latest_count = 0
    if latest_session:
        latest_count = conn.execute(
            "SELECT COUNT(*) FROM crawl_records WHERE session_id=?", (latest_session[0],)
        ).fetchone()[0]
    conn.close()
    return {
        "total_records": total_records,
        "distinct_games": distinct_games,
        "session_count": session_count,
        "latest_session": latest_session,
        "latest_count": latest_count,
    }


def get_top_by_downloads(limit=10):
    conn = _connect()
    latest_session_id = conn.execute(
        "SELECT id FROM crawl_sessions ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not latest_session_id:
        conn.close()
        return []
    rows = conn.execute(
        """SELECT game_name, downloads, rating, followers, publish_date
           FROM crawl_records
           WHERE session_id = ? AND downloads != '' AND downloads != '获取失败'
           ORDER BY CAST(REPLACE(downloads, ',', '') AS INTEGER) DESC
           LIMIT ?""",
        (latest_session_id[0], limit),
    ).fetchall()
    conn.close()
    return rows


def get_top_by_rating(limit=10):
    conn = _connect()
    latest_session_id = conn.execute(
        "SELECT id FROM crawl_sessions ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not latest_session_id:
        conn.close()
        return []
    rows = conn.execute(
        """SELECT game_name, rating, downloads, followers, publish_date
           FROM crawl_records
           WHERE session_id = ? AND rating IS NOT NULL AND rating > 0
           ORDER BY rating DESC
           LIMIT ?""",
        (latest_session_id[0], limit),
    ).fetchall()
    conn.close()
    return rows


def get_crawl_sessions():
    conn = _connect()
    rows = conn.execute(
        """SELECT s.id, s.crawled_at,
                  (SELECT COUNT(*) FROM crawl_records WHERE session_id = s.id) as cnt
           FROM crawl_sessions s ORDER BY s.id DESC"""
    ).fetchall()
    conn.close()
    return rows


def get_crawl_records_count(session_id=None):
    conn = _connect()
    if session_id is None:
        count = conn.execute("SELECT COUNT(*) FROM crawl_records").fetchone()[0]
    else:
        count = conn.execute(
            "SELECT COUNT(*) FROM crawl_records WHERE session_id=?", (session_id,)
        ).fetchone()[0]
    conn.close()
    return count


def get_crawl_records(session_id, offset=0, limit=50):
    conn = _connect()
    rows = conn.execute(
        """SELECT id, game_name, detail_url, publish_date, downloads,
                  followers, rating, rating_count, crawled_at
           FROM crawl_records
           WHERE session_id = ?
           ORDER BY id
           LIMIT ? OFFSET ?""",
        (session_id, limit, offset),
    ).fetchall()
    conn.close()
    return rows
