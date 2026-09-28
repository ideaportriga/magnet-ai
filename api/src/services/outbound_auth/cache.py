from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

T = TypeVar("T")

_MAX_CACHE_ENTRIES = 512


@dataclass(frozen=True, slots=True)
class _CacheEntry(Generic[T]):
    """Store a cached value together with its monotonic expiration time."""

    value: T
    expires_at: float


_entries: OrderedDict[str, _CacheEntry[Any]] = OrderedDict()
_locks: dict[str, asyncio.Lock] = {}


def get_cached_value(
    cache_key: str,
    *,
    skew_seconds: float = 0,
) -> T | None:
    """Return a cached value if it remains valid beyond the configured skew."""
    entry = _entries.get(cache_key)

    if entry is None:
        return None

    if entry.expires_at - skew_seconds <= time.monotonic():
        _entries.pop(cache_key, None)
        return None

    _entries.move_to_end(cache_key)

    return cast(T, entry.value)


def cache_value(
    cache_key: str,
    value: T,
    *,
    ttl_seconds: float,
) -> None:
    """Store a value in the cache for the provided time-to-live."""
    if ttl_seconds <= 0:
        return

    _entries[cache_key] = _CacheEntry(
        value=value,
        expires_at=time.monotonic() + ttl_seconds,
    )

    _entries.move_to_end(cache_key)

    while len(_entries) > _MAX_CACHE_ENTRIES:
        _entries.popitem(last=False)


def get_cache_lock(
    cache_key: str,
) -> asyncio.Lock:
    """Return the lock associated with a cache key, creating it if necessary."""
    lock = _locks.get(cache_key)

    if lock is None:
        lock = asyncio.Lock()
        _locks[cache_key] = lock

    return lock


def clear_cache() -> None:
    """Clear all process-local cached values and cache locks."""
    _entries.clear()
    _locks.clear()
