# dd-cache

Backend-swappable caching layer for the dd-* ecosystem.

## Install

```bash
pip install -e .           # core (memory + disk)
pip install -e ".[redis]"  # add Redis support
pip install -e ".[dev]"    # + pytest
```

## Quick start

```python
from dd_cache import InMemoryCache, DiskCache

# In-process, TTL-aware
with InMemoryCache() as cache:
    cache.set("key", {"data": 42}, ttl=60)
    value = cache.get("key")

# Persistent SQLite
with DiskCache(".cache/myapp.db") as cache:
    result = cache.get_or_set("expensive_key", lambda: run_expensive_query())
```

## Adapters

| Class           | Backend   | Persistence | TTL     | Extra deps |
|-----------------|-----------|-------------|---------|------------|
| `InMemoryCache` | dict      | process     | lazy    | none       |
| `DiskCache`     | SQLite    | file        | lazy    | none       |
| `RedisCache`    | Redis     | server      | native  | `redis`    |

## API

```python
cache.get(key)                    # → Any | None
cache.set(key, value, ttl=None)   # ttl in seconds
cache.delete(key)                 # → bool
cache.exists(key)                 # → bool
cache.clear()
cache.stats()                     # → CacheStats
cache.get_or_set(key, fn, ttl=None)
```

See `docs/DESIGN.md` for architecture details.
