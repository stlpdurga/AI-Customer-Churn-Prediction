import json
import os
import sqlite3


def init_db():
    conn = sqlite3.connect(os.getenv("DATABASE_PATH", "churn_history.db"))
    conn.execute("CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, dataset_name TEXT, payload TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()


def connection():
    db_path = os.getenv("DATABASE_PATH", "churn_history.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, dataset_name TEXT, payload TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    return conn


def user_by_email(email):
    conn = connection()
    user = conn.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user


def create_user(name, email, password_hash):
    conn = connection()
    cursor = conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, password_hash))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def save(dataset_name, payload):
    conn = connection()
    cursor = conn.execute("INSERT INTO analyses (dataset_name, payload) VALUES (?, ?)", (dataset_name, json.dumps(payload, default=str)))
    conn.commit()
    analysis_id = cursor.lastrowid
    conn.close()
    return analysis_id


def history():
    conn = connection()
    rows = [dict(row) for row in conn.execute("SELECT id, created_at, dataset_name, payload FROM analyses ORDER BY id DESC LIMIT 25")]
    conn.close()
    for row in rows:
        row["payload"] = json.loads(row["payload"])
    return rows
