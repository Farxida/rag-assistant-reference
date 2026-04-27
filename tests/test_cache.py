import time

from src.cache.response_cache import ResponseCache


def test_cache_miss_returns_none():
    c = ResponseCache()
    assert c.get("any query", "tenant-a") is None


def test_cache_hit_returns_stored_value():
    c = ResponseCache()
    c.set("hello", "tenant-a", {"answer": "world"})
    assert c.get("hello", "tenant-a") == {"answer": "world"}


def test_cache_isolated_by_tenant():
    c = ResponseCache()
    c.set("hello", "tenant-a", {"answer": "A"})
    assert c.get("hello", "tenant-b") is None
    assert c.get("hello", "tenant-a") == {"answer": "A"}


def test_cache_expires_after_ttl():
    c = ResponseCache(ttl_seconds=0)
    c.set("hello", "tenant-a", {"answer": "world"})
    time.sleep(0.01)
    assert c.get("hello", "tenant-a") is None


def test_cache_evicts_oldest_when_full():
    c = ResponseCache(max_entries=2)
    c.set("q1", "t", {"a": 1})
    c.set("q2", "t", {"a": 2})
    c.set("q3", "t", {"a": 3})
    assert c.get("q1", "t") is None
    assert c.get("q2", "t") == {"a": 2}
    assert c.get("q3", "t") == {"a": 3}


def test_cache_clear():
    c = ResponseCache()
    c.set("q", "t", {"a": 1})
    c.clear()
    assert c.size() == 0
