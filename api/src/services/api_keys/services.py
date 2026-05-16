import asyncio
import hashlib
import secrets
from logging import getLogger
from uuid import UUID

from core.config.app import alchemy
from core.db.models.api_key import APIKey as APIKeyModel
from core.domain.api_keys.schemas import APIKey, APIKeyCreate, APIKeyUpdate
from core.domain.api_keys.service import APIKeysService
from guards.permissions import Permission, get_effective_permissions
from litestar.exceptions import PermissionDeniedException, ValidationException
from sqlalchemy import select

from .types import (
    ApiKeyConfigEntity,
    ApiKeyConfigPersisted,
    CreateApiKeyData,
    CreateApiKeyResult,
    UpdateApiKeyData,
)

logger = getLogger(__name__)

_ALL_PERMISSION_CODES = frozenset(p.value for p in Permission)


# Cache for API keys (protected by _cache_lock to prevent partial visibility
# during concurrent refresh operations)
API_KEYS_ENTITIES_CACHE: list[ApiKeyConfigEntity] = []
API_KEYS_PERSISTED_BY_HASH_CACHE: dict[str, ApiKeyConfigPersisted] = {}
_cache_lock = asyncio.Lock()


async def initialize_api_keys_cache() -> None:
    """Initialize the API keys cache on startup."""
    await refresh_api_keys_caches()


async def retrieve_api_keys() -> list[ApiKeyConfigEntity]:
    """Retrieve all API keys without hash field for security."""
    async with alchemy.get_session() as session:
        service = APIKeysService(session=session)
        api_keys = await service.list()
        return [
            ApiKeyConfigEntity(**_api_key_data(service, api_key, include_hash=False))
            for api_key in api_keys
        ]


def get_api_key_config(api_key: str) -> ApiKeyConfigPersisted:
    """Get API key configuration by hash from cache."""
    api_key_hash = hash_api_key(api_key)
    if api_key_hash not in API_KEYS_PERSISTED_BY_HASH_CACHE:
        raise KeyError("API key not found")
    return API_KEYS_PERSISTED_BY_HASH_CACHE[api_key_hash]


async def refresh_api_keys_caches() -> None:
    """Refresh API keys caches from SQLAlchemy."""
    async with _cache_lock:
        async with alchemy.get_session() as session:
            service = APIKeysService(session=session)
            api_keys = await service.list()

            entities: list[ApiKeyConfigEntity] = []
            dict_by_hash: dict[str, ApiKeyConfigPersisted] = {}

            for api_key in api_keys:
                api_key_data = _api_key_data(service, api_key, include_hash=True)

                # Store in hash cache with hash
                api_key_persisted = ApiKeyConfigPersisted(**api_key_data)
                dict_by_hash[api_key_persisted.hash] = api_key_persisted

                # Store in entities cache without hash
                entity_data = api_key_data.copy()
                entity_data.pop("hash", None)
                entities.append(ApiKeyConfigEntity(**entity_data))

            global API_KEYS_ENTITIES_CACHE
            global API_KEYS_PERSISTED_BY_HASH_CACHE

            API_KEYS_ENTITIES_CACHE = entities
            API_KEYS_PERSISTED_BY_HASH_CACHE = dict_by_hash


async def list_api_keys(tenant_id: str) -> list[ApiKeyConfigEntity]:
    """List API keys in one tenant without hash field for security."""
    return [k for k in API_KEYS_ENTITIES_CACHE if str(k.tenant_id) == str(tenant_id)]


def hash_api_key(api_key: str) -> str:
    """Hash the API key using SHA-256"""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


