import io
import json
import os
import re
from typing import Annotated
from venv import logger

from cryptography.fernet import Fernet
from litestar import Controller, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel
from pypdf import PdfReader

from core.config.app import alchemy
from core.domain.api_servers.schemas import ApiServerCreate
from core.domain.api_servers.service import ApiServersService
from services.agents.models import AgentActionType
from services.api_servers.types import (
    ApiServerConfigWithSecrets,
    ApiTool,
    ApiToolMockResponse,
    ApiToolParameters,
)
from stores import get_db_client


class ParsePdfResponse(BaseModel):
    pages: list[str]


# duplicate of UserUtilsController TODO - rework
class UtilsController(Controller):
    path = "/utils"
    tags = ["utils"]

    @post("/parse-pdf", status_code=HTTP_200_OK)
    async def parse_pdf(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> ParsePdfResponse:
        """Parse PDF file and extract text from its pages"""
        if not data:
            raise ClientException("No file provided")

        content = await data.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() for page in pdf_reader.pages]

        return ParsePdfResponse(pages=pages)

    @post("/generate_secret_encryption_key", status_code=HTTP_200_OK)
    async def generate_secret_encryption_key(
        self,
    ) -> dict:
        """
        Generates A URL-safe base64-encoded 32-byte key
        which can be used as a vaulue of the environment variable `SECRET_ENCRYPTION_KEY`
        to encrypt secrets stored in the database.
        """

        secret_encryption_key = Fernet.generate_key().decode()

        return {"key": secret_encryption_key}

    @post("/migrate_api_tools_and_providers_to_api_servers", status_code=HTTP_200_OK)
    async def migrate_api_tools_and_providers_to_api_servers(
        self,
    ) -> dict:
        """
        Temporary. TODO - delete.
        Creates API servers with tools from deprecated API tools and providers stored in env variables.
        Also updates Agent actions with provider names.
        """
        verify_ssl = os.environ.get("TEMP_ASSISTANT_SKIP_SSL_VERIFICATION") != "true"
        MOCK_PROVIDER_NAME = "MOCK"

        tools_with_provider_missing = []

        client = get_db_client()
        cursor = client.get_collection("api_tools").find({})

        api_servers_by_system_name: dict[str, ApiServerConfigWithSecrets] = {
            MOCK_PROVIDER_NAME: ApiServerConfigWithSecrets(
                system_name=MOCK_PROVIDER_NAME,
                url="",
                name=MOCK_PROVIDER_NAME,
                tools=[],
            )
        }

        api_tool_providers: dict[str, str] = {}

        ENV_VAR_PREFIX = "API_PROVIDER_"

        for env_key, provider_config_value in os.environ.items():
            if env_key.startswith(ENV_VAR_PREFIX):
                provider_name = env_key[len(ENV_VAR_PREFIX) :]

                try:
                    provider_config = json.loads(provider_config_value)

                    security_scheme = provider_config.get("security_schema")
                    security_values = None
                    secrets = None

                    if security_scheme:
                        security_type = security_scheme.get("type")
                        auth_params = provider_config.get("auth_params", {})

                        if security_type == "oauth2":
                            security_values = {
                                "client_id": auth_params.get("client_id", ""),
                                "client_secret": "{CLIENT_SECRET}",
                            }
                            secrets = {
                                "CLIENT_SECRET": auth_params.get("client_secret", "")
                            }

                        elif (
                            security_type == "http"
                            and security_scheme.get("scheme") == "basic"
                        ):
                            security_values = {
                                "username": auth_params.get("username", ""),
                                "password": "{PASSWORD}",
                            }
                            secrets = {"PASSWORD": auth_params.get("password", "")}

                        elif (
                            security_type == "apiKey"
                            and security_scheme.get("in") == "header"
                        ):
                            security_values = {"api_key": "{API_KEY}"}
                            if auth_params.get("api_key"):
                                security_values = {"api_key": "{API_KEY}"}
                                secrets = {"API_KEY": auth_params.get("api_key", "")}
                            elif auth_params.get("api_key_variable"):
                                security_values = {
                                    "api_key_variable": auth_params.get(
                                        "api_key_variable"
                                    )
                                }

                    api_servers_by_system_name[provider_name] = (
                        ApiServerConfigWithSecrets(
                            system_name=provider_name,
                            url=provider_config.get("server_url", ""),
                            name=provider_name,
                            security_scheme=security_scheme,
                            security_values=security_values,
                            secrets=secrets,
                            verify_ssl=verify_ssl,
                            tools=[],
                        )
                    )

                    logger.info(
                        f"Loaded API Tool provider config for system name {env_key}",
                    )
                except Exception:
                    logger.error(
                        f"Failed to load API Tool provider config for system name {env_key}",
                    )

        async for document in cursor:
            api_tool = document  # Now a dict

            # Get active variant value from variants
            variants = api_tool.get("variants", [])
            active_variant_key = api_tool.get("active_variant")
            active_variant = next(
                (
                    variant
                    for variant in variants
                    if variant.get("variant") == active_variant_key
                ),
                {},
            )

            active_variant_value = active_variant.get("value", {})

            assert active_variant_value, (
                f"Active variant not found in API tool {api_tool.get('system_name', '')}"
            )

            active_variant_parameters = active_variant_value.get("parameters")
            assert active_variant_parameters, (
                f"Active variant parameters not found in API tool {api_tool.get('system_name', '')}"
            )

            provider_name = api_tool.get("api_provider")

            if provider_name == MOCK_PROVIDER_NAME:
                api_tool_new = ApiTool(
                    system_name=re.sub(
                        r"[^a-zA-Z0-9_]", "", api_tool.get("system_name", "")
                    ),
                    name=api_tool.get("name"),
                    method=api_tool.get("method"),
                    path=api_tool.get("path"),
                    description=api_tool.get("description"),
                    parameters=ApiToolParameters(
                        input=active_variant_parameters.get("input", {}),
                        output=active_variant_parameters.get("output", {}),
                    ),
                    original_operation_definition=api_tool.get(
                        "original_operation_definition"
                    ),
                    mock_response=ApiToolMockResponse(
                        content=api_tool.get("mock", {}).get("content")
                    )
                    if api_tool.get("mock")
                    else None,
                    mock_response_enabled=True,
                )

                api_tool_providers[api_tool.get("system_name")] = provider_name
                api_servers_by_system_name[provider_name].tools.append(api_tool_new)  # type: ignore
                continue
            else:
                if provider_name not in api_servers_by_system_name:
                    logger.warning(
                        f"Provider config for {provider_name} is not defined in environment variables. Skipping."
                    )
                    api_tool_new = ApiTool(
                        system_name=re.sub(
                            r"[^a-zA-Z0-9_]", "", api_tool.get("system_name", "")
                        ),
                        name=api_tool.get("name"),
                        method=api_tool.get("method"),
                        path=api_tool.get("path"),
                        description=f"[Migrated from non-existent provider {provider_name}] {api_tool.get('description')}",
                        parameters=ApiToolParameters(
                            input=active_variant_parameters.get("input", {}),
                            output=active_variant_parameters.get("output", {}),
                        ),
                        original_operation_definition=api_tool.get(
                            "original_operation_definition"
                        ),
                        mock_response=ApiToolMockResponse(
                            content=api_tool.get("mock", {}).get("content", "")
                        )
                        if api_tool.get("mock")
                        else None,
                        mock_response_enabled=True,
                    )

                    tools_with_provider_missing.append(api_tool.get("system_name"))
                    api_tool_providers[api_tool_new.system_name] = MOCK_PROVIDER_NAME
                    api_servers_by_system_name[MOCK_PROVIDER_NAME].tools.append(
                        api_tool_new
                    )  # type: ignore

                else:
                    api_tool_new = ApiTool(
                        system_name=re.sub(
                            r"[^a-zA-Z0-9_]", "", api_tool.get("system_name", "")
                        ),
                        name=api_tool.get("name"),
                        method=api_tool.get("method"),
                        path=api_tool.get("path"),
                        description=api_tool.get("description"),
                        parameters=ApiToolParameters(
                            input=active_variant_parameters.get("input", {}),
                            output=active_variant_parameters.get("output", {}),
                        ),
                        original_operation_definition=api_tool.get(
                            "original_operation_definition"
                        ),
                    )

                    api_tool_providers[api_tool_new.system_name] = provider_name
                    api_servers_by_system_name[provider_name].tools.append(api_tool_new)  # type: ignore

        created_api_servers = []

        async with alchemy.get_session() as session:
            api_servers_service = ApiServersService(session=session)

            for api_server in api_servers_by_system_name.values():
                # Convert to domain schema format
                api_server_create = ApiServerCreate(
                    name=api_server.name,
                    system_name=api_server.system_name,
                    url=api_server.url,
                    security_scheme=api_server.security_scheme,
                    security_values=api_server.security_values,
                    verify_ssl=api_server.verify_ssl,
                    tools=api_server.tools,  # type: ignore - will be converted in domain
                    secrets_encrypted=api_server.secrets,  # type: ignore - secrets as dict
                )

                created_obj = await api_servers_service.create(
                    api_server_create, auto_commit=True
                )
                created_api_servers.append(
                    {
                        "system_name": api_server.system_name,
                        "inserted_id": str(created_obj.id),
                    }
                )

        agents_colection = client.get_collection("agents")
        agents_cursor = agents_colection.find({})

        updated_agents = []

        async for agent in agents_cursor:
            update_agent = False
            updated_actions = []
            for variant in agent.get("variants", []):
                topics = variant.get("value", {}).get("topics", [])

                for topic in topics:
                    for action in topic.get("actions", []):
                        tool_system_name = re.sub(
                            r"[^a-zA-Z0-9_]", "", action.get("tool_system_name")
                        )

                        if (
                            action.get("type") == AgentActionType.API
                            and tool_system_name in api_tool_providers
                        ):
                            action["tool_system_name"] = tool_system_name
                            action["tool_provider"] = api_tool_providers[
                                tool_system_name
                            ]
                            update_agent = True
                            updated_actions.append(action["system_name"])

            if update_agent:
                logger.info(
                    f"Updating agent {agent.get('name')} with new tool provider names"
                )
                await agents_colection.update_one(
                    {"_id": agent.get("_id")},
                    {"$set": {"variants": agent["variants"]}},
                )

                updated_agents.append(
                    {
                        "system_name": agent.get("system_name"),
                        "updated_actions": updated_actions,
                    }
                )

        return {
            "created_api_servers": created_api_servers,
            "tools_with_provider_missing": tools_with_provider_missing,
            "updated_agents": updated_agents,
        }
