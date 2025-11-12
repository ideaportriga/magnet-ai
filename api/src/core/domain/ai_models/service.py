from __future__ import annotations

from logging import getLogger
from typing import Any

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.ai_model import AIModel

from .schemas import AIModelUpdate

logger = getLogger(__name__)


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

    async def set_default(self, type_value: str, system_name: str) -> None:
        """
        Set a model as default for its type.
        
        Args:
            type_value: The type of the model (e.g., 'prompts', 'embeddings')
            system_name: The system name of the model to set as default
            
        Raises:
            LookupError: If the model with the given type and system_name is not found
        """
        try:
            # First, set all models of this type to not default
            models_of_type = await self.list(type=type_value)
            for model in models_of_type:
                if model.is_default:
                    # Create an AIModelUpdate object with only the fields we want to update
                    update_data = AIModelUpdate(is_default=False)
                    await self.update(
                        update_data, item_id=model.id, auto_commit=False
                    )

            # Then, find the target model and set it as default
            target_model = await self.get_one_or_none(
                type=type_value, system_name=system_name
            )

            if not target_model:
                raise LookupError(
                    f"Model with type '{type_value}' and system_name '{system_name}' not found"
                )

            await self.update(
                AIModelUpdate(is_default=True), item_id=target_model.id, auto_commit=True
            )

        except Exception as err:
            logger.warning(
                "Failed to set default model for type '%s' and system_name '%s': %s",
                type_value,
                system_name,
                err,
            )
            raise
