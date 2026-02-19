# dd-cache Design

## Motivation

Three packages in the dd-* ecosystem needed caching but solved it independently:

| Package   | Ad-hoc solution                         | Limitation                          |
|-----------|-----------------------------------------|-------------------------------------|
| dd-embed  | `EmbeddingCache` (pickle/numpy)         | No TTL, no backend choice           |
| dd-llm    | None                                    | Expensive API calls repeated        |
| spl       | None                                    | Query results not cached            |

`dd-cache` provides a single, backend-swappable KV cache following the same adapter
pattern used by `dd-db` and `dd-vectordb`.

---

## Architecture

```
BaseCacheAdapter (ABC)
├── InMemoryCache   — dict + TTL, stdlib only, process lifetime
├── DiskCache       — SQLite BLOB store, stdlib only, persistent
└── RedisCache      — Redis via redis-py, optional dependency
```

All adapters implement the same interface:

```
get(key)           → Any | None
set(key, value, *, ttl=None)
delete(key)        → bool
exists(key)        → bool
clear()
stats()            → CacheStats
close()
```

Plus the concrete helper `get_or_set(key, fn, *, ttl)` and context-manager support.

---

## TTL handling

| Adapter   | Strategy                                                        |
|-----------|-----------------------------------------------------------------|
| Memory    | Lazy eviction: `_expiry` dict compared against `time.time()`   |
| Disk      | SQLite `expires_at REAL` column; evicted on read                |
| Redis     | Native `SET … EX <seconds>`; handled server-side               |

---

## Serialisation

`InMemoryCache` stores Python objects in-process (no serialisation needed).
`DiskCache` and `RedisCache` use `pickle.dumps` / `pickle.loads` via `dd_cache.utils`.
This supports arbitrary Python objects at the cost of cross-language compatibility.

---

## Extending

Add a new backend by subclassing `BaseCacheAdapter` and implementing all abstract
methods.  No registration step is required — import and use directly.

```python
from dd_cache.base import BaseCacheAdapter

class MyCache(BaseCacheAdapter):
    ...
```

---

## Why not `cachetools` / `dogpile.cache` / `diskcache`?

- **Minimal surface area**: dd-cache exposes only what the dd-* ecosystem needs.
- **Consistent adapter pattern**: mirrors `dd-db` and `dd-vectordb` for uniform DX.
- **Zero mandatory dependencies** for the two most common backends (memory + disk).
- Easy to replace if a heavier solution is needed later — same interface.
