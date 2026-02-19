from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from dd_cache.base import BaseCacheAdapter
from dd_cache.models import CacheStats
from dd_cache.utils import deserialize, serialize

_DEFAULT_PATH = ".cache/dd_cache.db"

_DDL = """
CREATE TABLE IF NOT EXISTS cache (
    key        TEXT PRIMARY KEY,
    value      BLOB NOT NULL,
    expires_at REAL
);
"""


class DiskCache(BaseCacheAdapter):
    """SQLite-backed persistent cache.

    Values are serialised with pickle.  Expired entries are evicted lazily
    on ``get()``.  The SQLite database file (and parent directories) are
    created automatically.
    """

    def __init__(self, path: str | Path = _DEFAULT_PATH) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path))
        self._conn.execute(_DDL)
        self._conn.commit()

    # ------------------------------------------------------------------
    # BaseCacheAdapter interface
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any:
        row = self._conn.execute(
            "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        value_blob, expires_at = row
        if expires_at is not None and time.time() > expires_at:
            self._conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            self._conn.commit()
            return None
        return deserialize(value_blob)

    def set(self, key: str, value: Any, *, ttl: Optional[int] = None) -> None:
        expires_at = time.time() + ttl if ttl is not None else None
        self._conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
            (key, serialize(value), expires_at),
        )
        self._conn.commit()

    def delete(self, key: str) -> bool:
        existed = self.exists(key)
        self._conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        self._conn.commit()
        return existed

    def exists(self, key: str) -> bool:
        row = self._conn.execute(
            "SELECT expires_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return False
        expires_at = row[0]
        if expires_at is not None and time.time() > expires_at:
            self._conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            self._conn.commit()
            return False
        return True

    def clear(self) -> None:
        self._conn.execute("DELETE FROM cache")
        self._conn.commit()

    def stats(self) -> CacheStats:
        now = time.time()
        row = self._conn.execute(
            "SELECT COUNT(*) FROM cache WHERE expires_at IS NULL OR expires_at > ?",
            (now,),
        ).fetchone()
        total = row[0] if row else 0
        ttl_row = self._conn.execute(
            "SELECT COUNT(*) FROM cache WHERE expires_at IS NOT NULL"
        ).fetchone()
        has_ttl = (ttl_row[0] > 0) if ttl_row else False
        return CacheStats(
            backend="disk",
            total_keys=total,
            ttl_enabled=has_ttl,
            extra={"path": str(self._path)},
        )

    def close(self) -> None:
        self._conn.close()
