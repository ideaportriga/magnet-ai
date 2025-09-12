import json
import os
from logging import getLogger

env = os.environ

logger = getLogger(__name__)

ENV_VAR_PREFIX = "API_PROVIDER_"


PROVIDER_CONFIG_MOCK = "MOCK"


def api_tool_provider_config_mapping() -> dict[str, dict]:
    logger.info("Setting up API Tool providers")
    config_mapping = {}

    for env_key, value in env.items():
        if env_key.startswith(ENV_VAR_PREFIX):
            api_provider_code = env_key[len(ENV_VAR_PREFIX) :]

            try:
                value_parsed = json.loads(value)
                config_mapping[api_provider_code] = value_parsed

                logger.info(
                    f"Loaded API Tool provider config for system name {api_provider_code}",
                )
            except Exception:
                logger.error(
                    f"Failed to load API Tool provider config for system name {api_provider_code}",
                )

    return config_mapping


API_TOOL_PROVIDER_CONFIG_MAPPING = api_tool_provider_config_mapping()
