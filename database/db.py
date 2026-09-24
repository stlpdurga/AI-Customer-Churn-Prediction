import json
import os
import sqlite3


def _postgres_url():
    return os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")


def _database_url_or_fail():
    database_url = _postgres_url()
    if os.getenv("VERCEL") == "1" and not database_url:
        raise RuntimeError("DATABASE_URL must be configured in Vercel project settings.")
    return database_url


def init_db():
    database_url = _database_url_or_fail()
    if database_url:
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(database_url, row_factory=dict_row)
        conn.execute("CREATE TABLE IF NOT EXISTS analyses (id BIGSERIAL PRIMARY KEY, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, dataset_name TEXT, payload TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS users (id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    else:
        conn = sqlite3.connect(os.getenv("DATABASE_PATH", "churn_history.db"))
        conn.execute("CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, dataset_name TEXT, payload TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()


def connection():
    database_url = _database_url_or_fail()
    if database_url:
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(database_url, row_factory=dict_row)
        conn.execute("CREATE TABLE IF NOT EXISTS analyses (id BIGSERIAL PRIMARY KEY, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, dataset_name TEXT, payload TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS users (id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    else:
        db_path = os.getenv("DATABASE_PATH", "churn_history.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, dataset_name TEXT, payload TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    return conn


def user_by_email(email):
    conn = connection()
    placeholder = "%s" if _postgres_url() else "?"
    user = conn.execute(f"SELECT id, name, email, password_hash FROM users WHERE email = {placeholder}", (email,)).fetchone()
    conn.close()
    return user


def create_user(name, email, password_hash):
    conn = connection()
    placeholder = "%s" if _postgres_url() else "?"
    statement = f"INSERT INTO users (name, email, password_hash) VALUES ({placeholder}, {placeholder}, {placeholder})"
    if _postgres_url():
        statement += " RETURNING id"
    cursor = conn.execute(statement, (name, email, password_hash))
    conn.commit()
    user_id = cursor.fetchone()["id"] if _postgres_url() else cursor.lastrowid
    conn.close()
    return user_id


def save(dataset_name, payload):
    conn = connection()
    placeholder = "%s" if _postgres_url() else "?"
    statement = f"INSERT INTO analyses (dataset_name, payload) VALUES ({placeholder}, {placeholder})"
    if _postgres_url():
        statement += " RETURNING id"
    cursor = conn.execute(statement, (dataset_name, json.dumps(payload, default=str)))
    conn.commit()
    analysis_id = cursor.fetchone()["id"] if _postgres_url() else cursor.lastrowid
    conn.close()
    return analysis_id


def history():
    conn = connection()
    rows = [dict(row) for row in conn.execute("SELECT id, created_at, dataset_name, payload FROM analyses ORDER BY id DESC LIMIT 25")]
    conn.close()
    for row in rows:
        row["payload"] = json.loads(row["payload"])
    return rows
