import os


def get_required_env_var(env_var_name: str) -> str:
    value = os.environ.get(env_var_name)

    assert value, f"Missing required env variable {env_var_name}"

    return value
