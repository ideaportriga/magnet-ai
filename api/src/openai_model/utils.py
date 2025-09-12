from logging import getLogger

from core.config.app import alchemy
from core.domain.ai_models.schemas import AIModel
from core.domain.ai_models.service import AIModelsService

logger = getLogger(__name__)

# Cache for model configurations to reduce database calls
_model_cache = {}


async def get_model_by_system_name(system_name_for_model: str) -> dict:
    # Check cache first to avoid database call
    if system_name_for_model in _model_cache:
        return _model_cache[system_name_for_model]

    async with alchemy.get_session() as session:
        try:
            service = AIModelsService(session=session)
            model = await service.get_one_or_none(system_name=system_name_for_model)

            if not model:
                raise LookupError(
                    f"model template with system_name '{system_name_for_model}' not found",
                )

            model_schema = service.to_schema(model, schema_type=AIModel)
            model_dict = model_schema.model_dump()

            # Cache the result for future use
            _model_cache[system_name_for_model] = model_dict

            return model_dict

        except Exception as err:
            logger.warning("Failed to get model: '%s': %s", system_name_for_model, err)
            raise


def clear_model_cache():
    """Clear the model cache - useful for testing or when models are updated"""
    global _model_cache
    _model_cache.clear()


async def set_default_model(type_value: str, system_name: str):
    try:
        async with alchemy.get_session() as session:
            service = AIModelsService(session=session)

            # First, set all models of this type to not default
            models_of_type = await service.list(type=type_value)
            for model in models_of_type:
                if model.is_default:
                    # Create a dictionary with only the fields we want to update
                    await service.update(
                        {"is_default": False}, item_id=model.id, auto_commit=False
                    )

            # Then, find the target model and set it as default
            target_model = await service.get_one_or_none(
                type=type_value, system_name=system_name
            )

            if not target_model:
                raise LookupError(
                    f"Model with type '{type_value}' and system_name '{system_name}' not found",
                )

            await service.update(
                {"is_default": True}, item_id=target_model.id, auto_commit=True
            )

    except Exception as err:
        logger.warning(
            "Failed to set default model for type '%s' and system_name '%s': %s",
            type_value,
            system_name,
            err,
        )
        raise
