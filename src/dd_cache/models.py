from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CacheStats(BaseModel):
    backend: str        # "memory" | "disk" | "redis"
    total_keys: int
    ttl_enabled: bool
    extra: dict[str, Any] = {}


class CacheError(Exception):
    """Raised for cache configuration or operation errors."""
