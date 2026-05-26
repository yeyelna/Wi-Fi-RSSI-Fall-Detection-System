import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "history.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            timestamp_display TEXT NOT NULL,
            input_mode TEXT NOT NULL,
            record_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def insert_record(record: Dict):
    init_db()
    conn = get_connection()
    conn.execute(
        """
        INSERT OR REPLACE INTO history
        (id, timestamp, timestamp_display, input_mode, record_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            record["id"],
            record["timestamp"],
            record["timestamp_display"],
            record["input_mode"],
            json.dumps(record),
        ),
    )
    conn.commit()
    conn.close()


def list_records(limit: int = 20) -> List[Dict]:
    init_db()
    limit = max(1, min(int(limit), 500))
    conn = get_connection()
    rows = conn.execute(
        "SELECT record_json FROM history ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [json.loads(row["record_json"]) for row in rows]


def latest_record() -> Optional[Dict]:
    records = list_records(limit=1)
    return records[0] if records else None


def delete_record(record_id: str) -> bool:
    init_db()
    conn = get_connection()
    cur = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def delete_manual_records() -> int:
    init_db()
    conn = get_connection()
    cur = conn.execute("DELETE FROM history WHERE input_mode IN ('MANUAL TEST', 'MANUAL UPLOAD')")
    conn.commit()
    count = cur.rowcount
    conn.close()
    return count


def delete_all_records() -> int:
    init_db()
    conn = get_connection()
    cur = conn.execute("DELETE FROM history")
    conn.commit()
    count = cur.rowcount
    conn.close()
    return count
