"""dd-cache: backend-swappable caching layer for the dd-* ecosystem."""

from dd_cache.adapters.disk import DiskCache
from dd_cache.adapters.memory import InMemoryCache
from dd_cache.adapters.redis_adapter import RedisCache
from dd_cache.base import BaseCacheAdapter
from dd_cache.models import CacheError, CacheStats

__all__ = [
    "BaseCacheAdapter",
    "CacheError",
    "CacheStats",
    "InMemoryCache",
    "DiskCache",
    "RedisCache",
]
