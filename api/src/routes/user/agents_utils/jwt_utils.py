import base64
import json
from typing import Any, Iterable, Mapping
from litestar.exceptions import ValidationException


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def read_jwt_payload_noverify(token: str) -> Mapping[str, Any]:
    try:
        header, payload, *_ = token.split(".")
    except ValueError as exc:
        raise ValidationException("Invalid JWT format") from exc

    if not payload:
        raise ValidationException("Invalid JWT format")

    try:
        payload_bytes = _b64url_decode(payload)
        return json.loads(payload_bytes.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValidationException("Unable to decode JWT payload") from exc


def pick_audience(payload: Mapping[str, Any]) -> str | None:
    aud = payload.get("aud")
    if isinstance(aud, str) and aud:
        return aud

    if isinstance(aud, Iterable):
        for candidate in aud:
            if isinstance(candidate, str) and candidate:
                return candidate

    app_id = payload.get("appid")
    if isinstance(app_id, str) and app_id:
        return app_id

    return None
