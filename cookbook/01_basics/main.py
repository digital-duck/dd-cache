"""dd-cache basics cookbook: demonstrates InMemoryCache, DiskCache, and shared patterns."""
import time
from pathlib import Path

from dd_cache import DiskCache, InMemoryCache
from dd_cache.utils import make_key

DISK_PATH = Path("/tmp/dd_cache_demo.db")

# ------------------------------------------------------------------
# 1. InMemoryCache — zero-dependency, process-lifetime storage
# ------------------------------------------------------------------
print("=== InMemoryCache ===")
with InMemoryCache() as mem:
    mem.set("greeting", "hello, world")
    print("get:", mem.get("greeting"))                    # hello, world
    print("exists:", mem.exists("greeting"))              # True
    print("miss:", mem.get("not_there"))                  # None

    # TTL: value disappears after 1 second
    mem.set("ephemeral", "blink", ttl=1)
    print("before TTL:", mem.get("ephemeral"))            # blink
    time.sleep(1.1)
    print("after TTL:", mem.get("ephemeral"))             # None

    # get_or_set: cache expensive computation
    call_count = [0]
    def expensive():
        call_count[0] += 1
        return sum(range(1_000_000))

    key = make_key("results", "sum_1M")
    r1 = mem.get_or_set(key, expensive)
    r2 = mem.get_or_set(key, expensive)   # fn not called again
    print(f"result: {r1}, fn called {call_count[0]} time(s)")  # 1 time

    print("stats:", mem.stats())

# ------------------------------------------------------------------
# 2. DiskCache — SQLite-backed, survives process restarts
# ------------------------------------------------------------------
print("\n=== DiskCache ===")

DISK_PATH.unlink(missing_ok=True)  # clean demo run

with DiskCache(DISK_PATH) as disk:
    disk.set("user:42", {"name": "Alice", "score": 99})
    user = disk.get("user:42")
    print("user:", user)

    # Overwrite
    disk.set("user:42", {"name": "Alice", "score": 100})
    print("updated score:", disk.get("user:42")["score"])

    # Delete
    deleted = disk.delete("user:42")
    print("deleted:", deleted)            # True
    print("after delete:", disk.get("user:42"))  # None

    print("stats:", disk.stats())

print("\nAll cookbook examples ran successfully.")
