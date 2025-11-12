import logging

from openai_model.utils import get_model_by_system_name
from services.ai_services.factory import get_ai_provider


async def get_provider_by_model(system_name_for_model: str):
    try:
        provider_system_name = None
        if system_name_for_model:
            model_config = await get_model_by_system_name(system_name_for_model)
            if model_config:
                provider_system_name_from_config = model_config.get("provider_system_name")
                if isinstance(provider_system_name_from_config, str):
                    provider_system_name = provider_system_name_from_config

        if not provider_system_name:
            raise ValueError(
                f"Model '{system_name_for_model}' does not have a provider_system_name configured"
            )

        provider = await get_ai_provider(provider_system_name)
        return provider

    except Exception as e:
        logging.exception(
            f"Error retrieving provider for model {system_name_for_model}: {e}",
        )
        raise
