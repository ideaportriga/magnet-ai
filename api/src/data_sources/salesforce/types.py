from dataclasses import dataclass


@dataclass
class SalesforceConfig:
    username: str
    password: str
    security_token: str
