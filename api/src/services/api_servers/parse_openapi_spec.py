import asyncio
import json
import re
from http import HTTPMethod

import aiohttp
import jsonref

from .types import ApiTool, ApiToolParameters, ParsedOpenApiSpec


async def resolve_openapi_spec_refs(openapi_spec_raw: dict) -> dict:
    async def async_loader(uri, **kwargs):
        async with aiohttp.ClientSession() as session:
            async with session.get(uri) as resp:
                return await resp.text()

    loop = asyncio.get_event_loop()
    api_spec = await loop.run_in_executor(
        None,
        lambda: json.loads(
            json.dumps(
                jsonref.loads(
                    json.dumps(openapi_spec_raw),
                    loader=async_loader,
                ),
                default=dict,
            ),
        ),
    )
    return api_spec


def generate_name_from_path_and_method(path: str, method: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9/]", "", path)
    name = name.replace("/", "_")
    name = f"{method}_{name}".upper()

    return name


def convert_openapi_to_api_tools(openapi_spec) -> list[ApiTool]:
    api_tools = []

    for path, methods in openapi_spec["paths"].items():
        for method, operation_definition in methods.items():
            api_tool = convert_openapi_operation_to_api_tools(
                path=path, method=method, operation_definition=operation_definition
            )
            api_tools.append(api_tool)

    return api_tools


def convert_openapi_operation_to_api_tools(
    path: str, method: str, operation_definition: dict
) -> ApiTool:
    schema_operation_id = operation_definition.get("operationId")
    schema_description = operation_definition.get("description")
    schema_summary = operation_definition.get("summary")

    system_name = schema_operation_id or generate_name_from_path_and_method(
        path=path, method=method
    )
    name = schema_summary or system_name
    description = schema_description or ""

    input_schema = convert_openapi_operation_to_json_schema(operation_definition)

    parameters = ApiToolParameters(
        input=input_schema,
        output={},
    )

    api_tool = ApiTool(
        system_name=system_name,
        name=name,
        description=description,
        path=path,
        method=HTTPMethod(method.upper()),
        original_operation_definition=operation_definition,
        parameters=parameters,
    )

    return api_tool


def convert_openapi_operation_to_json_schema(operation_definition: dict) -> dict:
    properties_schema = {}
    required_properties = []

    req_body = (
        operation_definition.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema")
    )

    if req_body:
        properties_schema["requestBody"] = req_body
        required_properties.append("requestBody")

    path_params = {}
    query_params = {}

    for param in operation_definition.get("parameters", []):
        param_name = param["name"]
        param_in = param["in"]

        if param_in == "path":
            path_params[param_name] = param
        elif param_in == "query":
            query_params[param_name] = param

    if path_params:
        path_params_schema = convert_operation_parameters_to_json_schema(path_params)
        properties_schema["pathParams"] = path_params_schema

        if path_params_schema.get("required"):
            required_properties.append("pathParams")

    if query_params:
        query_params_schema = convert_operation_parameters_to_json_schema(query_params)
        properties_schema["queryParams"] = query_params_schema

        if query_params_schema.get("required"):
            required_properties.append("queryParams")

    input_parameters = {
        "type": "object",
        "properties": properties_schema,
        "required": required_properties,
    }

    return input_parameters


def convert_operation_parameters_to_json_schema(parameters: dict) -> dict:
    parameters_schema = {}
    parameters_required = []

    for name, details in parameters.items():
        param_schema = details.get("schema", {})
        param_description = details.get("description", "")

        parameters_schema[name] = {
            **param_schema,
            "description": param_description,
        }

        parameters_required.append(name)

    required = [
        name for name, details in parameters.items() if details.get("required", False)
    ]
    schema = {
        "type": "object",
        "properties": parameters_schema,
        "required": required,
    }

    return schema


async def parse_openapi_spec(openapi_spec_raw: dict) -> ParsedOpenApiSpec:
    openapi_spec = await resolve_openapi_spec_refs(openapi_spec_raw)
    tools = convert_openapi_to_api_tools(openapi_spec)
    name = openapi_spec.get("info", {}).get("title", "")
    servers = openapi_spec.get("servers", [])
    security_schemes = openapi_spec.get("components", {}).get("securitySchemes", {})

    parsed_spec = ParsedOpenApiSpec(
        name=name,
        tools=tools,
        servers=servers,
        security_schemes=security_schemes,
    )

    return parsed_spec
