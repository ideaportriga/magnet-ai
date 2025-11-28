from __future__ import annotations

import os
import httpx
from typing import List
from ..base import BaseDiarization
from ...storage.postgres_storage import PgDataStorage
from ...models import DiarizationCfg, DiarizationSegment

MODELS_URL = os.getenv("MODELS_SVC_URL", "")


class PyAnnoteHttpDiarizer(BaseDiarization):
    def __init__(self, storage: PgDataStorage, cfg: DiarizationCfg):
        super().__init__(cfg)
        self._storage = storage
        self._timeout = (cfg.internal_cfg or {}).get(
            "http_timeout", 10800
        )  # 3 hours in seconds

    async def diarize(self, file_id: str) -> List[DiarizationSegment]:
        # ── 1) Pull the file and its metadata  ──────────────────────────────
        raw_bytes: bytes = await self._storage.load_audio(file_id)
        meta = await self._storage.get_meta(file_id)  # <- FileData instance

        filename = meta.filename_with_ext or f"{file_id}"
        mime = meta.content_type or "application/octet-stream"

        # ── 2) Call the models service  ─────────────────────────────────────
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{MODELS_URL}/diarize",
                files={"file": (filename, raw_bytes, mime)},
            )
            resp.raise_for_status()
            data = resp.json()

        # ── 3) Build typed segments  ───────────────────────────────────────
        segments = [
            DiarizationSegment(
                start=float(seg["start"]),
                end=float(seg["end"]),
                speaker=str(seg["speaker"]),
            )
            for seg in data
        ]
        segments.sort(key=lambda s: s.start)
        return segments
