import os
import asyncio
from openai import AzureOpenAI
from ..base import BaseTranscriber
from ...models import TranscriptionCfg
from ...storage.postgres_storage import PgDataStorage
from io import BytesIO
from ...services.ffmpeg import transcode_to_webm_opus, split_to_opus_chunks

MAX_BODY = 50 * 1024 * 1024
MARGIN = 2 * 1024 * 1024

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "")

# TODO - rework env variable handling
# if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY or not AZURE_OPENAI_API_VERSION:
#     raise RuntimeError("AZURE_OPENAI_* env-vars are missing or empty")


class AzureWhisperTranscriber(BaseTranscriber):
    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        super().__init__(storage, cfg)
        self._granularity = (cfg.internal_cfg or {}).get("granularity", "segment")
        self._deployment = cfg.internal_cfg["deployment_id"]
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )

    async def _get_audio(self, file_id: str) -> BytesIO:
        buf: BytesIO = await self._storage.get_file(file_id)
        buf.seek(0)
        meta = await self._storage.get_meta(file_id)
        ext = getattr(meta, "file_ext", None) or ".mp3"
        buf.name = f"{file_id}{ext}"
        return buf

    async def _transcribe(self, file_id: str) -> dict:
        raw = await self._get_audio(file_id)
        raw.seek(0)
        data = raw.read()

        comp = await asyncio.to_thread(transcode_to_webm_opus, data, kbps=24, sr=16000)

        if len(comp.getbuffer()) < (MAX_BODY - MARGIN):
            chunks = [comp]
        else:
            chunks = await asyncio.to_thread(split_to_opus_chunks, data, 8, 24)

        ts_grans = (
            ["segment"] if self._granularity == "segment" else ["word", "segment"]
        )

        all_segments = []
        all_texts = []
        offset = 0.0

        for i, buf in enumerate(chunks):
            if not getattr(buf, "name", None):
                buf.name = f"chunk_{i}.webm"

            backoff = 1.0
            for attempt in range(4):
                try:
                    res = await asyncio.to_thread(
                        self.client.audio.transcriptions.create,
                        file=buf,
                        model=self._deployment,
                        response_format="verbose_json",
                        timestamp_granularities=ts_grans,
                    )
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    await asyncio.sleep(backoff)
                    backoff *= 2

            segs = getattr(res, "segments", None) or []
            if segs:
                for s in segs:
                    all_segments.append(
                        {
                            "start": float(s.start) + offset,
                            "end": float(s.end) + offset,
                            "text": s.text,
                        }
                    )

                offset = all_segments[-1]["end"]
            else:
                txt = getattr(res, "text", "") or ""
                if txt:
                    all_segments.append({"start": offset, "end": offset, "text": txt})

            if getattr(res, "text", ""):
                all_texts.append(res.text)

        return {"text": " ".join(all_texts).strip(), "segments": all_segments}
