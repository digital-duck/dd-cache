"""Redis cache tests — skipped automatically if redis is not installed or not running."""
import pytest

redis = pytest.importorskip("redis", reason="redis package not installed")

from dd_cache.adapters.redis_adapter import RedisCache  # noqa: E402
from tests.conftest import CacheContractMixin, assert_ttl_expiry  # noqa: E402


def _redis_available() -> bool:
    try:
        import redis as r
        client = r.Redis()
        client.ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _redis_available(),
    reason="Redis server not reachable on localhost:6379",
)


@pytest.fixture()
def redis_cache():
    cache = RedisCache()
    cache.clear()  # start clean
    yield cache
    cache.clear()
    cache.close()


class TestRedisCache(CacheContractMixin):
    @pytest.fixture(autouse=True)
    def _setup(self, redis_cache):
        self._cache = redis_cache

    def make_cache(self) -> RedisCache:
        self._cache.clear()
        return self._cache

    def test_ttl_expires(self):
        assert_ttl_expiry(self._cache, "redis_ttl", ttl_seconds=1)

    def test_stats_backend_is_redis(self):
        assert self._cache.stats().backend == "redis"

    def test_stats_extra_has_version(self):
        extra = self._cache.stats().extra
        assert "redis_version" in extra

    def test_import_error_without_redis(self, monkeypatch):
        """Verify helpful CacheError is raised when redis is not importable."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "redis":
                raise ImportError("mocked missing redis")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        from dd_cache.models import CacheError
        with pytest.raises(CacheError, match="redis"):
            RedisCache()
