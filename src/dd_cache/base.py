from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from dd_cache.models import CacheStats


class BaseCacheAdapter(ABC):

    @abstractmethod
    def get(self, key: str) -> Any:
        """Return the cached value or None on a cache miss."""

    @abstractmethod
    def set(self, key: str, value: Any, *, ttl: Optional[int] = None) -> None:
        """Store *value* under *key*.  *ttl* is seconds; None means no expiry."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove *key*.  Returns True if the key existed, False otherwise."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if *key* is present (and not expired)."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries from the cache."""

    @abstractmethod
    def stats(self) -> CacheStats:
        """Return a snapshot of cache statistics."""

    @abstractmethod
    def close(self) -> None:
        """Flush buffers and release resources (disconnect, close file handles)."""

    # ------------------------------------------------------------------
    # Concrete helpers
    # ------------------------------------------------------------------

    def get_or_set(self, key: str, fn: Callable[[], Any], *, ttl: Optional[int] = None) -> Any:
        """Return the cached value for *key*; if missing, call *fn()*, store the
        result, and return it.  Handles None values correctly by using exists()
        before get()."""
        if self.exists(key):
            return self.get(key)
        value = fn()
        self.set(key, value, ttl=ttl)
        return value

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "BaseCacheAdapter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
