from dataclasses import dataclass

import httpx


@dataclass
class OracleKnowledgeConfig:
    url: str
    auth: httpx.BasicAuth
