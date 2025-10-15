from __future__ import annotations

from typing import Any

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.ai_model import AIModel

from .schemas import AIModelUpdate


class AIModelsService(service.SQLAlchemyAsyncRepositoryService[AIModel]):
    """AI Models service."""

    class Repo(repository.SQLAlchemyAsyncRepository[AIModel]):
        """AI Models repository."""

        model_type = AIModel

    repository_type = Repo

    async def update(
        self, data: AIModelUpdate, item_id: Any, auto_commit: bool = False, **kwargs
    ) -> AIModel:
        """
        Update AI model.
        
        Uses exclude_unset=True to only update fields that were explicitly set in the request,
        preventing unintentional clearing of optional fields like provider_system_name.
        """
        # Use exclude_unset to only include fields that were explicitly provided
        update_data = data.model_dump(exclude_unset=True)
        
        # Call parent update method with the filtered data
        return await super().update(
            update_data, item_id=item_id, auto_commit=auto_commit, **kwargs
        )
