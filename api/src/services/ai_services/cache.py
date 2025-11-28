"""
Provider cache management.

This module manages the cache of AI provider instances.
It is separated from factory.py to avoid circular imports with ProvidersService.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.ai_services.interface import AIProviderInterface

# Cache for provider instances
_provider_cache: dict[str, "AIProviderInterface"] = {}


def invalidate_provider_cache(provider_system_name: str) -> None:
    """
    Invalidate cached provider instance by system_name.

    This should be called when a provider is updated or deleted to ensure
    the next request fetches fresh configuration from the database.

    Args:
        provider_system_name: The system_name of the provider to invalidate
    """
    if provider_system_name in _provider_cache:
        del _provider_cache[provider_system_name]


def get_cached_provider(provider_system_name: str) -> "AIProviderInterface | None":
    """
    Get provider from cache if exists.

    Args:
        provider_system_name: The system_name of the provider

    Returns:
        Cached provider instance or None if not cached
    """
    return _provider_cache.get(provider_system_name)


def cache_provider(
    provider_system_name: str, provider_instance: "AIProviderInterface"
) -> None:
    """
    Store provider instance in cache.

    Args:
        provider_system_name: The system_name of the provider
        provider_instance: The provider instance to cache
    """
    _provider_cache[provider_system_name] = provider_instance
