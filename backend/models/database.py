import sqlite3
import json
import os
from datetime import datetime, timedelta
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
    # 旧库迁移：补充问诊过程字段
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(health_records)")}
    if "messages" not in columns:
        conn.execute("ALTER TABLE health_records ADD COLUMN messages TEXT")
    # 旧库迁移：补全会话快照字段
    session_columns = {row["name"] for row in conn.execute("PRAGMA table_info(sessions)")}
    if "data" not in session_columns:
        conn.execute("ALTER TABLE sessions ADD COLUMN data TEXT")
    conn.commit()
    conn.close()


def _row_to_record(row) -> dict:
    record = dict(row)
    for key in ("tcm_analysis", "western_reference"):
        try:
            record[key] = json.loads(record[key]) if record.get(key) else {}
        except (json.JSONDecodeError, TypeError):
            record[key] = {}
    try:
        record["messages"] = json.loads(record["messages"]) if record.get("messages") else []
    except (json.JSONDecodeError, TypeError):
        record["messages"] = []
    return record


def save_health_record(
    session_id: str,
    tcm_analysis: Optional[dict] = None,
    western_reference: Optional[dict] = None,
    notes: Optional[str] = None,
    messages: Optional[list] = None,
) -> dict:
    now = datetime.now().isoformat()
    conn = get_db()
    # 同一会话重复分析时覆盖旧记录，避免历史列表出现重复条目
    conn.execute("DELETE FROM health_records WHERE session_id = ?", (session_id,))
    conn.execute(
        "INSERT INTO health_records (session_id, tcm_analysis, western_reference, notes, messages, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            session_id,
            json.dumps(tcm_analysis or {}, ensure_ascii=False),
            json.dumps(western_reference or {}, ensure_ascii=False),
            notes,
            json.dumps(messages or [], ensure_ascii=False),
            now,
        ),
    )
    conn.commit()
    record = conn.execute(
        "SELECT * FROM health_records WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    return _row_to_record(record) if record else None


def get_health_record_by_session(session_id: str) -> Optional[dict]:
    conn = get_db()
    record = conn.execute(
        "SELECT * FROM health_records WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    return _row_to_record(record) if record else None


def get_health_records(limit: int = 20, offset: int = 0) -> List[dict]:
    conn = get_db()
    records = conn.execute(
        "SELECT * FROM health_records ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [_row_to_record(r) for r in records]


def save_session(session: dict) -> None:
    """把内存会话快照写入数据库，服务重启后可恢复。"""
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO sessions
           (session_id, region, age, gender, season, messages, inquiry_data, data, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session.get("session_id"),
            session.get("region"),
            session.get("age"),
            session.get("gender"),
            session.get("season"),
            json.dumps(session.get("messages") or [], ensure_ascii=False),
            json.dumps(session.get("inquiry_data") or {}, ensure_ascii=False),
            json.dumps(session, ensure_ascii=False),
            session.get("created_at") or datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def load_session(session_id: str, max_age_hours: int = 24) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    if not row["data"]:
        return None
    try:
        session = json.loads(row["data"])
    except (json.JSONDecodeError, TypeError):
        return None

    created_at = session.get("created_at")
    if created_at:
        try:
            if datetime.now() - datetime.fromisoformat(created_at) > timedelta(hours=max_age_hours):
                delete_session(session_id)
                return None
        except ValueError:
            pass
    return session


def delete_session(session_id: str) -> None:
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def delete_expired_sessions(max_age_hours: int = 24) -> int:
    cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
    conn = get_db()
    cursor = conn.execute("DELETE FROM sessions WHERE created_at < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


init_db()
