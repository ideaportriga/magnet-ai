import httpx

from core.config.base import get_knowledge_source_settings
from data_sources.oracle_knowledge.types import OracleKnowledgeConfig


def get_oracle_knowledge_config(oracle_knowledge_url) -> OracleKnowledgeConfig:
    try:
        settings = get_knowledge_source_settings()
        username = settings.ORACLE_KNOWLEDGE_USERNAME
        password = settings.ORACLE_KNOWLEDGE_PASSWORD
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
