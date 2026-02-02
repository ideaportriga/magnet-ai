import aiohttp
from aiohttp import BasicAuth

from services.api_servers.types import ApiServerConfigWithSecrets
from utils.secrets import replace_placeholders_in_dict


async def create_api_client_session(
    api_server: ApiServerConfigWithSecrets,
) -> aiohttp.ClientSession:
    security_scheme = api_server.security_scheme

    if not security_scheme:
        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=api_server.verify_ssl),
        )
        return session

    assert api_server.security_values, "Security values are not provided for API server"

    security_values = replace_placeholders_in_dict(
        api_server.security_values, api_server.secrets or {}
    )

    type = security_scheme.get("type")

    match type:
        case "oauth2":
            flows = security_scheme.get("flows", {})

            # Check for password flow first
            if "password" in flows:
                token_url = flows.get("password", {}).get("tokenUrl")
                username = security_values.get("username")
                password = security_values.get("password")

                # TODO - better validation
                if not username or not password:
                    raise ValueError("Username and password required for password flow")

                client = await create_oauth2_password_client(
                    username=username,
                    password=password,
                    token_url=token_url,
                    custom_headers=api_server.custom_headers,
                )

                return client

            # Fall back to client credentials flow
            elif "clientCredentials" in flows:
                token_url = flows.get("clientCredentials", {}).get("tokenUrl")
                client_id = security_values.get("client_id")
                client_secret = security_values.get("client_secret")

                # TODO - better validation
                if not client_id or not client_secret:
                    raise ValueError("Auth params missing")

                client = await create_oauth2_client(
                    client_id=client_id,
                    client_secret=client_secret,
                    token_url=token_url,
                    custom_headers=api_server.custom_headers,
                )

                return client

            raise ValueError("Unsupported OAuth2 flow")

        case "http":
            scheme = security_scheme.get("scheme")

            if scheme == "basic":
                # TODO - validation
                username = security_values.get("username", "")
                password = security_values.get("password", "")
                client = await create_basic_auth_client(
                    username=username,
                    password=password,
                    custom_headers=api_server.custom_headers,
                )

                return client

            if scheme == "bearer":
                token = security_values.get("token", "")
                session = aiohttp.ClientSession(
                    headers={
                        "Authorization": f"Bearer {token}",
                        **(api_server.custom_headers or {}),
                    },
                    connector=aiohttp.TCPConnector(verify_ssl=api_server.verify_ssl),
                )
                return session

            raise NotImplementedError

        case "apiKey":
            if security_scheme.get("in") == "header":
                header_name = security_scheme.get("name", "")
                header_value = security_values.get("api_key", "")

                client = await create_api_key_client(
                    header_name=header_name,
                    header_value=header_value,
                    custom_headers=api_server.custom_headers,
                )

                return client

            raise NotImplementedError

        case _:
            raise NotImplementedError


async def create_api_key_client(
    header_name: str,
    header_value: str,
    custom_headers: dict[str, str] | None = None,
    verify_ssl: bool = True,
) -> aiohttp.ClientSession:
    session = aiohttp.ClientSession(
        headers={**(custom_headers or {}), header_name: header_value},
        connector=aiohttp.TCPConnector(verify_ssl=verify_ssl),
    )
    return session


async def create_basic_auth_client(
    username: str,
    password: str,
    custom_headers: dict[str, str] | None = None,
    verify_ssl: bool = True,
) -> aiohttp.ClientSession:
    session = aiohttp.ClientSession(
        auth=BasicAuth(username, password),
        headers=custom_headers,
        connector=aiohttp.TCPConnector(verify_ssl=verify_ssl),
    )
    return session


async def create_oauth2_client(
    client_id: str,
    client_secret: str,
    token_url: str,
    custom_headers: dict[str, str] | None = None,
    verify_ssl: bool = True,
) -> aiohttp.ClientSession:
    # https://docs.aiohttp.org/en/stable/client_reference.html#client-session
    connector = aiohttp.TCPConnector(verify_ssl=verify_ssl)
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
        headers={**(custom_headers or {}), "Authorization": f"Bearer {token}"},
        connector=aiohttp.TCPConnector(verify_ssl=verify_ssl),
    )
    return session


async def create_oauth2_password_client(
    username: str,
    password: str,
    token_url: str,
    custom_headers: dict[str, str] | None = None,
    verify_ssl: bool = True,
) -> aiohttp.ClientSession:
    connector = aiohttp.TCPConnector(verify_ssl=verify_ssl)
    async with aiohttp.ClientSession(connector=connector) as temp_session:
        try:
            data = {
                "grant_type": "password",
                "username": username,
                "password": password,
            }

            async with temp_session.post(token_url, data=data) as auth_response:
                auth_response.raise_for_status()
                resp_json = await auth_response.json()
                token = resp_json.get("access_token")
                if not token:
                    raise RuntimeError("No access_token in OAuth2 response")
        except Exception as e:
            raise RuntimeError(f"Failed to obtain OAuth2 token: {e}")

    session = aiohttp.ClientSession(
        headers={**(custom_headers or {}), "Authorization": f"Bearer {token}"},
        connector=aiohttp.TCPConnector(verify_ssl=verify_ssl),
    )
    return session
