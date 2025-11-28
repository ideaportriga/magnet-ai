import json
from enum import StrEnum
from typing import Any

import openai
from openai.types.chat.completion_create_params import ResponseFormat


class CollectionSource(StrEnum):
    SHAREPOINT = "Sharepoint"
    SHAREPOINT_PAGES = "Sharepoint Pages"
    CONFLUENCE = "Confluence"
    SALESFORCE = "Salesforce"
    RIGHTNOW = "RightNow"
    ORACLEKNOWLEDGE = "Oracle Knowledge"
    FILE = "File"
    HUBSPOT = "Hubspot"
    FLUID_TOPICS = "Fluid Topics"


def transform_schema(
    input_object: dict[str, Any] | None,
) -> ResponseFormat | openai.NotGiven:
    if input_object is None:
        return openai.NOT_GIVEN

    try:
        if input_object.get("type") == "text":
            return {
                "type": "text",
            }
        elif input_object.get("type") == "json_object":
            return {
                "type": "json_object",
            }
        elif (
            input_object.get("type") == "json_schema" and "json_schema" in input_object
        ):
            schema_str = input_object["json_schema"].get("schema")
            if schema_str:
                return {
                    "type": "json_schema",
                    "json_schema": {
                        "name": input_object["json_schema"].get("name", ""),
                        "schema": json.loads(schema_str),
                    },
                }
    except Exception:
        pass
    return openai.NOT_GIVEN
