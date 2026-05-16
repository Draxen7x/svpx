import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "svpx.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            icon TEXT DEFAULT 'fas fa-folder',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            filename TEXT,
            original_filename TEXT,
            file_size INTEGER DEFAULT 0,
            image_url TEXT,
            file_url TEXT,
            version TEXT DEFAULT '1.0',
            downloads_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT DEFAULT 'SVPX Admin',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)

    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cats = [
            ("CLEO", "cleo", "fas fa-code"),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO categories (name, slug, icon) VALUES (?, ?, ?)",
            cats
        )

    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        settings = [
            ("site_name", "SVPX Community"),
            ("server_ip", "127.0.0.1:7777"),
            ("server_name", "SVPX Roleplay"),
            ("max_players", "500"),
            ("discord_link", "https://discord.gg/zp4qXWwWw"),
            ("website_version", "1.0.0"),
            ("description", "Elite SA-MP modding community. Premium CLEO scripts, tools, and resources."),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            settings
        )

    conn.commit()
    conn.close()

def get_categories():
    conn = get_db()
    cur = conn.execute("SELECT * FROM categories ORDER BY name")
    items = cur.fetchall()
    conn.close()
    return [dict(c) for c in items]

def get_downloads(category_slug=None, search=None):
    conn = get_db()
    query = """
        SELECT d.*, c.name as category_name, c.slug as category_slug, c.icon as category_icon
        FROM downloads d
        LEFT JOIN categories c ON d.category_id = c.id
        WHERE 1=1
    """
    params = []
    if category_slug:
        query += " AND c.slug = ?"
        params.append(category_slug)
    if search:
        query += " AND (d.title LIKE ? OR d.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY d.created_at DESC"
    cur = conn.execute(query, params)
    items = cur.fetchall()
    conn.close()
    return [dict(i) for i in items]

def get_download_by_id(download_id):
    conn = get_db()
    cur = conn.execute("""
        SELECT d.*, c.name as category_name, c.slug as category_slug
        FROM downloads d
        LEFT JOIN categories c ON d.category_id = c.id
        WHERE d.id = ?
    """, (download_id,))
    item = cur.fetchone()
    conn.close()
    return dict(item) if item else None

def increment_download_count(download_id):
    conn = get_db()
    conn.execute("UPDATE downloads SET downloads_count = downloads_count + 1 WHERE id = ?", (download_id,))
    conn.commit()
    conn.close()

def add_download(title, description, category_id, filename, original_filename, file_size, image_url, file_url, version):
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO downloads (title, description, category_id, filename, original_filename, file_size, image_url, file_url, version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, description, category_id, filename, original_filename, file_size, image_url, file_url, version))
    conn.commit()
    did = cur.lastrowid
    conn.close()
    return did

def update_download(download_id, title, description, category_id, version, image_url, file_url, filename=None, original_filename=None, file_size=None):
    conn = get_db()
    if filename:
        conn.execute("""
            UPDATE downloads SET title=?, description=?, category_id=?, version=?,
            image_url=?, file_url=?, filename=?, original_filename=?, file_size=?
            WHERE id=?
        """, (title, description, category_id, version, image_url, file_url, filename, original_filename, file_size, download_id))
    else:
        conn.execute("""
            UPDATE downloads SET title=?, description=?, category_id=?, version=?,
            image_url=?, file_url=?
            WHERE id=?
        """, (title, description, category_id, version, image_url, file_url, download_id))
    conn.commit()
    conn.close()

def delete_download(download_id):
    conn = get_db()
    conn.execute("DELETE FROM downloads WHERE id=?", (download_id,))
    conn.commit()
    conn.close()

def get_news(limit=None):
    conn = get_db()
    query = "SELECT * FROM news ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {limit}"
    cur = conn.execute(query)
    items = cur.fetchall()
    conn.close()
    return [dict(n) for n in items]

def add_news(title, content, author="SVPX Admin"):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO news (title, content, author) VALUES (?, ?, ?)",
        (title, content, author)
    )
    conn.commit()
    nid = cur.lastrowid
    conn.close()
    return nid

def delete_news(news_id):
    conn = get_db()
    conn.execute("DELETE FROM news WHERE id=?", (news_id,))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = get_db()
    cur = conn.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else None

def update_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_db()
    total_downloads = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
    total_categories = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    total_news = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
    total_dl_count = conn.execute("SELECT COALESCE(SUM(downloads_count), 0) FROM downloads").fetchone()[0]
    recent = conn.execute("""
        SELECT d.*, c.name as category_name FROM downloads d
        LEFT JOIN categories c ON d.category_id = c.id
        ORDER BY d.created_at DESC LIMIT 5
    """).fetchall()
    conn.close()
    return {
        "total_downloads": total_downloads,
        "total_categories": total_categories,
        "total_news": total_news,
        "total_dl_count": total_dl_count,
        "recent_downloads": [dict(d) for d in recent],
    }

def add_category(name, slug, icon="fas fa-folder"):
    conn = get_db()
    try:
        conn.execute("INSERT INTO categories (name, slug, icon) VALUES (?, ?, ?)", (name, slug, icon))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def delete_category(category_id):
    conn = get_db()
    conn.execute("DELETE FROM categories WHERE id=?", (category_id,))
    conn.commit()
    conn.close()

def get_category_by_id(category_id):
    conn = get_db()
    cur = conn.execute("SELECT * FROM categories WHERE id=?", (category_id,))
    item = cur.fetchone()
    conn.close()
    return dict(item) if item else None

def update_category(category_id, name, slug, icon):
    conn = get_db()
    conn.execute("UPDATE categories SET name=?, slug=?, icon=? WHERE id=?", (name, slug, icon, category_id))
    conn.commit()
    conn.close()
