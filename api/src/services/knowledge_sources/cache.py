"""
Knowledge Source Provider cache management.

This module manages the cache of knowledge source provider configurations.
Similar to AI services cache but for knowledge source providers.
"""

from typing import Any, Dict

# Cache for provider configurations
# Structure: {provider_system_name: resolved_config_dict}
_provider_config_cache: Dict[str, Dict[str, Any]] = {}


def invalidate_provider_config_cache(provider_system_name: str) -> None:
    """
    Invalidate cached provider configuration by system_name.

    This should be called when a provider is updated or deleted to ensure
    the next request fetches fresh configuration from the database.

    Args:
        provider_system_name: The system_name of the provider to invalidate
    """
    if provider_system_name in _provider_config_cache:
        del _provider_config_cache[provider_system_name]


def get_cached_provider_config(provider_system_name: str) -> Dict[str, Any] | None:
    """
    Get provider configuration from cache if exists.

    Args:
        provider_system_name: The system_name of the provider

    Returns:
        Cached provider configuration dict or None if not cached
    """
    return _provider_config_cache.get(provider_system_name)


def cache_provider_config(provider_system_name: str, config: Dict[str, Any]) -> None:
    """
    Store provider configuration in cache.

    Args:
        provider_system_name: The system_name of the provider
        config: The resolved configuration dictionary to cache
    """
    _provider_config_cache[provider_system_name] = config
