"""SQLite-backed cache with TTL for sports data (stdlib only).

Why a cache: ESPN is unofficial and rate-sensitive; API-Football has paid quotas. The Hub reads
through this cache so we minimize calls and can serve **stale** data if a provider is down.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

DEFAULT_DB = Path("data") / "sports_cache.db"


class SportsCache:
    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache ("
                "key TEXT PRIMARY KEY, value TEXT NOT NULL, ts REAL NOT NULL)"
            )

    def set(self, key: str, value: Any) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO cache(key, value, ts) VALUES(?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, ts=excluded.ts",
                (key, json.dumps(value), time.time()),
            )

    def get(self, key: str, ttl: float) -> Optional[Any]:
        """Return the cached value if it exists and is younger than ``ttl`` seconds, else None."""
        row = self._row(key)
        if row and (time.time() - row["ts"]) <= ttl:
            return json.loads(row["value"])
        return None

    def get_stale(self, key: str) -> Optional[dict]:
        """Return {'value', 'age'} regardless of TTL (used as fallback when a provider is down)."""
        row = self._row(key)
        if row:
            return {"value": json.loads(row["value"]), "age": round(time.time() - row["ts"], 1)}
        return None

    def age(self, key: str) -> Optional[float]:
        row = self._row(key)
        return round(time.time() - row["ts"], 1) if row else None

    def _row(self, key: str):
        with self._connect() as conn:
            cur = conn.execute("SELECT value, ts FROM cache WHERE key = ?", (key,))
            return cur.fetchone()
