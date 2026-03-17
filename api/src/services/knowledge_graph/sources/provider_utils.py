"""Utilities for resolving Knowledge Source provider credentials in KG sources.

Convention
----------
A Knowledge Source provider has three relevant fields:

- ``endpoint``         — the base URL of the service (plaintext, always visible)
- ``connection_config``— non-sensitive key/value pairs, visible in the UI.
                         Values may contain ``{secret_key}`` placeholders that are
                         resolved at runtime against ``secrets_encrypted``.
- ``secrets_encrypted``— sensitive values stored encrypted (API keys, passwords, tokens).
                         Decrypted automatically by the ORM column type when read.

``resolve_provider_params`` merges these into a single flat dict so KG sources
can simply do ``params.get("client_id")`` without caring whether the value came
from ``connection_config`` or ``secrets_encrypted``.

Merge order (later keys win):
    secrets  →  resolved_connection_config  →  {"endpoint": endpoint}

This means an explicit value in ``connection_config`` overrides a secret with the
same key, and ``endpoint`` is always present under the ``"endpoint"`` key.

Typical usage
-------------
::

    provider = await get_kg_provider(
        session, source_config, expected_type="salesforce"
    )
    params = resolve_provider_params(provider)

    client_id     = params.get("client_id") or ""      # from connection_config
    client_secret = params.get("client_secret") or ""  # from secrets_encrypted
    endpoint      = params.get("endpoint") or ""       # always present
"""

import logging
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException
from sqlalchemy.ext.asyncio import AsyncSession

from utils.secrets import replace_placeholders_in_dict

logger = logging.getLogger(__name__)


def resolve_provider_params(provider: Any) -> dict[str, Any]:
    """Merge a provider's connection_config (with placeholders resolved) and secrets.

    Returns a flat dict containing all resolved connection params, secrets, and the
    endpoint URL under the ``"endpoint"`` key.

    Non-sensitive identifiers (e.g. ``client_id``, ``username``) should be stored in
    ``connection_config``; sensitive values (e.g. ``client_secret``, ``password``) in
    ``secrets_encrypted``.  Both are accessible via the same returned dict — callers
    don't need to know which storage location was used.

    Args:
        provider: ORM provider object with ``connection_config``, ``secrets_encrypted``,
                  and ``endpoint`` attributes.  ``secrets_encrypted`` is expected to
                  already be decrypted (handled by the ORM column type).

    Returns:
        Flat dict: ``{**secrets, **resolved_connection_config, "endpoint": endpoint}``
    """
    connection_config: dict[str, Any] = provider.connection_config or {}
    secrets: dict[str, Any] = provider.secrets_encrypted or {}

    # Inject secret values into any {placeholder} references in connection_config
    resolved_connection_config = replace_placeholders_in_dict(
        connection_config, secrets
    )

    # Merge: secrets < resolved connection_config < endpoint
    params: dict[str, Any] = {
        **secrets,
        **resolved_connection_config,
        "endpoint": provider.endpoint,
    }

    logger.debug(
        "Resolved provider params",
        extra={
            "provider_id": str(getattr(provider, "id", "")),
            "provider_type": getattr(provider, "type", ""),
            "param_keys": list(params.keys()),
        },
    )

    return params


async def get_kg_provider(
    session: AsyncSession,
    source_config: dict[str, Any],
    *,
    expected_type: str,
    config_key: str = "ks_provider_id",
) -> Any:
    """Look up and validate a Knowledge Source provider referenced by a KG source config.

    Handles the common boilerplate of:
    - reading ``ks_provider_id`` (or a custom ``config_key``) from ``source_config``
    - parsing and validating the UUID
    - fetching the provider from the DB
    - asserting the provider type matches ``expected_type``

    Args:
        session:       Active async DB session.
        source_config: The KG source's ``config`` dict (``source.config``).
        expected_type: Expected provider ``type`` value (case-insensitive comparison).
        config_key:    Key in ``source_config`` that holds the provider UUID string.
                       Defaults to ``"ks_provider_id"``.

    Returns:
        The provider ORM object.

    Raises:
        ClientException: If the provider ID is missing/invalid, the provider is not found,
                         or the provider type does not match.
    """
    from core.domain.providers.service import ProvidersService

    provider_id: str | None = source_config.get(config_key)
    if not provider_id:
        raise ClientException(
            f"Source config is missing '{config_key}'. "
            "Select a Knowledge Source provider."
        )

    try:
        provider_uuid = UUID(provider_id)
    except ValueError as exc:
        raise ClientException(
            f"Source config has invalid '{config_key}': {provider_id!r}"
        ) from exc

    providers_service = ProvidersService(session=session)
    try:
        provider = await providers_service.get(provider_uuid)
    except Exception as exc:
        raise ClientException(
            f"Knowledge Source provider '{provider_id}' not found."
        ) from exc

    if provider.type.lower() != expected_type.lower():
        raise ClientException(
            f"Provider '{provider.name}' has type '{provider.type}', "
            f"expected '{expected_type}'."
        )

    return provider
