# transcription/diarize/elevenlabs_diarize/models.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..base import BaseDiarization
from ...storage.postgres_storage import PgDataStorage
from ...models import DiarizationCfg
from ...transcribe.elevenlabs_transcribe.models import (
    _drain_cached,
)  # <- keep this path


# Small POJO the pipeline already expects (attributes, not dict)
@dataclass
class SpeakerSeg:
    start: float
    end: float
    speaker: str


class ElevenLabsDiarization(BaseDiarization):
    def __init__(self, storage: PgDataStorage, cfg: DiarizationCfg):
        super().__init__(storage)
        self.cfg = cfg

    async def diarize(self, file_id: str) -> List[SpeakerSeg]:
        cached = _drain_cached(file_id) or {}
        payload: Dict[str, Any] = cached.get("payload") or {}

        raw_words = payload.get("words") or []

        if not raw_words:
            meta = await self._storage.get_meta(file_id)
            segs = (getattr(meta, "transcription", None) or {}).get("segments", [])
            if segs:
                return [
                    SpeakerSeg(
                        float(segs[0]["start"]), float(segs[-1]["end"]), "unknown"
                    )
                ]
            return []

        try:
            raw_words = sorted(raw_words, key=lambda w: float(w.get("start", 0.0)))
        except Exception:
            pass

        results: List[SpeakerSeg] = []
        glue = 0.40
        cur_spk: Optional[str] = None
        cur_start: Optional[float] = None
        cur_end: Optional[float] = None

        for w in raw_words:
            spk = str(w.get("speaker_id") or "unknown")
            s = float(w.get("start", 0.0))
            e = float(w.get("end", s))

            if cur_spk is None:
                cur_spk, cur_start, cur_end = spk, s, e
                continue

            if spk == cur_spk and s <= (cur_end or s) + glue:
                cur_end = max(cur_end or e, e)
            else:
                results.append(
                    SpeakerSeg(float(cur_start), float(cur_end), str(cur_spk))
                )
                cur_spk, cur_start, cur_end = spk, s, e

        if cur_spk is not None:
            results.append(SpeakerSeg(float(cur_start), float(cur_end), str(cur_spk)))

        return results
