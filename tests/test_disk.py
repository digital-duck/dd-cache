import pytest

from dd_cache.adapters.disk import DiskCache
from tests.conftest import CacheContractMixin, assert_ttl_expiry


class TestDiskCache(CacheContractMixin):
    @pytest.fixture(autouse=True)
    def _tmp_db(self, tmp_path):
        self._db_path = tmp_path / "test_cache.db"

    def make_cache(self) -> DiskCache:
        return DiskCache(path=self._db_path)

    def test_ttl_expires(self):
        cache = self.make_cache()
        assert_ttl_expiry(cache, "ttl_key", ttl_seconds=1)

    def test_stats_backend_is_disk(self):
        with self.make_cache() as cache:
            assert cache.stats().backend == "disk"

    def test_stats_extra_has_path(self):
        with self.make_cache() as cache:
            assert "path" in cache.stats().extra

    def test_persists_across_instances(self):
        c1 = DiskCache(path=self._db_path)
        c1.set("pkey", "pval")
        c1.close()

        c2 = DiskCache(path=self._db_path)
        assert c2.get("pkey") == "pval"
        c2.close()

    def test_clear_removes_all(self):
        cache = self.make_cache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.stats().total_keys == 0
        cache.close()
