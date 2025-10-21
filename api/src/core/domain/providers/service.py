from __future__ import annotations

from typing import Any

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.provider import Provider
from services.ai_services.cache import invalidate_provider_cache
from services.knowledge_sources.cache import (
    invalidate_provider_config_cache as invalidate_ks_provider_cache,
)


class ProvidersService(service.SQLAlchemyAsyncRepositoryService[Provider]):
    """Providers service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Provider]):
        """Providers repository."""

        model_type = Provider

    repository_type = Repo

    async def create(
        self,
        data: Provider | dict[str, Any],
        **kwargs: Any,
    ) -> Provider:
        """
        Create a new provider and invalidate cache.
        """
        # Call parent create method
        created_provider = await super().create(data, **kwargs)
        
        # Invalidate provider cache after successful creation
        # This ensures any cached lookups will fetch fresh data
        invalidate_provider_cache(created_provider.system_name)
        # Also invalidate knowledge source provider cache
        invalidate_ks_provider_cache(created_provider.system_name)
        
        return created_provider

    async def update(
        self,
        data: Provider | dict[str, Any],
        item_id: Any | None = None,
        **kwargs: Any,
    ) -> Provider:
        """
        Update a provider.

        If the endpoint is changed, clear the secrets_encrypted field.
        For secrets_encrypted field, only update keys with non-empty values,
        preserving existing secrets when empty strings are provided.
        """
        # Get the current provider to check if endpoint changed
        if item_id is not None:
            existing_provider = await self.get(item_id)
            
            # Extract endpoint from update data
            new_endpoint = None
            if isinstance(data, dict):
                new_endpoint = data.get("endpoint")
            else:
                new_endpoint = getattr(data, "endpoint", None)
            
            # If endpoint is being changed and is different from current, clear secrets
            if new_endpoint is not None and existing_provider.endpoint != new_endpoint:
                if isinstance(data, dict):
                    data["secrets_encrypted"] = None
                else:
                    data.secrets_encrypted = None
            else:
                # Handle secrets_encrypted field - merge with existing secrets
                # Only update secrets that have non-empty values
                if isinstance(data, dict):
                    new_secrets = data.get("secrets_encrypted")
                else:
                    new_secrets = getattr(data, "secrets_encrypted", None)
                
                if new_secrets is not None:
                    # Get existing secrets
                    existing_secrets = existing_provider.secrets_encrypted or {}
                    
                    # Merge: keep existing secrets, only update non-empty values
                    merged_secrets = existing_secrets.copy()
                    for key, value in new_secrets.items():
                        if value and value.strip():  # Only update if value is non-empty
                            merged_secrets[key] = value
                        # If value is empty/None, keep the existing value (don't delete)
                    
                    # Update data with merged secrets
                    if isinstance(data, dict):
                        data["secrets_encrypted"] = merged_secrets
                    else:
                        data.secrets_encrypted = merged_secrets
        
        # Call parent update method
        updated_provider = await super().update(data, item_id=item_id, **kwargs)
        
        # Invalidate provider cache after successful update
        invalidate_provider_cache(updated_provider.system_name)
        # Also invalidate knowledge source provider cache
        invalidate_ks_provider_cache(updated_provider.system_name)
        
        return updated_provider

