from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..base import BaseDiarization
from ...storage.postgres_storage import PgDataStorage
from ...models import DiarizationCfg
from ...transcribe.mistral_transcribe.models import _drain_cached


@dataclass
class SpeakerSeg:
    start: float
    end: float
    speaker: str


def _to_dict(obj: Any):
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, (list, tuple)):
        return [_to_dict(x) for x in obj]
    return obj


class MistralVoxtralDiarization(BaseDiarization):
    def __init__(self, storage: PgDataStorage, cfg: DiarizationCfg):
        super().__init__(storage)
        self.cfg = cfg

    async def diarize(self, file_id: str) -> List[SpeakerSeg]:
        cached = _drain_cached(file_id) or {}
        payload: Dict[str, Any] = cached.get("payload") or {}

        segs = _to_dict(payload.get("segments") or []) or []
        if not segs:
            meta = await self._storage.get_meta(file_id)
            tx = getattr(meta, "transcription", None) or {}
            fallback = tx.get("segments", [])
            if fallback:
                return [
                    SpeakerSeg(
                        float(fallback[0]["start"]),
                        float(fallback[-1]["end"]),
                        "unknown",
                    )
                ]
            return []

        events: List[Dict[str, Any]] = []
        for seg in segs:
            seg = _to_dict(seg) or {}
            spk = seg.get("speaker") or seg.get("speaker_id") or "unknown"
            s = seg.get("start")
            e = seg.get("end", s)
            if s is None or e is None:
                continue
            events.append({"speaker": str(spk), "start": float(s), "end": float(e)})

        if not events:
            return []

        try:
            events = sorted(events, key=lambda x: float(x.get("start", 0.0)))
        except Exception:
            pass

        spk_map: dict[str, str] = {}
        next_idx = 0

        def norm_speaker(raw: str) -> str:
            nonlocal next_idx
            if raw in {"unknown", "", None}:
                return "unknown"
            raw = str(raw)
            if raw not in spk_map:
                spk_map[raw] = f"speaker_{next_idx}"
                next_idx += 1
            return spk_map[raw]

        results: List[SpeakerSeg] = []
        glue = 0.40

        cur_spk: Optional[str] = None
        cur_start: Optional[float] = None
        cur_end: Optional[float] = None

        for ev in events:
            spk = norm_speaker(ev.get("speaker") or "unknown")
            s = float(ev.get("start", 0.0))
            e = float(ev.get("end", s))

            if cur_spk is None:
                cur_spk, cur_start, cur_end = spk, s, e
                continue

            if spk == cur_spk and s <= (cur_end or s) + glue:
                cur_end = max(cur_end or e, e)
            else:
                results.append(SpeakerSeg(float(cur_start), float(cur_end), cur_spk))
                cur_spk, cur_start, cur_end = spk, s, e

        if cur_spk is not None:
            results.append(SpeakerSeg(float(cur_start), float(cur_end), cur_spk))

        return results
