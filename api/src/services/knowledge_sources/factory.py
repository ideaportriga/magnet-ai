"""
Knowledge Source Provider Configuration Factory.

This module provides functions to retrieve and build provider configurations
for knowledge source plugins.
"""
from typing import Any, Dict

from core.config.app import alchemy
from services.knowledge_sources.cache import (
    cache_provider_config,
    get_cached_provider_config,
    invalidate_provider_config_cache,
)
from utils.secrets import replace_placeholders_in_dict

# Re-export for convenience
__all__ = ["get_provider_config", "invalidate_provider_config_cache"]


def _build_provider_config(provider_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build provider config from database data.
    
    Resolves placeholders in connection_config using secrets_encrypted values.
    
    Args:
        provider_data: Provider data from database (secrets_encrypted is already decrypted by EncryptedJsonB)
        
    Returns:
        Resolved config dict with all placeholders replaced
    """
    connection_config = provider_data.get("connection_config", {})
    # secrets_encrypted is already decrypted by EncryptedJsonB when read from database
    secrets = provider_data.get("secrets_encrypted", {})
    
    # Resolve placeholders like {api_key} in connection_config with actual secret values
    resolved_connection_config = replace_placeholders_in_dict(connection_config, secrets)
    
    # Merge resolved connection_config and secrets
    resolved_config = {**secrets, **resolved_connection_config}
    
    # Add endpoint if present
    if provider_data.get("endpoint"):
        resolved_config["endpoint"] = provider_data["endpoint"]
    
    return resolved_config


async def get_provider_config(provider_system_name: str) -> Dict[str, Any]:
    """
    Get knowledge source provider configuration by provider_system_name.
    
    Retrieves provider configuration from database, resolves placeholders 
    in connection_config using secrets, and caches the result.
    
    This function returns a dictionary with resolved configuration values
    that can be merged with source_config before passing to plugins.
    
    Args:
        provider_system_name: The system_name of the provider from the providers table
        
    Returns:
        Dictionary with resolved configuration (endpoint, connection params, secrets)
        
    Raises:
        ValueError: If provider not found
        
    Example:
        >>> provider_config = await get_provider_config("SHAREPOINT_MAIN")
        >>> # provider_config will contain: {"endpoint": "...", "client_id": "...", ...}
        >>> # Merge with source config
        >>> merged_config = {**provider_config, **source_config}
    """
    # Check cache first
    cached_config = get_cached_provider_config(provider_system_name)
    if cached_config is not None:
        return cached_config

    # Get provider data from database
    async with alchemy.get_session() as session:
        # Import here to avoid circular import
        from core.domain.providers.service import ProvidersService
        
        providers_service = ProvidersService(session=session)
        provider = await providers_service.get_one(system_name=provider_system_name)
        
        if not provider:
            raise ValueError(f"Provider '{provider_system_name}' is not found in database.")

        # Convert to dict for easier handling
        # EncryptedJsonB automatically decrypts secrets_encrypted field
        provider_data = {
            "system_name": provider.system_name,
            "name": provider.name,
            "type": provider.type,
            "endpoint": provider.endpoint,
            "connection_config": provider.connection_config or {},
            "secrets_encrypted": provider.secrets_encrypted or {},
            "metadata_info": provider.metadata_info or {},
        }

    # Build resolved configuration
    resolved_config = _build_provider_config(provider_data)
    
    # Cache the configuration
    cache_provider_config(provider_system_name, resolved_config)
    
    return resolved_config
