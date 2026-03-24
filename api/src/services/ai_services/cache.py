"""
Cache management for AI services.

This module provides:
- Provider instance cache (with TTL and max size)
- In-memory response cache (for LLM responses with TTL)

Separated from factory.py to avoid circular imports with ProvidersService.
"""

import json
from hashlib import sha256
from time import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from services.ai_services.interface import AIProviderInterface


# ---------------------------------------------------------------------------
# Provider instance cache (with TTL)
# ---------------------------------------------------------------------------

_PROVIDER_CACHE_TTL = 600  # 10 minutes
_PROVIDER_CACHE_MAX_SIZE = 50

# Cache entries: {system_name: (provider_instance, expires_at)}
_provider_cache: dict[str, tuple["AIProviderInterface", float]] = {}


def invalidate_provider_cache(provider_system_name: str) -> None:
    """
    Invalidate cached provider instance by system_name.

    This should be called when a provider is updated or deleted to ensure
    the next request fetches fresh configuration from the database.

    Args:
        provider_system_name: The system_name of the provider to invalidate
    """
    _provider_cache.pop(provider_system_name, None)


def invalidate_all_provider_cache() -> None:
    """Invalidate all cached provider instances."""
    _provider_cache.clear()


def get_cached_provider(provider_system_name: str) -> "AIProviderInterface | None":
    """
    Get provider from cache if exists and not expired.

    Args:
        provider_system_name: The system_name of the provider

    Returns:
        Cached provider instance or None if not cached / expired
    """
    entry = _provider_cache.get(provider_system_name)
    if entry is None:
        return None
    provider_instance, expires_at = entry
    if time() >= expires_at:
        del _provider_cache[provider_system_name]
        return None
    return provider_instance


def cache_provider(
    provider_system_name: str, provider_instance: "AIProviderInterface"
) -> None:
    """
    Store provider instance in cache with TTL.

    Args:
        provider_system_name: The system_name of the provider
        provider_instance: The provider instance to cache
    """
    # Evict oldest entry if at capacity
    if len(_provider_cache) >= _PROVIDER_CACHE_MAX_SIZE:
        oldest_key = min(_provider_cache, key=lambda k: _provider_cache[k][1])
        del _provider_cache[oldest_key]

    _provider_cache[provider_system_name] = (
        provider_instance,
        time() + _PROVIDER_CACHE_TTL,
    )


# ---------------------------------------------------------------------------
# In-memory response cache (for LLM / embedding responses)
# ---------------------------------------------------------------------------


class ResponseCache:
    """In-memory cache with TTL support for LLM response caching.

    Used by OCI providers (native SDK) and as a shared utility.
    LiteLLM-based providers can also use litellm's built-in cache.
    """

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size

    def make_key(self, **kwargs: Any) -> str:
        """Create a stable cache key from request parameters.

        Uses JSON serialization with sorted keys for deterministic output,
        unlike str() which doesn't guarantee dict key ordering.
        """

        def _serialize(obj: Any) -> Any:
            """Convert obj to a JSON-serializable form."""
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            if isinstance(obj, (list, tuple)):
                return [_serialize(item) for item in obj]
            if isinstance(obj, dict):
                return {str(k): _serialize(v) for k, v in sorted(obj.items())}
            return str(obj)

        serialized = {str(k): _serialize(v) for k, v in sorted(kwargs.items())}
        key_str = json.dumps(serialized, sort_keys=True, ensure_ascii=False)
        return sha256(key_str.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time() < expires_at:
            return value
        del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with TTL."""
        if len(self._cache) >= self._max_size:
            # Remove oldest (by expiry) entry
            oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        expires_at = time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expires_at)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()


# Global response cache instance — shared across all providers
response_cache = ResponseCache()
