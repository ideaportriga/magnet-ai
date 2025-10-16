from microsoft_agents.authentication.msal import MsalAuth
from microsoft_agents.hosting.core.authorization import Connections


class StaticConnections(Connections):
    """Connections implementation that always returns the same token provider."""

    def __init__(self, token_provider: MsalAuth) -> None:
        super().__init__()
        self._token_provider = token_provider

    def get_token_provider(self, *_args, **_kwargs):  # type: ignore[override]
        return self._token_provider

    def get_connection(self, _name: str = ""):
        return self._token_provider

    def get_default_connection(self):
        return self._token_provider

    def get_default_connection_configuration(self):
        return None
