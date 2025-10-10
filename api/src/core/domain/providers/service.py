from __future__ import annotations

from typing import Any

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.provider import Provider


class ProvidersService(service.SQLAlchemyAsyncRepositoryService[Provider]):
    """Providers service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Provider]):
        """Providers repository."""

        model_type = Provider

    repository_type = Repo

    async def update(
        self,
        data: Provider | dict[str, Any],
        item_id: Any | None = None,
        **kwargs: Any,
    ) -> Provider:
        """
        Update a provider.

        If the endpoint is changed, clear the secrets_encrypted field.
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
        
        # Call parent update method
        return await super().update(data, item_id=item_id, **kwargs)
