import httpx

from data_sources.common.utils import get_required_env_var
from data_sources.oracle_knowledge.types import OracleKnowledgeConfig


def get_oracle_knowledge_config(oracle_knowledge_url) -> OracleKnowledgeConfig:
    try:
        username = get_required_env_var("ORACLE_KNOWLEDGE_USERNAME")
        password = get_required_env_var("ORACLE_KNOWLEDGE_PASSWORD")
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
