"""Server-side free-tier daily quota per client_id (SQLite)."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Tuple


class SqliteDailyQuota:
    """Atomic increment with daily limit per (client_id, day_utc)."""

    def __init__(self, db_path: str) -> None:
        self._path = db_path
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self._path, timeout=30)
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def _init_db(self) -> None:
        c = self._conn()
        try:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS glb_client_daily (
                    client_id TEXT NOT NULL,
                    day_utc TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (client_id, day_utc)
                )
                """
            )
        finally:
            c.close()

    def try_consume_one(self, client_id: str, day_utc: str, limit: int) -> Tuple[bool, int]:
        """
        Increment count by 1 if below limit. Returns (allowed, count_after_attempt).
        If not allowed, count is unchanged.
        """
        with self._lock:
            c = self._conn()
            try:
                c.execute("BEGIN IMMEDIATE")
                cur = c.execute(
                    "SELECT count FROM glb_client_daily WHERE client_id = ? AND day_utc = ?",
                    (client_id, day_utc),
                )
                row = cur.fetchone()
                current = int(row[0]) if row else 0
                if current >= limit:
                    c.execute("ROLLBACK")
                    return False, current
                new_val = current + 1
                c.execute(
                    """
                    INSERT INTO glb_client_daily (client_id, day_utc, count)
                    VALUES (?, ?, ?)
                    ON CONFLICT(client_id, day_utc) DO UPDATE SET count = excluded.count
                    """,
                    (client_id, day_utc, new_val),
                )
                c.execute("COMMIT")
                return True, new_val
            finally:
                c.close()
