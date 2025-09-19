from __future__ import annotations

from typing import Any

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.mcp_server.mcp_server import MCPServer

from .schemas import MCPServer as MCPServerSchema
from .schemas import MCPServerUpdate


class MCPServersService(service.SQLAlchemyAsyncRepositoryService[MCPServer]):
    """MCP servers service."""

    class Repo(repository.SQLAlchemyAsyncRepository[MCPServer]):
        """MCP servers repository."""

        model_type = MCPServer

    repository_type = Repo

    async def update(
        self, data: MCPServerUpdate, item_id: Any, auto_commit: bool = False, **kwargs
    ) -> MCPServer:
        """
        Update MCP server with special logic for secrets_encrypted.

        For secrets_encrypted field:
        - If key comes with value - update it
        - If key comes with empty/null value - keep existing value
        - If key is not present in request - delete it from secrets
        """
        update_data = data.model_dump(exclude_unset=True)

        # Special handling for secrets_encrypted
        if "secrets_encrypted" in update_data:
            # Get current object to access existing secrets
            current_obj = await self.get(item_id)
            existing_secrets = current_obj.secrets_encrypted or {}

            new_secrets_data = update_data["secrets_encrypted"]

            if isinstance(new_secrets_data, dict) and isinstance(
                existing_secrets, dict
            ):
                # Start with empty dict - only keys from request will remain
                updated_secrets = {}

                for key, value in new_secrets_data.items():
                    if value is not None and value != "":
                        # Key has value - update it
                        updated_secrets[key] = value
                    else:
                        # Key has empty/null value - keep existing if exists
                        if key in existing_secrets:
                            updated_secrets[key] = existing_secrets[key]
                        # If key doesn't exist in existing secrets, don't add it

                # Keys not present in the request are automatically deleted
                # because we only add keys that are in new_secrets_data

                update_data["secrets_encrypted"] = updated_secrets

        # Use parent's update method with processed data
        return await super().update(
            update_data, item_id=item_id, auto_commit=auto_commit, **kwargs
        )

    async def get_with_secrets(self, item_id: Any) -> MCPServerSchema:
        """
        Get MCP server with full secrets for internal service operations.

        WARNING: This method returns sensitive data and should only be used
        in secure internal contexts, never for API responses.
        """
        obj = await self.get(item_id)
        return MCPServerSchema.model_validate(obj, from_attributes=True)

    async def get_with_secrets_by_system_name(
        self, system_name: str
    ) -> MCPServerSchema:
        """
        Get MCP server by system_name with full secrets for internal service operations.

        WARNING: This method returns sensitive data and should only be used
        in secure internal contexts, never for API responses.
        """
        obj = await self.get_one(system_name=system_name)
        return MCPServerSchema.model_validate(obj, from_attributes=True)

    async def list_with_secrets(self, *filters) -> list[MCPServerSchema]:
        """
        List MCP servers with full secrets for internal service operations.

        WARNING: This method returns sensitive data and should only be used
        in secure internal contexts, never for API responses.
        """
        results, _ = await self.list_and_count(*filters)
        return [
            MCPServerSchema.model_validate(obj, from_attributes=True) for obj in results
        ]
