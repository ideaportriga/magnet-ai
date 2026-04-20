"""Storage configuration — env vars fallback for storage providers."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageConfig(BaseSettings):
    """Env-based storage configuration.

    Serves as fallback — if a Provider with category="storage" exists in the
    database for a given backend, it takes priority over these values.
    """

    # No env_file here: config.config.load_env() is the single loader and
    # has already populated os.environ by the time StorageConfig is
    # instantiated. A relative `env_file=".env"` would be resolved against
    # cwd and reintroduce the api/.env vs root/.env ambiguity.
    model_config = SettingsConfigDict(env_prefix="STORAGE_", extra="ignore")

    # --- Backend connections ---
    local_root: str = "/tmp/magnet_storage"

    azure_account: str = ""
    azure_key: str = ""
    azure_container: str = ""
    azure_endpoint: str = ""

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    s3_endpoint_url: str = ""

    gcs_bucket: str = ""
    gcs_credentials_json: str = ""

    # --- Entity → backend routing ---
    kg_files_backend: str = "default"
    ks_files_backend: str = "default"
    recordings_backend: str = "azure"
    transcriptions_backend: str = "azure"

    # --- File size limits (MB, 0 = unlimited) ---
    max_file_size_mb: int = 50
    kg_max_file_size_mb: int = 0
    ks_max_file_size_mb: int = 0

    # --- Quotas (MB, 0 = unlimited) ---
    kg_source_quota_mb: int = 0
    kg_quota_mb: int = 0
    ks_quota_mb: int = 0

    # --- GC ---
    gc_soft_delete_retention_hours: int = 24
    gc_tmp_retention_hours: int = 6
    gc_interval_hours: int = 1

    # --- TTL ---
    export_ttl_hours: int = 48
    snapshot_ttl_days: int = 90
