import time

import pytest

from dd_cache.adapters.memory import InMemoryCache
from tests.conftest import CacheContractMixin, assert_ttl_expiry


class TestInMemoryCache(CacheContractMixin):
    def make_cache(self) -> InMemoryCache:
        return InMemoryCache()

    def test_ttl_expires(self):
        cache = self.make_cache()
        assert_ttl_expiry(cache, "ttl_key", ttl_seconds=1)

    def test_ttl_not_expired_yet(self):
        cache = self.make_cache()
        cache.set("alive", "yes", ttl=60)
        assert cache.get("alive") == "yes"
        assert cache.exists("alive") is True
        cache.close()

    def test_no_ttl_persists(self):
        cache = self.make_cache()
        cache.set("persist", "forever")
        time.sleep(0.05)
        assert cache.get("persist") == "forever"
        cache.close()

    def test_stats_counts_live_keys_only(self):
        cache = self.make_cache()
        cache.set("live", "v")
        cache.set("dead", "v", ttl=1)
        time.sleep(1.1)
        s = cache.stats()
        assert s.total_keys == 1
        cache.close()

    def test_stats_backend_is_memory(self):
        cache = self.make_cache()
        assert cache.stats().backend == "memory"
        cache.close()
