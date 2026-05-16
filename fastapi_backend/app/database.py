from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")


def malaysia_timestamp() -> str:
    """Return ISO timestamp in Malaysia time (UTC/GMT+8)."""
    return datetime.now(MALAYSIA_TZ).isoformat(timespec="seconds")


def derive_status(prediction_text: Optional[str]) -> str:
    if str(prediction_text).strip().lower() == "fall":
        return "Alert"
    if str(prediction_text).strip().lower() in {"non-fall", "nonfall", "normal"}:
        return "Normal"
    return "Unknown"


def frontend_friendly_record(row: Dict[str, Any]) -> Dict[str, Any]:
    """Add stable aliases so Figma/React dashboards can map fields easily."""
    r = dict(row)

    if r.get("correct") is not None:
        r["correct"] = bool(r["correct"])

    if not r.get("input_mode"):
        r["input_mode"] = "MANUAL TEST"

    r["status"] = derive_status(r.get("prediction_text"))
    r["timestamp_timezone"] = "Asia/Kuala_Lumpur"
    r["timestamp_gmt_offset"] = "+08:00"

    # Aliases for frontends that use different field names.
    r["filename"] = r.get("file_name")
    r["classified_activity"] = r.get("prediction_text")
    r["fall_confidence"] = r.get("probability")
    try:
        r["fall_confidence_percent"] = None if r.get("probability") is None else round(float(r.get("probability")) * 100, 2)
    except Exception:
        r["fall_confidence_percent"] = None

    # User-friendly dashboard labels while preserving raw values.
    r["display_model_name"] = "MTFF" if r.get("model_name") in {"Balanced_COMB", "Balanced COMB", "COMB"} else r.get("model_name")
    r["display_feature_source"] = "Feature Bank" if r.get("feature_source") == "precomputed_feature_bank" else r.get("feature_source")

    return r


class PredictionLogDB:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _table_columns(self, conn) -> set[str]:
        cur = conn.execute("PRAGMA table_info(prediction_logs)")
        return {row[1] for row in cur.fetchall()}

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    file_name TEXT,
                    input_mode TEXT,
                    prediction_label INTEGER,
                    prediction_text TEXT,
                    probability REAL,
                    threshold REAL,
                    risk_level TEXT,
                    model_name TEXT,
                    feature_source TEXT,
                    processing_time_sec REAL,
                    actual_label INTEGER,
                    actual_event TEXT,
                    correct INTEGER
                )
                """
            )

            columns = self._table_columns(conn)
            if "input_mode" not in columns:
                conn.execute("ALTER TABLE prediction_logs ADD COLUMN input_mode TEXT")

            conn.commit()

    def insert(self, item: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = malaysia_timestamp()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO prediction_logs (
                    timestamp, file_name, input_mode, prediction_label, prediction_text, probability,
                    threshold, risk_level, model_name, feature_source, processing_time_sec,
                    actual_label, actual_event, correct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    item.get("file_name"),
                    item.get("input_mode"),
                    item.get("prediction_label"),
                    item.get("prediction_text"),
                    item.get("probability"),
                    item.get("threshold"),
                    item.get("risk_level"),
                    item.get("model_name"),
                    item.get("feature_source"),
                    item.get("processing_time_sec"),
                    item.get("actual_label"),
                    item.get("actual_event"),
                    None if item.get("correct") is None else int(bool(item.get("correct"))),
                ),
            )
            conn.commit()
            item["id"] = cur.lastrowid
            item["timestamp"] = timestamp
        return frontend_friendly_record(item)

    def latest(self) -> Optional[Dict[str, Any]]:
        rows = self.history(limit=1)
        return rows[0] if rows else None

    def history(self, limit: int = 20) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM prediction_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = [frontend_friendly_record(dict(r)) for r in cur.fetchall()]
        return rows

    def delete_one(self, record_id: int) -> Dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM prediction_logs WHERE id = ?", (int(record_id),))
            conn.commit()
            deleted = int(cur.rowcount)
        return {"deleted": deleted, "id": int(record_id)}

    def clear_manual(self) -> Dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                DELETE FROM prediction_logs
                WHERE input_mode IN ('MANUAL TEST', 'MANUAL UPLOAD')
                   OR input_mode IS NULL
                   OR input_mode = ''
                """
            )
            conn.commit()
            deleted = int(cur.rowcount)
        return {"deleted": deleted, "scope": "manual_only"}

    def clear_all(self) -> Dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM prediction_logs")
            conn.commit()
            deleted = int(cur.rowcount)
        return {"deleted": deleted, "scope": "all"}
