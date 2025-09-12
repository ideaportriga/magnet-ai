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
