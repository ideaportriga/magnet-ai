import os
from dataclasses import dataclass
from logging import getLogger

import httpx
from aiocache import cached
from jose import jwt

logger = getLogger(__name__)

env = os.environ

AUTH_PROVIDER = env.get("AUTH_PROVIDER", "MICROSOFT")
if AUTH_PROVIDER == "MICROSOFT":
    MICROSOFT_ENTRA_ID_TENANT_ID = env.get("MICROSOFT_ENTRA_ID_TENANT_ID")
    TOKEN_TYPE = "id_token"
    BASE_URL = f"https://login.microsoftonline.com/{MICROSOFT_ENTRA_ID_TENANT_ID}"
    CLIENT_ID = env.get("MICROSOFT_ENTRA_ID_CLIENT_ID")
    CLIENT_SECRET = env.get("MICROSOFT_ENTRA_ID_CLIENT_SECRET")
    REDIRECT_URI = env.get("MICROSOFT_ENTRA_ID_REDIRECT_URI")
    KEYS_URL = f"{BASE_URL}/discovery/v2.0/keys"
    OAUTH2_BASE_URL = f"{BASE_URL}/oauth2/v2.0"
    USER_ID_KEY = "oid"
elif AUTH_PROVIDER == "ORACLE":
    TOKEN_TYPE = "access_token"
    BASE_URL = str(env.get("ORACLE_AUTH_TENANT_URL"))
    BASE_URL = BASE_URL.removesuffix("/")
    CLIENT_ID = env.get("ORACLE_AUTH_CLIENT_ID")
    CLIENT_SECRET = env.get("ORACLE_AUTH_CLIENT_SECRET")
    REDIRECT_URI = env.get("ORACLE_AUTH_REDIRECT_URL")
    KEYS_URL = f"{BASE_URL}/admin/v1/SigningCert/jwk"
    OAUTH2_BASE_URL = f"{BASE_URL}/oauth2/v1"
    USER_ID_KEY = "sub"
else:
    raise ValueError("Incorrect value for AUTH_PROVIDER")

OAUTH2_TOKEN_URL = f"{OAUTH2_BASE_URL}/token"
OAUTH2_AUTHORIZE_URL = f"{OAUTH2_BASE_URL}/authorize"
SIGNING_ALGORITHM = "RS256"
SIGNING_KEYS_CACHE_TTL_HOURS = 24
SIGNING_KEYS_CACHE_TTL_SECONDS = SIGNING_KEYS_CACHE_TTL_HOURS * 60 * 60
RESPONSE_MODE = "form_post"
RESPONSE_TYPE = "code"
AUTH_SCOPE = "openid profile email offline_access"


API_KEY_HEADER_NAME = "x-api-key"
API_USER_ID_HEADER_NAME = "x-user-id"

@dataclass
class Tokens:
    token: str
    refresh_token: str | None = None


class OpenIdKeysFetchError(Exception):
    pass


async def fetch_signing_keys() -> dict:
    logger.info("Fetch signing keys")
    async with httpx.AsyncClient() as client:
        response = await client.get(KEYS_URL, timeout=10)

        if response.status_code != 200:
            raise OpenIdKeysFetchError

        logger.info("Signing keys received")
        return response.json()


@cached(ttl=SIGNING_KEYS_CACHE_TTL_SECONDS)
async def fetch_signing_keys_cached() -> dict:
    return await fetch_signing_keys()


async def decode_token(token: str) -> dict:
    options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_aud": True,
        "verify_at_hash": False,
    }

    audience = CLIENT_ID
    if AUTH_PROVIDER == "ORACLE":
        audience = str(BASE_URL)
        if not audience.endswith(":443"):
            audience += ":443"

    key = await fetch_signing_keys_cached()

    decoded_token = jwt.decode(
        token=token,
        key=key,
        audience=audience,
        algorithms=[SIGNING_ALGORITHM],
        options=options,
    )
    return decoded_token


async def get_tokens(additional_data: dict) -> Tokens:
    data = {
        **additional_data,
    }

    auth = None

    if AUTH_PROVIDER == "MICROSOFT":
        data.update(
            {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
            },
        )
    elif AUTH_PROVIDER == "ORACLE":
        auth = httpx.BasicAuth(str(CLIENT_ID), str(CLIENT_SECRET))

    async with httpx.AsyncClient() as client:
        response = await client.post(
            OAUTH2_TOKEN_URL,
            data=data,
            timeout=10,
            auth=auth or httpx.USE_CLIENT_DEFAULT,
        )
        response.raise_for_status()
        response_data = response.json()

        token = response_data.get(TOKEN_TYPE)
        refresh_token = response_data.get("refresh_token")

        return Tokens(token=token, refresh_token=refresh_token)


async def redeem_code(code: str) -> Tokens:
    aditional_data = {
        "grant_type": "authorization_code",
        "code": code,
    }

    return await get_tokens(aditional_data)
