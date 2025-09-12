import os

env = os.environ

API_KEY_PREFIX = "API_KEY_"

def get_api_key_client_mapping() -> dict[str, str]:
    api_key_client_mapping = {}

    api_key_variables = {
        key: value for key, value in env.items() if key.startswith(API_KEY_PREFIX)
    }

    for api_key_variable, api_keys in api_key_variables.items():
        api_client_code = api_key_variable[len(API_KEY_PREFIX) :]
        api_keys = api_keys.split(",")

        for api_key in api_keys:
            api_key = api_key.strip()

            if not api_key:
                continue

            if api_key in api_key_client_mapping:
                raise ValueError(
                    f"Duplicate API key detected for client code: {api_client_code} and {api_key_client_mapping[api_key]}",
                )

            api_key_client_mapping[api_key] = api_client_code

    return api_key_client_mapping

