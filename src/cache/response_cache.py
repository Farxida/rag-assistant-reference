import hashlib
import time
from collections import OrderedDict


class ResponseCache:
    def __init__(self, ttl_seconds: int = 600, max_entries: int = 256):
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._store: OrderedDict[str, tuple[float, dict]] = OrderedDict()

    @staticmethod
    def _key(query: str, tenant_id: str) -> str:
        return hashlib.sha256(f"{tenant_id}::{query}".encode()).hexdigest()[:24]

    def get(self, query: str, tenant_id: str):
        key = self._key(query, tenant_id)
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.time() - ts > self.ttl:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    def set(self, query: str, tenant_id: str, value: dict):
        key = self._key(query, tenant_id)
        self._store[key] = (time.time(), value)
        self._store.move_to_end(key)
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    def size(self) -> int:
        return len(self._store)

    def clear(self):
        self._store.clear()


default_cache = ResponseCache()
