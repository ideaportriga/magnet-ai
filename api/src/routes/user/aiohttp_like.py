from typing import Any, Dict
from multidict import CIMultiDict
from yarl import URL


class AiohttpLikeRequest:
    """Duck-typed request compatible with ``CloudAdapter`` expectations."""

    def __init__(
        self,
        *,
        method: str,
        url: str,
        headers: Dict[str, str],
        json_body: Dict[str, Any],
        app_state: Dict[str, Any],
        auth_header: str,
    ) -> None:
        self.method = method.upper()
        self.rel_url = URL(url)
        self.url = self.rel_url
        self.path = self.rel_url.path
        self.host = self.rel_url.host
        self._headers = CIMultiDict(headers or {})
        self._json = json_body
        self.app = app_state or {}
        self.can_read_body = True
        self.content_type = "application/json"
        self._items: dict[str, Any] = {}
        self.auth_header = auth_header

    @property
    def headers(self) -> CIMultiDict:
        return self._headers

    def get(self, key: str, default: Any = None) -> Any:
        return self._items.get(key, default)

    def __setitem__(self, key: str, value: Any) -> None:
        self._items[key] = value

    async def json(self) -> Dict[str, Any]:
        return self._json
