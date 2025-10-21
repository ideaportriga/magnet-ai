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


def create_salesforce_instance_with_config(
    username: str | None = None,
    password: str | None = None,
    security_token: str | None = None,
) -> Salesforce:
    """Create Salesforce instance with explicit configuration.
    
    This function allows passing credentials directly instead of reading from environment.
    Useful when credentials come from provider configuration in database.
    
    Args:
        username: Salesforce username
        password: Salesforce password
        security_token: Salesforce security token
        
    Returns:
        Salesforce instance
    """
    # If no credentials provided, fall back to environment
    if not username or not password or not security_token:
        return create_salesforce_instance()
    
    return Salesforce(
        username=username,
        password=password,
        security_token=security_token,
    )
