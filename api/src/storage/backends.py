"""Storage backend registration — hybrid loading from DB providers + env fallback."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from advanced_alchemy.types.file_object import storages
from advanced_alchemy.types.file_object.backends.obstore import ObstoreBackend

from .config import StorageConfig
from .resolver import StorageResolver

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from core.db.models.provider import Provider

log = logging.getLogger(__name__)


async def setup_storage(
    cfg: StorageConfig | None = None,
    db_session: AsyncSession | None = None,
) -> StorageResolver | None:
    """Register storage backends and return a StorageResolver.

    Order:
    1. Always register LocalStore ("default") from env.
    2. Load providers with ``category="storage"`` from DB (Phase 8+).
    3. For backends not registered from DB — fall back to env vars.
    4. Build StorageResolver from providers (or return None for env fallback).
    """
    cfg = cfg or StorageConfig()
    providers: list[Provider] = []

    # 1. Local — always present
    os.makedirs(cfg.local_root, exist_ok=True)
    storages.register_backend(
        ObstoreBackend(key="default", fs=f"file://{cfg.local_root}")
    )
    log.info("Storage backend 'default' registered (local: %s)", cfg.local_root)

    # 2. Load providers from DB
    if db_session:
        try:
            from core.domain.providers.service import ProvidersService

            svc = ProvidersService(session=db_session)
            db_providers = await svc.list(category="storage")
            for p in db_providers:
                key = (p.connection_config or {}).get("backend_key", p.system_name)
                try:
                    _register_from_provider(key, p)
                    providers.append(p)
                    log.info(
                        "Storage backend '%s' registered from provider '%s'",
                        key,
                        p.system_name,
                    )
                except Exception:
                    log.exception(
                        "Failed to register storage backend '%s' from provider '%s'",
                        key,
                        p.system_name,
                    )
        except Exception:
            log.exception("Failed to load storage providers from DB")

    # 3. Env fallback for backends not registered from DB
    if (
        not storages.is_registered("azure")
        and cfg.azure_account
        and cfg.azure_container
    ):
        _register_azure_from_env(cfg)
        log.info("Storage backend 'azure' registered from env (fallback)")

    if not storages.is_registered("s3") and cfg.aws_access_key_id and cfg.s3_bucket:
        _register_s3_from_env(cfg)
        log.info("Storage backend 's3' registered from env (fallback)")

    if not storages.is_registered("gcs") and cfg.gcs_bucket:
        _register_gcs_from_env(cfg)
        log.info("Storage backend 'gcs' registered from env (fallback)")

    # 4. Build resolver
    return StorageResolver(providers) if providers else None


# ---------------------------------------------------------------------------
# Provider-based registration
# ---------------------------------------------------------------------------


def _register_from_provider(key: str, provider: Provider) -> None:
    cfg: dict[str, Any] = provider.connection_config or {}
    secrets: dict[str, Any] = provider.secrets_encrypted or {}

    if provider.type == "azure":
        from obstore.store import AzureStore

        azure_cfg: dict[str, str] = {
            "account_name": secrets.get("account_name", ""),
            "account_key": secrets.get("account_key", ""),
        }
        if provider.endpoint:
            azure_cfg["endpoint"] = provider.endpoint
        storages.register_backend(
            ObstoreBackend(
                key=key,
                fs=AzureStore(container_name=cfg["container_name"], config=azure_cfg),
            )
        )
    elif provider.type == "s3":
        from obstore.store import S3Store

        s3_cfg: dict[str, str] = {
            "access_key_id": secrets.get("access_key_id", ""),
            "secret_access_key": secrets.get("secret_access_key", ""),
            "region": cfg.get("region", "us-east-1"),
        }
        if provider.endpoint:
            s3_cfg["endpoint"] = provider.endpoint
        storages.register_backend(
            ObstoreBackend(key=key, fs=S3Store(bucket=cfg["bucket"], config=s3_cfg))
        )
    elif provider.type == "gcs":
        from obstore.store import GCSStore

        gcs_cfg: dict[str, str] = {}
        if secrets.get("service_account_key"):
            gcs_cfg["service_account_key"] = secrets["service_account_key"]
        storages.register_backend(
            ObstoreBackend(key=key, fs=GCSStore(bucket=cfg["bucket"], config=gcs_cfg))
        )
    elif provider.type == "local":
        root = provider.endpoint or "/var/magnet/storage"
        os.makedirs(root, exist_ok=True)
        storages.register_backend(ObstoreBackend(key=key, fs=f"file://{root}"))


# ---------------------------------------------------------------------------
# Env-based registration (fallback)
# ---------------------------------------------------------------------------


def _register_azure_from_env(cfg: StorageConfig) -> None:
    from obstore.store import AzureStore

    azure_cfg: dict[str, str] = {
        "account_name": cfg.azure_account,
        "account_key": cfg.azure_key,
    }
    if cfg.azure_endpoint:
        azure_cfg["endpoint"] = cfg.azure_endpoint
    storages.register_backend(
        ObstoreBackend(
            key="azure",
            fs=AzureStore(container_name=cfg.azure_container, config=azure_cfg),
        )
    )


def _register_s3_from_env(cfg: StorageConfig) -> None:
    from obstore.store import S3Store

    s3_cfg: dict[str, str] = {
        "access_key_id": cfg.aws_access_key_id,
        "secret_access_key": cfg.aws_secret_access_key,
        "region": cfg.aws_region,
    }
    if cfg.s3_endpoint_url:
        s3_cfg["endpoint"] = cfg.s3_endpoint_url
    storages.register_backend(
        ObstoreBackend(key="s3", fs=S3Store(bucket=cfg.s3_bucket, config=s3_cfg))
    )


def _register_gcs_from_env(cfg: StorageConfig) -> None:
    from obstore.store import GCSStore

    gcs_cfg: dict[str, str] = {}
    if cfg.gcs_credentials_json:
        gcs_cfg["service_account_key"] = cfg.gcs_credentials_json
    storages.register_backend(
        ObstoreBackend(key="gcs", fs=GCSStore(bucket=cfg.gcs_bucket, config=gcs_cfg))
    )