async def create_api_key(
    data: CreateApiKeyData,
    tenant_id: str | None = None,
    auth=None,
) -> CreateApiKeyResult:
    """Generates a new random API key and creates config record for it"""
    api_key = secrets.token_urlsafe(32)
    if tenant_id is None:
        tenant_id = getattr(auth, "tenant_id", None) if auth is not None else None
    if tenant_id is None:
        raise PermissionDeniedException("Tenant context required for API key creation")

    async with alchemy.get_session() as session:
        service = APIKeysService(session=session)

        # Create the API key record
        create_data = APIKeyCreate(
            name=data.name,
            hash=hash_api_key(api_key),
            value_masked=f"...{api_key[-4:]}",
            is_active=True,
            expires_at=None,
            notes=None,
            tenant_id=_as_uuid(tenant_id),
            scopes=_validate_scopes(data.scopes, auth=auth),
        )

        created_api_key = await service.create(create_data, auto_commit=True)
        await refresh_api_keys_caches()
        return CreateApiKeyResult(id=str(created_api_key.id), api_key=api_key)


async def get_api_key(id: str, tenant_id: str) -> ApiKeyConfigEntity:
    """Get a single API key by id."""
    async with alchemy.get_session() as session:
        service = APIKeysService(session=session)
        api_key_obj = await _get_api_key_in_tenant(session, id=id, tenant_id=tenant_id)
        api_key_data = _api_key_data(service, api_key_obj, include_hash=False)
        return ApiKeyConfigEntity(**api_key_data)


async def update_api_key(
    id: str, data: UpdateApiKeyData, tenant_id: str, auth=None
) -> ApiKeyConfigEntity:
    """Update an existing API key."""
    async with alchemy.get_session() as session:
        service = APIKeysService(session=session)

        await _get_api_key_in_tenant(session, id=id, tenant_id=tenant_id)

        payload = data.model_dump(exclude_unset=True)
        if "scopes" in payload:
            payload["scopes"] = _validate_scopes(payload["scopes"], auth=auth)
        update_payload = APIKeyUpdate(**payload)
        await service.update(update_payload, item_id=id, auto_commit=True)
        await refresh_api_keys_caches()

    return await get_api_key(id, tenant_id)


async def delete_api_key(id: str, tenant_id: str) -> None:
    """Deletes API key"""
    async with alchemy.get_session() as session:
        service = APIKeysService(session=session)

        # Try to get the API key first to check if it exists
        await _get_api_key_in_tenant(session, id=id, tenant_id=tenant_id)

        # Delete the API key
        await service.delete(id, auto_commit=True)
        await refresh_api_keys_caches()

    return None


def _api_key_data(
    service: APIKeysService, api_key: APIKeyModel, *, include_hash: bool
) -> dict:
    api_key_schema = service.to_schema(api_key, schema_type=APIKey)
    data = api_key_schema.model_dump()
    if data.get("id") is not None:
        data["id"] = str(data["id"])
    if data.get("tenant_id") is not None:
        data["tenant_id"] = str(data["tenant_id"])
    data["scopes"] = list(data.get("scopes") or [])
    if not include_hash:
        data.pop("hash", None)
    return data


async def _get_api_key_in_tenant(session, *, id: str, tenant_id: str) -> APIKeyModel:
    result = await session.execute(
        select(APIKeyModel).where(
            APIKeyModel.id == _as_uuid(id),
            APIKeyModel.tenant_id == _as_uuid(tenant_id),
        )
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise ValueError("API key not found")
    return api_key


def _validate_scopes(scopes: list[str] | None, *, auth=None) -> list[str]:
    requested = {str(scope) for scope in (scopes or [])}
    unknown = requested - _ALL_PERMISSION_CODES
    if unknown:
        raise ValidationException(
            f"Unknown API key scope(s): {', '.join(sorted(unknown))}"
        )

    if auth is not None:
        effective = get_effective_permissions(auth)
        not_allowed = requested - effective
        if not_allowed:
            raise PermissionDeniedException(
                "Cannot grant API key scopes you don't hold yourself: "
                + ", ".join(sorted(not_allowed))
            )
    return sorted(requested)


def _as_uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))
