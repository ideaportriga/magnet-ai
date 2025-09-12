from litestar import Controller, get

from config.api_tool_providers import (
    API_TOOL_PROVIDER_CONFIG_MAPPING,
    PROVIDER_CONFIG_MOCK,
)

RESULT = {
    "system_names": list(API_TOOL_PROVIDER_CONFIG_MAPPING.keys())
    + [PROVIDER_CONFIG_MOCK],
}


class ApiToolProvidersController(Controller):
    path = "/api_tool_providers"
    tags = ["api_tool_providers"]

    @get("")
    async def get_providers(self) -> dict:
        return RESULT
