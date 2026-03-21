import sqlite3
from pathlib import Path

from app.config import settings


def get_db() -> sqlite3.Connection:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (datetime('now')),
            ip TEXT,
            route TEXT,
            model_requested TEXT,
            provider_used TEXT,
            status_code INTEGER,
            response_time_ms INTEGER,
            tokens_in INTEGER,
            tokens_out INTEGER
        )
    """)
    conn.commit()
    conn.close()
