"""Shared fixtures and an abstract contract mixin for testing cache adapters."""
from __future__ import annotations

import time

import pytest

from dd_cache.base import BaseCacheAdapter


class CacheContractMixin:
    """Mix into a test class to exercise the full BaseCacheAdapter contract.

    Subclasses must implement ``make_cache()`` returning a fresh adapter.
    """

    def make_cache(self) -> BaseCacheAdapter:  # pragma: no cover
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Contract tests
    # ------------------------------------------------------------------

    def test_set_and_get(self):
        cache = self.make_cache()
        cache.set("k", "hello")
        assert cache.get("k") == "hello"
        cache.close()

    def test_miss_returns_none(self):
        cache = self.make_cache()
        assert cache.get("nonexistent") is None
        cache.close()

    def test_exists_true_after_set(self):
        cache = self.make_cache()
        cache.set("x", 42)
        assert cache.exists("x") is True
        cache.close()

    def test_exists_false_on_miss(self):
        cache = self.make_cache()
        assert cache.exists("missing") is False
        cache.close()

    def test_delete_returns_true_when_existed(self):
        cache = self.make_cache()
        cache.set("d", "v")
        assert cache.delete("d") is True
        cache.close()

    def test_delete_returns_false_when_missing(self):
        cache = self.make_cache()
        assert cache.delete("ghost") is False
        cache.close()

    def test_delete_removes_key(self):
        cache = self.make_cache()
        cache.set("rem", "val")
        cache.delete("rem")
        assert cache.get("rem") is None
        cache.close()

    def test_clear_removes_all(self):
        cache = self.make_cache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
        cache.close()

    def test_stats_backend_name(self):
        cache = self.make_cache()
        s = cache.stats()
        assert isinstance(s.backend, str)
        assert len(s.backend) > 0
        cache.close()

    def test_stats_total_keys(self):
        cache = self.make_cache()
        cache.set("p", "q")
        cache.set("r", "s")
        s = cache.stats()
        assert s.total_keys >= 2
        cache.close()

    def test_get_or_set_miss_calls_fn(self):
        cache = self.make_cache()
        called = []

        def fn():
            called.append(True)
            return "computed"

        result = cache.get_or_set("lazy", fn)
        assert result == "computed"
        assert called == [True]
        cache.close()

    def test_get_or_set_hit_skips_fn(self):
        cache = self.make_cache()
        cache.set("eager", "cached")
        calls = []
        result = cache.get_or_set("eager", lambda: calls.append(1) or "new")
        assert result == "cached"
        assert calls == []
        cache.close()

    def test_get_or_set_stores_none_value(self):
        """None is a valid cached value; get_or_set must not re-call fn."""
        cache = self.make_cache()
        cache.set("null_val", None)
        calls = []
        result = cache.get_or_set("null_val", lambda: calls.append(1) or "x")
        assert result is None
        assert calls == []
        cache.close()

    def test_context_manager_calls_close(self):
        cache = self.make_cache()
        with cache:
            cache.set("cm", True)
        # After __exit__ the cache object should still be usable for stats
        # but we mainly verify no exception was raised.

    def test_overwrite_value(self):
        cache = self.make_cache()
        cache.set("ov", "first")
        cache.set("ov", "second")
        assert cache.get("ov") == "second"
        cache.close()

    def test_complex_value(self):
        cache = self.make_cache()
        val = {"list": [1, 2, 3], "nested": {"ok": True}}
        cache.set("complex", val)
        assert cache.get("complex") == val
        cache.close()


# ------------------------------------------------------------------
# TTL helpers used by concrete test files
# ------------------------------------------------------------------

def assert_ttl_expiry(cache: BaseCacheAdapter, key: str, ttl_seconds: int = 1) -> None:
    """Set a value with TTL, sleep, assert it disappeared."""
    cache.set(key, "ttl_val", ttl=ttl_seconds)
    assert cache.get(key) == "ttl_val"
    time.sleep(ttl_seconds + 0.1)
    assert cache.get(key) is None
    assert cache.exists(key) is False
