from __future__ import annotations

import pytest

from services.outbound_auth import cache


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    cache.clear_cache()


def test_cache_value_returns_unexpired_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = 1_000.0
    monkeypatch.setattr(cache.time, "monotonic", lambda: now)

    cache.cache_value("key", "value", ttl_seconds=120)

    assert cache.get_cached_value("key") == "value"


def test_cache_value_returns_none_after_expiration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [1_000.0]
    monkeypatch.setattr(cache.time, "monotonic", lambda: now[0])
    cache.cache_value("key", "value", ttl_seconds=120)

    now[0] = 1_120.0

    assert cache.get_cached_value("key") is None


def test_cache_value_applies_expiry_skew(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [1_000.0]
    monkeypatch.setattr(cache.time, "monotonic", lambda: now[0])
    cache.cache_value("key", "value", ttl_seconds=120)

    now[0] = 1_061.0

    assert cache.get_cached_value("key", skew_seconds=60) is None


@pytest.mark.parametrize("ttl_seconds", [0, -1])
def test_cache_does_not_store_non_positive_ttl(ttl_seconds: float) -> None:
    cache.cache_value("key", "value", ttl_seconds=ttl_seconds)

    assert cache.get_cached_value("key") is None


def test_cache_evicts_least_recently_used_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cache, "_MAX_CACHE_ENTRIES", 2)

    cache.cache_value("first", 1, ttl_seconds=60)
    cache.cache_value("second", 2, ttl_seconds=60)

    # Reading first makes second the least recently used entry.
    assert cache.get_cached_value("first") == 1
    cache.cache_value("third", 3, ttl_seconds=60)

    assert cache.get_cached_value("first") == 1
    assert cache.get_cached_value("second") is None
    assert cache.get_cached_value("third") == 3


def test_get_cache_lock_reuses_lock_for_same_key() -> None:
    assert cache.get_cache_lock("same") is cache.get_cache_lock("same")
    assert cache.get_cache_lock("same") is not cache.get_cache_lock("other")


def test_clear_cache_removes_values_and_locks() -> None:
    cache.cache_value("key", "value", ttl_seconds=60)
    previous_lock = cache.get_cache_lock("key")

    cache.clear_cache()

    assert cache.get_cached_value("key") is None
    assert cache.get_cache_lock("key") is not previous_lock
