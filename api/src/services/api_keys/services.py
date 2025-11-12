import hashlib
import secrets
from logging import getLogger

from core.config.app import alchemy
from core.domain.api_keys.schemas import APIKey, APIKeyCreate
from core.domain.api_keys.service import APIKeysService

from .types import (
    ApiKeyConfigEntity,
    ApiKeyConfigPersisted,
    CreateApiKeyData,
    CreateApiKeyResult,
)

logger = getLogger(__name__)


# Cache for API keys
API_KEYS_ENTITIES_CACHE: list[ApiKeyConfigEntity] = []
API_KEYS_PERSISTED_BY_HASH_CACHE: dict[str, ApiKeyConfigPersisted] = {}


async def initialize_api_keys_cache() -> None:
    """Initialize the API keys cache on startup."""
    await refresh_api_keys_caches()


async def retrieve_api_keys() -> list[ApiKeyConfigEntity]:
    """Retrieve all API keys without hash field for security."""
    async with alchemy.get_session() as session:
        service = APIKeysService(session=session)
        api_keys = await service.list()
        entities = []
        for api_key in api_keys:
            api_key_schema = service.to_schema(api_key, schema_type=APIKey)
            # Convert to ApiKeyConfigEntity format (without hash)
            entity_data = api_key_schema.model_dump()

            # Convert UUID to string if present
            if "id" in entity_data and entity_data["id"] is not None:
                entity_data["id"] = str(entity_data["id"])

            entity_data.pop("hash", None)  # Remove hash for security
            entities.append(ApiKeyConfigEntity(**entity_data))
        return entities


def get_api_key_config(api_key: str) -> ApiKeyConfigPersisted:
    """Get API key configuration by hash from cache."""
    api_key_hash = hash_api_key(api_key)
    if api_key_hash not in API_KEYS_PERSISTED_BY_HASH_CACHE:
        raise KeyError("API key not found")
    return API_KEYS_PERSISTED_BY_HASH_CACHE[api_key_hash]


async def refresh_api_keys_caches() -> None:
    """Refresh API keys caches from SQLAlchemy."""
    async with alchemy.get_session() as session:
        service = APIKeysService(session=session)
        api_keys = await service.list()

        entities: list[ApiKeyConfigEntity] = []
        dict_by_hash: dict[str, ApiKeyConfigPersisted] = {}

        for api_key in api_keys:
            api_key_schema = service.to_schema(api_key, schema_type=APIKey)
            api_key_data = api_key_schema.model_dump()

            # Convert UUID to string if present
            if "id" in api_key_data and api_key_data["id"] is not None:
                api_key_data["id"] = str(api_key_data["id"])

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


async def list_api_keys() -> list[ApiKeyConfigEntity]:
    """List all API keys without hash field for security."""
    return API_KEYS_ENTITIES_CACHE


def hash_api_key(api_key: str) -> str:
    """Hash the API key using SHA-256"""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


async def create_api_key(
    data: CreateApiKeyData,
) -> CreateApiKeyResult:
    """Generates a new random API key and creates config record for it"""
    api_key = secrets.token_urlsafe(32)

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
        )

        created_api_key = await service.create(create_data, auto_commit=True)
        await refresh_api_keys_caches()
        return CreateApiKeyResult(id=str(created_api_key.id), api_key=api_key)


async def delete_api_key(id: str) -> None:
    """Deletes API key"""
    async with alchemy.get_session() as session:
        service = APIKeysService(session=session)

        # Try to get the API key first to check if it exists
        api_key_obj = await service.get_one_or_none(id=id)
        if not api_key_obj:
            raise ValueError("API key not found")

        # Delete the API key
        await service.delete(id, auto_commit=True)
        await refresh_api_keys_caches()

    return None
