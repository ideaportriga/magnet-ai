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
