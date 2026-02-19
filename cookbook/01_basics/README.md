# dd-cache Basics

Demonstrates the core `dd-cache` API using `InMemoryCache` and `DiskCache`.

## Run

```bash
cd ~/projects/digital-duck/dd-cache
pip install -e .
python cookbook/01_basics/main.py
```

## What it covers

- `InMemoryCache`: set/get/exists/delete, TTL, `get_or_set`, stats
- `DiskCache`: SQLite-backed persistence, survives process restarts
- `make_key()` utility for namespaced cache keys
- Context-manager usage (`with cache:`)
