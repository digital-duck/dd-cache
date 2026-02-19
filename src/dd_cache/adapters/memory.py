from __future__ import annotations

import time
from typing import Any, Optional

from dd_cache.base import BaseCacheAdapter
from dd_cache.models import CacheStats


class InMemoryCache(BaseCacheAdapter):
    """Thread-unsafe in-process cache backed by a plain dict.

    TTL is enforced lazily: expired entries are treated as cache misses on
    ``get()`` / ``exists()`` without a background sweep thread.
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}  # unix timestamp of expiry

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_expired(self, key: str) -> bool:
        exp = self._expiry.get(key)
        return exp is not None and time.time() > exp

    def _evict(self, key: str) -> None:
        self._store.pop(key, None)
        self._expiry.pop(key, None)

    # ------------------------------------------------------------------
    # BaseCacheAdapter interface
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any:
        if self._is_expired(key):
            self._evict(key)
            return None
        return self._store.get(key)

    def set(self, key: str, value: Any, *, ttl: Optional[int] = None) -> None:
        self._store[key] = value
        if ttl is not None:
            self._expiry[key] = time.time() + ttl
        else:
            self._expiry.pop(key, None)

    def delete(self, key: str) -> bool:
        existed = key in self._store and not self._is_expired(key)
        self._evict(key)
        return existed

    def exists(self, key: str) -> bool:
        if key not in self._store:
            return False
        if self._is_expired(key):
            self._evict(key)
            return False
        return True

    def clear(self) -> None:
        self._store.clear()
        self._expiry.clear()

    def stats(self) -> CacheStats:
        # Count only non-expired keys
        now = time.time()
        live = sum(
            1 for k in self._store
            if k not in self._expiry or self._expiry[k] > now
        )
        return CacheStats(
            backend="memory",
            total_keys=live,
            ttl_enabled=bool(self._expiry),
        )

    def close(self) -> None:
        pass  # nothing to flush or disconnect
