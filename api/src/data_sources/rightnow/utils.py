import httpx

from data_sources.common.utils import get_required_env_var
from data_sources.rightnow.types import RightNowConfig


def get_rightnow_config() -> RightNowConfig:
    try:
        config = RightNowConfig(
            username=get_required_env_var("RIGHTNOW_USERNAME"),
            password=get_required_env_var("RIGHTNOW_PASSWORD"),
        )
        return config
    except Exception as err:
        raise ValueError("RightNow connection is misconfigured") from err


def get_rightnow_basic_auth() -> httpx.BasicAuth:
    config = get_rightnow_config()
    return httpx.BasicAuth(config.username, config.password)
