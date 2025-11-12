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


def get_rightnow_basic_auth_with_config(
    username: str | None = None,
    password: str | None = None,
) -> httpx.BasicAuth:
    """Create RightNow BasicAuth with explicit credentials.
    
    This function allows passing credentials directly instead of reading from environment.
    Useful when credentials come from provider configuration in database.
    
    Args:
        username: RightNow username
        password: RightNow password
        
    Returns:
        httpx.BasicAuth instance
    """
    # If no credentials provided, fall back to environment
    if not username or not password:
        return get_rightnow_basic_auth()
    
    return httpx.BasicAuth(username, password)
