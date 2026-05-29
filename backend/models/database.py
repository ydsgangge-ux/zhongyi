import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tcm_ai.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            tcm_analysis TEXT,
            western_reference TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            region TEXT,
            age INTEGER,
            gender TEXT,
            season TEXT,
            messages TEXT,
            inquiry_data TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def save_health_record(session_id: str, notes: Optional[str] = None) -> Optional[dict]:
    conn = get_db()
    session = conn.execute(
        "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    if not session:
        conn.close()
        return None

    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO health_records (session_id, tcm_analysis, western_reference, notes, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, session["messages"], json.dumps({}), notes, now),
    )
    conn.commit()
    record = conn.execute(
        "SELECT * FROM health_records WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    return dict(record) if record else None


def get_health_records(limit: int = 20, offset: int = 0) -> List[dict]:
    conn = get_db()
    records = conn.execute(
        "SELECT * FROM health_records ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in records]


init_db()
