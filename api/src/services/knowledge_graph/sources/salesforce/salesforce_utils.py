from __future__ import annotations

import asyncio
import re
import logging
from typing import Any

from litestar.exceptions import ClientException
from simple_salesforce import Salesforce

from services.knowledge_sources.factory import get_provider_config

from .salesforce_models import (
    SalesforceRuntimeConfig,
)

logger = logging.getLogger(__name__)

# Regex for valid Salesforce Knowledge Article View object API names (e.g. ServiceArticle__kav)
_OBJECT_API_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)*__kav$")

# Regex to extract field names from a Python format-string template (e.g. {Question__c})
_TEMPLATE_FIELD_RE = re.compile(r"\{([^}]+)\}")


async def resolve_salesforce_credentials(cfg: dict[str, Any]) -> dict[str, str]:
    """Resolve Salesforce credentials from the referenced KS provider record.

    Looks up the provider by ``provider_system_name`` stored in the source config,
    decrypts its secrets, and returns a dict that may contain any of:
    ``username``, ``password``, ``security_token``, ``client_id``, ``client_secret``, ``domain``.

    Which keys are populated depends on the auth flow configured in the provider:

    * Username / password flow  → ``username`` + ``password`` (+ optional ``security_token``)
    * Client credentials flow   → ``client_id`` + ``client_secret``

    In both cases ``domain`` defaults to ``"login"`` (production); use ``"test"`` for sandbox.
    """
    provider_system_name = str(cfg.get("provider_system_name") or "").strip()
    if not provider_system_name:
        raise ClientException(
            "Salesforce source requires a provider_system_name in source config. "
            "Create a Knowledge Source Provider with Salesforce credentials and reference it here."
        )

    try:
        provider_config = await get_provider_config(provider_system_name)
    except ValueError as exc:
        raise ClientException(
            f"Salesforce provider '{provider_system_name}' not found: {exc}"
        ) from exc

    return {
        "username": str(provider_config.get("username") or "").strip(),
        "password": str(provider_config.get("password") or "").strip(),
        "security_token": str(provider_config.get("security_token") or "").strip(),
        "client_id": str(provider_config.get("client_id") or "").strip(),
        "client_secret": str(provider_config.get("client_secret") or "").strip(),
        "domain": str(provider_config.get("domain") or "login").strip() or "login",
    }


def extract_template_fields(template: str) -> list[str]:
    """Return field names referenced in a Python format-string template."""
    return _TEMPLATE_FIELD_RE.findall(template)


def validate_salesforce_runtime_config(cfg: SalesforceRuntimeConfig) -> None:
    """Raise ClientException if the resolved configuration is not usable."""
    if not cfg.object_api_name or not str(cfg.object_api_name).strip():
        raise ClientException(
            "Salesforce object_api_name is required in source config."
        )

    if not _OBJECT_API_NAME_RE.match(cfg.object_api_name):
        raise ClientException(
            f"Invalid Salesforce object_api_name '{cfg.object_api_name}'. "
            "Must match pattern *__kav (e.g. ServiceArticle__kav)."
        )

    if not cfg.content_template or not str(cfg.content_template).strip():
        raise ClientException(
            "Salesforce content_template is required in source config."
        )

    if not extract_template_fields(cfg.content_template):
        raise ClientException(
            "Salesforce content_template must reference at least one field using {FieldName} syntax."
        )

    if cfg.uses_client_credentials:
        # Both client_id and client_secret are present (guaranteed by the property check above)
        pass
    else:
        if not cfg.username:
            raise ClientException(
                f"Salesforce credentials missing from provider '{cfg.provider_system_name}'. "
                "Configure either username + password, or client_id + client_secret in the provider secrets."
            )
        if not cfg.password:
            raise ClientException(
                f"Salesforce password is missing from provider '{cfg.provider_system_name}'. "
                "Check the provider's secrets configuration."
            )


async def create_salesforce_connection(cfg: SalesforceRuntimeConfig) -> Salesforce:
    """Create and return an authenticated Salesforce client (async-safe via thread offload).

    Chooses the auth flow based on the credentials present in the runtime config:

    * Client credentials (OAuth 2.0) — when ``client_id`` and ``client_secret`` are set.
    * Username / password — otherwise.
    """
    if cfg.uses_client_credentials:
        return await asyncio.to_thread(
            Salesforce,
            consumer_key=cfg.client_id,
            consumer_secret=cfg.client_secret,
            domain=cfg.domain,
        )

    return await asyncio.to_thread(
        Salesforce,
        username=cfg.username,
        password=cfg.password,
        security_token=cfg.security_token,
        domain=cfg.domain,
    )


def build_soql_query(cfg: SalesforceRuntimeConfig) -> str:
    """Build the SOQL SELECT query from the runtime config.

    Always selects Id, CreatedDate, LastModifiedDate, Title plus any fields referenced
    in the content template or configured metadata_fields. Returns all published articles
    (``PublishStatus = 'Online'``).
    """
    content_fields = set(extract_template_fields(cfg.content_template))
    metadata_fields = set(cfg.metadata_fields) if cfg.metadata_fields else set()

    base_fields = {"Id", "CreatedDate", "LastModifiedDate", "Title"}
    extra_fields = (content_fields | metadata_fields) - base_fields

    select_clause = "Id, CreatedDate, LastModifiedDate, Title"
    if extra_fields:
        select_clause += ", " + ", ".join(sorted(extra_fields))

    return f"SELECT {select_clause} FROM {cfg.object_api_name} WHERE PublishStatus = 'Online'"
