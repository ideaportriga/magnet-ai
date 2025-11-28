from typing import Any

from core.config.app import alchemy
from core.domain.providers.service import ProvidersService
from services.ai_services.cache import (
    cache_provider,
    get_cached_provider,
    invalidate_provider_cache,
)
from services.ai_services.interface import AIProviderInterface
from services.ai_services.providers.azure_ai import AzureAIProvider
from services.ai_services.providers.azure_open_ai import AzureProvider
from services.ai_services.providers.groq import GroqProvider
from services.ai_services.providers.tmp_local import TmpLocalProvider
from services.ai_services.providers.oci import OCIProvider
from services.ai_services.providers.oci_llama import OCILlamaProvider
from services.ai_services.providers.openai import OpenAIProvider
from utils.secrets import replace_placeholders_in_dict

# Re-export for backward compatibility
__all__ = ["get_ai_provider", "invalidate_provider_cache"]


def _build_provider_config(provider_data: dict[str, Any]) -> dict[str, Any]:
    """
    Build provider config from database data in the format expected by provider classes.

    Args:
        provider_data: Provider data from database (secrets_encrypted is already decrypted by EncryptedJsonB)

    Returns:
        Config dict with 'connection' and 'defaults' keys
    """
    connection_config = provider_data.get("connection_config", {})
    # secrets_encrypted is already decrypted by EncryptedJsonB when read from database
    secrets = provider_data.get("secrets_encrypted", {})

    # Resolve placeholders like {api_key} in connection_config with actual secret values
    resolved_connection_config = replace_placeholders_in_dict(
        connection_config, secrets
    )

    # Merge resolved connection_config and secrets into 'connection' key
    connection = {**secrets, **resolved_connection_config}

    # Add endpoint if present
    if provider_data.get("endpoint"):
        connection["endpoint"] = provider_data["endpoint"]

    # Extract defaults from metadata_info if present
    metadata_info = provider_data.get("metadata_info") or {}
    defaults = metadata_info.get("defaults", {})

    return {
        "connection": connection,
        "defaults": defaults,
        "type": provider_data.get("type"),
        "label": provider_data.get("name"),
        "otel_gen_ai_system": metadata_info.get("otel_gen_ai_system"),
    }


async def get_ai_provider(provider_system_name: str) -> AIProviderInterface:
    """
    Get AI provider instance by provider_system_name.

    Retrieves provider configuration from database, resolves placeholders
    in connection_config using secrets, and creates/caches provider instance.

    Args:
        provider_system_name: The system_name of the provider from the providers table

    Returns:
        AIProviderInterface instance

    Raises:
        ValueError: If provider not found or type not supported
    """
    # Check cache first
    cached_provider = get_cached_provider(provider_system_name)
    if cached_provider is not None:
        return cached_provider

    # Get provider data from database
    async with alchemy.get_session() as session:
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

    provider_type = provider_data.get("type")
    if not provider_type:
        raise ValueError(f"Provider '{provider_system_name}' has no type specified.")

    # Map provider types to implementation classes
    provider_classes = {
        "openai": OpenAIProvider,
        "azure_ai": AzureAIProvider,
        "azure_open_ai": AzureProvider,
        "oci": OCIProvider,
        "oci_llama": OCILlamaProvider,
        "groq": GroqProvider,
        "datakom": TmpLocalProvider,
    }

    provider_class = provider_classes.get(str(provider_type))
    if not provider_class:
        raise ValueError(
            f"Provider type '{provider_type}' is not implemented. "
            f"Available types: {', '.join(provider_classes.keys())}"
        )

    # Build config in the format expected by provider classes
    provider_config = _build_provider_config(provider_data)

    # Create and cache provider instance
    provider_instance = provider_class(provider_config)
    cache_provider(provider_system_name, provider_instance)

    return provider_instance
