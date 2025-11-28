from __future__ import annotations

import os
import httpx
from io import BytesIO

from ..base import BaseTranscriber
from ...storage.postgres_storage import PgDataStorage
from ...models import TranscriptionCfg

MODELS_URL = os.getenv("MODELS_SVC_URL", "")


class WhisperHttpTranscriber(BaseTranscriber):
    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        super().__init__(storage, cfg)
        self._timeout = (cfg.internal_cfg or {}).get(
            "http_timeout", 10800
        )  # 3 hours in seconds

    async def _transcribe(self, file_id: str) -> dict:
        # ── 1) fetch bytes + meta ─────────────────────────────────────────
        buf: BytesIO = await self._storage.get_file(file_id)
        meta = await self._storage.get_meta(file_id)  # FileData

        filename = meta.filename_with_ext or f"{file_id}"
        mime = meta.content_type or "application/octet-stream"

        # ── 2) POST to models-service ─────────────────────────────────────
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{MODELS_URL}/transcribe",
                files={"file": (filename, buf.read(), mime)},
            )

        if resp.status_code != 200:
            raise RuntimeError(
                f"models-service /transcribe returned {resp.status_code}: {resp.text}"
            )

        data: dict = resp.json()
        if "segments" not in data or "text" not in data:
            raise RuntimeError("models-service JSON missing expected keys")

        return data
