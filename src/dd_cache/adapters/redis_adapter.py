from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from dd_cache.base import BaseCacheAdapter
from dd_cache.models import CacheError, CacheStats
from dd_cache.utils import deserialize, serialize

if TYPE_CHECKING:
    import redis as redis_lib


class RedisCache(BaseCacheAdapter):
    """Redis-backed cache.

    Requires the ``redis`` package (``pip install dd-cache[redis]``).
    Values are serialised with pickle so arbitrary Python objects are supported.
    TTL is delegated to native Redis ``EX`` seconds.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, **kwargs: Any) -> None:
        try:
            import redis
        except ImportError as exc:
            raise CacheError(
                "RedisCache requires the 'redis' package. "
                "Install it with: pip install dd-cache[redis]"
            ) from exc
        self._client: redis_lib.Redis = redis.Redis(host=host, port=port, db=db, **kwargs)

    # ------------------------------------------------------------------
    # BaseCacheAdapter interface
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any:
        data = self._client.get(key)
        if data is None:
            return None
        return deserialize(data)

    def set(self, key: str, value: Any, *, ttl: Optional[int] = None) -> None:
        serialized = serialize(value)
        if ttl is not None:
            self._client.set(key, serialized, ex=ttl)
        else:
            self._client.set(key, serialized)

    def delete(self, key: str) -> bool:
        return bool(self._client.delete(key))

    def exists(self, key: str) -> bool:
        return bool(self._client.exists(key))

    def clear(self) -> None:
        self._client.flushdb()

    def stats(self) -> CacheStats:
        info = self._client.info()
        return CacheStats(
            backend="redis",
            total_keys=self._client.dbsize(),
            ttl_enabled=True,
            extra={
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
            },
        )

    def close(self) -> None:
        self._client.close()
