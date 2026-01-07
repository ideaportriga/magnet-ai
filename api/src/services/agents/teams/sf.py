import os
from logging import getLogger
from typing import Any
from urllib.parse import quote

import httpx

logger = getLogger(__name__)

ENV_PREFIX = "TEAMS_NOTE_TAKER_SF_"


def _get_env(name: str) -> str:
    return os.getenv(f"{ENV_PREFIX}{name}", "").strip()


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


async def _fetch_access_token(
    *, token_url: str, client_id: str, client_secret: str
) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        response.raise_for_status()
        payload = response.json()

    token = payload.get("access_token")
    if not token:
        raise RuntimeError("No access_token in OAuth2 response.")
    return token


async def account_lookup(account_name: str) -> Any:
    if not account_name:
        raise ValueError("Account name is required.")

    api_url = _get_env("API_URL")
    token_url = _get_env("TOKEN_URL")
    client_id = _get_env("CLIENT_ID")
    client_secret = _get_env("CLIENT_SECRET")

    missing = [
        name
        for name, value in (
            ("TEAMS_NOTE_TAKER_SF_API_URL", api_url),
            ("TEAMS_NOTE_TAKER_SF_TOKEN_URL", token_url),
            ("TEAMS_NOTE_TAKER_SF_CLIENT_ID", client_id),
            ("TEAMS_NOTE_TAKER_SF_CLIENT_SECRET", client_secret),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Salesforce env vars: {', '.join(missing)}")

    base_url = _normalize_base_url(api_url)
    token = await _fetch_access_token(
        token_url=token_url, client_id=client_id, client_secret=client_secret
    )
    url = f"{base_url}/accountLookup/{quote(account_name, safe='')}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            logger.debug("Salesforce account lookup response was not JSON.")
            return response.text


async def post_stt_recording(payload: dict[str, Any]) -> Any:
    api_url = _get_env("API_URL")
    token_url = _get_env("TOKEN_URL")
    client_id = _get_env("CLIENT_ID")
    client_secret = _get_env("CLIENT_SECRET")

    missing = [
        name
        for name, value in (
            ("TEAMS_NOTE_TAKER_SF_API_URL", api_url),
            ("TEAMS_NOTE_TAKER_SF_TOKEN_URL", token_url),
            ("TEAMS_NOTE_TAKER_SF_CLIENT_ID", client_id),
            ("TEAMS_NOTE_TAKER_SF_CLIENT_SECRET", client_secret),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Salesforce env vars: {', '.join(missing)}")

    base_url = _normalize_base_url(api_url)
    token = await _fetch_access_token(
        token_url=token_url, client_id=client_id, client_secret=client_secret
    )
    url = f"{base_url}/sttRecording"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            logger.debug("Salesforce sttRecording response was not JSON.")
            return response.text


__all__ = ["account_lookup", "post_stt_recording"]
