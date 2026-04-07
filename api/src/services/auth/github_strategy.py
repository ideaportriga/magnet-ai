"""
GitHub OAuth2 identity strategy.

GitHub is not fully OIDC-compliant (no id_token, no OIDC discovery).
This strategy handles the code exchange + user info fetch manually.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any
from urllib.parse import urlencode

import httpx

from services.auth.types import ExternalIdentity

logger = getLogger(__name__)


class GitHubStrategy:
    """GitHub OAuth2 strategy."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_provider_name(self) -> str:
        return "github"

    async def get_authorization_url(self, state: str, nonce: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email read:user",
            "state": state,
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    async def handle_callback(
        self, request_data: dict[str, Any], expected_nonce: str | None = None
    ) -> ExternalIdentity:
        code = request_data.get("code")
        if not code:
            raise ValueError("Missing authorization code in callback")

        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                headers={"Accept": "application/json"},
                timeout=10,
            )
            resp.raise_for_status()
            token_data = resp.json()

        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("GitHub did not return an access token")

        # Fetch user profile
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}

            user_resp = await client.get(
                "https://api.github.com/user", headers=headers, timeout=10
            )
            user_resp.raise_for_status()
            user_data = user_resp.json()

            email = user_data.get("email")

            # GitHub may not return email in profile; fetch from emails API
            if not email:
                emails_resp = await client.get(
                    "https://api.github.com/user/emails", headers=headers, timeout=10
                )
                emails_resp.raise_for_status()
                for e in emails_resp.json():
                    if e.get("primary") and e.get("verified"):
                        email = e["email"]
                        break

        if not email:
            raise ValueError("GitHub did not return an email address")

        return ExternalIdentity(
            provider="github",
            subject_id=str(user_data["id"]),
            email=email,
            name=user_data.get("name") or user_data.get("login"),
            email_verified=True,  # GitHub verified emails are trustworthy
            raw_claims=user_data,
        )
