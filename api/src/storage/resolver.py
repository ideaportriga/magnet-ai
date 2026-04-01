"""StorageResolver — maps entity_type → backend_key + limits from Provider records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.db.models.provider import Provider


class StorageResolver:
    """Determines which backend to use for a given entity_type.

    Built from Provider records with ``category="storage"``.  Each provider's
    ``connection_config`` is expected to contain::

        {
            "backend_key": "azure",
            "entity_types": ["recording", "transcription"],
            "limits": {
                "max_file_size_mb": 1024,
                "quotas": {
                    "recording": 10240,
                    "transcription": 512,
                },
            },
        }
    """

    def __init__(self, providers: list[Provider]) -> None:
        self._entity_map: dict[str, str] = {}
        self._limits: dict[str, dict[str, Any]] = {}

        for p in providers:
            cfg = p.connection_config or {}
            key = cfg.get("backend_key", p.system_name)
            for et in cfg.get("entity_types", []):
                self._entity_map[et] = key
            self._limits[key] = cfg.get("limits", {})

    def backend_key_for(self, entity_type: str) -> str:
        return self._entity_map.get(entity_type, "default")

    def max_file_bytes(self, entity_type: str) -> int:
        key = self.backend_key_for(entity_type)
        mb = self._limits.get(key, {}).get("max_file_size_mb", 0)
        return mb * 1024 * 1024 if mb else 0

    def quota_bytes(self, entity_type: str) -> int:
        key = self.backend_key_for(entity_type)
        quotas = self._limits.get(key, {}).get("quotas", {})
        mb = quotas.get(entity_type, 0)
        return mb * 1024 * 1024 if mb else 0
