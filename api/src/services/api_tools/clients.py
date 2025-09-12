import os

import aiohttp
from aiohttp import BasicAuth

env = os.environ
TEMP_ASSISTANT_SKIP_SSL_VERIFICATION = (
    env.get("TEMP_ASSISTANT_SKIP_SSL_VERIFICATION") == "true"
)


async def create_api_client(
    security_schema: dict | None,
    auth_params: dict,
) -> aiohttp.ClientSession:
    if not security_schema:
        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                verify_ssl=not TEMP_ASSISTANT_SKIP_SSL_VERIFICATION
            ),
        )
        return session

    type = security_schema.get("type")

    match type:
        case "oauth2":
            token_url = (
                security_schema.get("flows", {})
                .get("clientCredentials", {})
                .get("tokenUrl")
            )
            client_id = auth_params.get("client_id")
            client_secret = auth_params.get("client_secret")

            # TODO - better validation
            if not client_id or not client_secret:
                raise ValueError("Auth params missing")

            client = await create_oauth2_client(
                client_id=client_id,
                client_secret=client_secret,
                token_url=token_url,
            )

            return client

        case "http":
            scheme = security_schema.get("scheme")

            if scheme == "basic":
                # TODO - validation
                username = auth_params.get("username", "")
                password = auth_params.get("password", "")
                client = await create_basic_auth_client(
                    username=username, password=password
                )

                return client

            raise NotImplementedError
        
        case "apiKey":
            if security_schema.get("in") == "header":
                header_name = security_schema.get("name", "")
                header_value = auth_params.get("api_key", "")
                client = await create_api_key_client(
                    header_name=header_name, header_value=header_value
                )
                
                return client

            raise NotImplementedError
        
        case _:
            raise NotImplementedError

async def create_api_key_client(
        header_name: str, header_value: str
) -> aiohttp.ClientSession:  
    session = aiohttp.ClientSession(
        headers={header_name: header_value},
        connector=aiohttp.TCPConnector(
            verify_ssl=not TEMP_ASSISTANT_SKIP_SSL_VERIFICATION
        ),
    )
    return session    


async def create_basic_auth_client(
    username: str, password: str
) -> aiohttp.ClientSession:
    session = aiohttp.ClientSession(
        auth=BasicAuth(username, password),
        connector=aiohttp.TCPConnector(
            verify_ssl=not TEMP_ASSISTANT_SKIP_SSL_VERIFICATION
        ),
    )
    return session


async def create_oauth2_client(
    client_id: str,
    client_secret: str,
    token_url: str,
) -> aiohttp.ClientSession:
    # https://docs.aiohttp.org/en/stable/client_reference.html#client-session
    connector = aiohttp.TCPConnector(
        verify_ssl=not TEMP_ASSISTANT_SKIP_SSL_VERIFICATION
    )
    async with aiohttp.ClientSession(connector=connector) as temp_session:
        try:
            async with temp_session.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            ) as auth_response:
                auth_response.raise_for_status()
                resp_json = await auth_response.json()
                token = resp_json.get("access_token")
                if not token:
                    raise RuntimeError("No access_token in OAuth2 response")
        except Exception as e:
            raise RuntimeError(f"Failed to obtain OAuth2 token: {e}")

    session = aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {token}"},
        connector=aiohttp.TCPConnector(
            verify_ssl=not TEMP_ASSISTANT_SKIP_SSL_VERIFICATION
        ),
    )
    return session
