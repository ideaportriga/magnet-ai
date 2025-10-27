from atlassian import Confluence

from data_sources.common.utils import get_required_env_var
from data_sources.confluence.types import ConfluenceConfig


def get_confluence_config() -> ConfluenceConfig:
    try:
        confluence_config = ConfluenceConfig(
            username=get_required_env_var("CONFLUENCE_USERNAME"),
            token=get_required_env_var("CONFLUENCE_TOKEN"),
        )
        return confluence_config
    except Exception as err:
        raise ValueError("Confluence connection is misconfigured") from err


def create_confluence_instance(url: str):
    config = get_confluence_config()

    return Confluence(url=url, username=config.username, password=config.token)


def create_confluence_instance_with_config(
    url: str,
    username: str | None = None,
    token: str | None = None,
) -> Confluence:
    """Create Confluence instance with explicit configuration.
    
    This function allows passing credentials directly instead of reading from environment.
    Useful when credentials come from provider configuration in database.
    
    Args:
        url: Confluence instance URL
        username: Confluence username
        token: Confluence API token
        
    Returns:
        Confluence instance
    """
    # If no credentials provided, fall back to environment
    if not username or not token:
        return create_confluence_instance(url)
    
    return Confluence(url=url, username=username, password=token)
