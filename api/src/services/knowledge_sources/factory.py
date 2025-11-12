"""
Knowledge Source Provider Configuration Factory.

This module provides functions to retrieve and build provider configurations
for knowledge source plugins.
"""

from typing import Any, Dict
import structlog

from core.config.app import alchemy
from services.knowledge_sources.cache import (
    cache_provider_config,
    get_cached_provider_config,
    invalidate_provider_config_cache,
)
from utils.secrets import replace_placeholders_in_dict

# Re-export for convenience
__all__ = ["get_provider_config", "invalidate_provider_config_cache"]

logger = structlog.get_logger(__name__)


def _build_provider_config(provider_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build provider config from database data.

    Resolves placeholders in connection_config using secrets_encrypted values.

    SECURITY NOTE: This function returns security-critical configuration including
    endpoint URLs and authentication credentials. These values should be treated as
    immutable and never overridden by user-controlled configuration to prevent
    credential leakage or unauthorized access.

    Args:
        provider_data: Provider data from database (secrets_encrypted is already decrypted by EncryptedJsonB)

    Returns:
        Resolved config dict with all placeholders replaced. Contains security-critical
        fields that must not be overridden by knowledge source configuration.
    """
    connection_config = provider_data.get("connection_config", {})
    # secrets_encrypted is already decrypted by EncryptedJsonB when read from database
    secrets = provider_data.get("secrets_encrypted", {})

    # Resolve placeholders like {api_key} in connection_config with actual secret values
    resolved_connection_config = replace_placeholders_in_dict(
        connection_config, secrets
    )

    # Merge resolved connection_config and secrets
    resolved_config = {**secrets, **resolved_connection_config}

    # Always add endpoint (even if None/empty) for clarity in debugging
    endpoint = provider_data.get("endpoint")
    resolved_config["endpoint"] = endpoint

    logger.debug(
        "Built provider config",
        provider_system_name=provider_data.get("system_name"),
        has_endpoint=bool(endpoint),
        endpoint_value=endpoint if endpoint else "None/Empty",
        config_keys=list(resolved_config.keys()),
    )

    return resolved_config


async def get_provider_config(provider_system_name: str) -> Dict[str, Any]:
    """
    Get knowledge source provider configuration by provider_system_name.

    Retrieves provider configuration from database, resolves placeholders
    in connection_config using secrets, and caches the result.

    This function returns a dictionary with security-critical configuration values
    (endpoint, credentials, secrets) that should NOT be overridden by source_config.

    SECURITY NOTE: The returned configuration contains sensitive fields (endpoint,
    credentials, tokens, keys) that are tied to authentication. These fields should
    NEVER be overridable from user-controlled source configuration to prevent
    unauthorized access or credential leakage to unintended endpoints.

    Args:
        provider_system_name: The system_name of the provider from the providers table

    Returns:
        Dictionary with resolved configuration (endpoint, connection params, secrets).
        All security-critical fields in this dict should be treated as immutable
        and not overridden by knowledge source configuration.

    Raises:
        ValueError: If provider not found

    Example:
        >>> provider_config = await get_provider_config("SHAREPOINT_MAIN")
        >>> # provider_config contains: {"endpoint": "...", "client_id": "...", ...}
        >>> # When merging, security-critical fields must NOT be overridden:
        >>> merged_config = {**provider_config}
        >>> for key, value in source_config.items():
        >>>     if key not in SECURITY_CRITICAL_FIELDS:
        >>>         merged_config[key] = value
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
            raise ValueError(
                f"Provider '{provider_system_name}' is not found in database."
            )

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
