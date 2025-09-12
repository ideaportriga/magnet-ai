import copy

from litestar import Controller, get

from config.providers import Config

_providers_data_cache: dict | None = None


class ModelProvidersController(Controller):
    path = "/model_providers"
    tags = ["model_providers"]

    @get()
    async def get_providers(self) -> list[dict]:
        global _providers_data_cache

        try:
            if _providers_data_cache is None:
                _providers_data_cache = copy.deepcopy(Config.AI_PROVIDERS)

            providers_list: list[dict] = []
            for key, provider in _providers_data_cache.items():
                provider_data = provider.copy()
                provider_data.pop("connection", None)
                provider_data["id"] = key
                providers_list.append(provider_data)

            return providers_list
        except Exception as e:
            raise Exception(f"Failed to fetch providers: {e!s}")


class ModelProvidersControllerDeprecated(ModelProvidersController):
    path = "/providers"
