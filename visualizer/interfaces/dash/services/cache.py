from __future__ import annotations
import time
from typing import Any, Callable, Optional, Tuple

class MemoryCache:
    def __init__(self):
        self._data: dict[Tuple[str, str], tuple[float, Any, Optional[float]]] = {}

    def get(self, ns: str, key: str) -> Any | None:
        k = (ns, key)
        if k not in self._data:
            return None
        ts, value, ttl = self._data[k]
        if ttl is not None and (time.time() - ts) > ttl:
            self._data.pop(k, None)
            return None
        return value

    def set(self, ns: str, key: str, value: Any, ttl: Optional[float] = None) -> None:
        self._data[(ns, key)] = (time.time(), value, ttl)

    def invalidate(self, ns: str, key: Optional[str] = None) -> None:
        if key is None:
            # invalidar todo el namespace
            to_del = [k for k in self._data if k[0] == ns]
            for k in to_del:
                self._data.pop(k, None)
        else:
            self._data.pop((ns, key), None)

# decorador simple
def cached(ns: str, key_builder: Callable[..., str], ttl: Optional[float] = 30.0):
    cache = MemoryCache()

    def _outer(fn: Callable[..., Any]):
        def _inner(*args, **kwargs):
            key = key_builder(*args, **kwargs)
            val = cache.get(ns, key)
            if val is not None:
                return val
            res = fn(*args, **kwargs)
            cache.set(ns, key, res, ttl=ttl)
            return res
        return _inner
    return _outer
