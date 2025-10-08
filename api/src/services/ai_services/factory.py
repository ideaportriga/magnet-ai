from config.providers import Config
from services.ai_services.interface import AIProviderInterface
from services.ai_services.providers.azure_ai import AzureAIProvider
from services.ai_services.providers.azure_open_ai import AzureProvider
from services.ai_services.providers.groq import GroqProvider
from services.ai_services.providers.tmp_local import TmpLocalProvider
from services.ai_services.providers.oci import OCIProvider
from services.ai_services.providers.oci_llama import OCILlamaProvider
from services.ai_services.providers.openai import OpenAIProvider

_provider_cache = {}


def get_ai_provider(provider_name: str) -> AIProviderInterface:
    if provider_name in _provider_cache:
        return _provider_cache[provider_name]

    provider_config = Config.AI_PROVIDERS.get(provider_name)
    if not provider_config:
        raise ValueError(f"Provider '{provider_name}' is not supported.")

    provider_type = provider_config.get("type")
    provider_classes = {
        "openai": OpenAIProvider,
        "azure_ai": AzureAIProvider,
        "azure_open_ai": AzureProvider,
        "oci": OCIProvider,
        "oci_llama": OCILlamaProvider,
        "groq": GroqProvider,
        "datacom": TmpLocalProvider,
    }

    provider_class = provider_classes.get(str(provider_type))
    if not provider_class:
        raise ValueError(f"Provider type '{provider_type}' is not implemented.")

    provider_instance = provider_class(provider_config)
    _provider_cache[provider_name] = provider_instance
    return provider_instance
