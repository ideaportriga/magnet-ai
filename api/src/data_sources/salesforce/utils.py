from simple_salesforce import Salesforce

from data_sources.common.utils import get_required_env_var
from data_sources.salesforce.types import SalesforceConfig


def get_salesforce_config() -> SalesforceConfig:
    try:
        salesforce_config = SalesforceConfig(
            username=get_required_env_var("SALESFORCE_USERNAME"),
            password=get_required_env_var("SALESFORCE_PASSWORD"),
            security_token=get_required_env_var("SALESFORCE_TOKEN"),
        )
        return salesforce_config
    except Exception as err:
        raise ValueError("Salesforce connection is misconfigured") from err


def create_salesforce_instance() -> Salesforce:
    config = get_salesforce_config()

    return Salesforce(
        username=config.username,
        password=config.password,
        security_token=config.security_token,
    )
