import httpx

from core.config._utils import get_env
from data_sources.oracle_knowledge.types import OracleKnowledgeConfig


def get_oracle_knowledge_config(oracle_knowledge_url) -> OracleKnowledgeConfig:
    try:
        username = get_env("ORACLE_KNOWLEDGE_USERNAME", "")()
        password = get_env("ORACLE_KNOWLEDGE_PASSWORD", "")()
        auth = httpx.BasicAuth(username, password)

        config = OracleKnowledgeConfig(
            auth=auth,
            url=oracle_knowledge_url,
        )
        return config
    except Exception as err:
        raise ValueError("Oracle Knowledge connection is misconfigured") from err


def create_oracle_knowledge_client(oracle_knowledge_url):
    oracle_knowledge_config = get_oracle_knowledge_config(oracle_knowledge_url)

    return oracle_knowledge_config


def create_oracle_knowledge_client_with_config(
    oracle_knowledge_url: str,
    username: str | None = None,
    password: str | None = None,
) -> OracleKnowledgeConfig:
    """Create Oracle Knowledge client with explicit configuration.
    
    This function allows passing credentials directly instead of reading from environment.
    Useful when credentials come from provider configuration in database.
    
    Args:
        oracle_knowledge_url: Oracle Knowledge base URL
        username: Oracle Knowledge username
        password: Oracle Knowledge password
        
    Returns:
        OracleKnowledgeConfig instance
    """
    # If no credentials provided, fall back to environment
    if not username or not password:
        return create_oracle_knowledge_client(oracle_knowledge_url)
    
    auth = httpx.BasicAuth(username, password)
    
    return OracleKnowledgeConfig(
        auth=auth,
        url=oracle_knowledge_url,
    )
