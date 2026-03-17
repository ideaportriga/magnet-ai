from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..base import BaseDiarization
from ...storage.postgres_storage import PgDataStorage
from ...models import DiarizationCfg
from ...transcribe.azure_speech_transcribe.models import _drain_cached


@dataclass
class SpeakerSeg:
    start: float
    end: float
    speaker: str


def _ms_to_s(x: Any) -> float:
    try:
        return float(x or 0.0) / 1000.0
    except Exception:
        return 0.0


class AzureSpeechDiarization(BaseDiarization):
    def __init__(self, storage: PgDataStorage, cfg: DiarizationCfg):
        super().__init__(storage)
        self.cfg = cfg

    async def diarize(self, file_id: str) -> List[SpeakerSeg]:
        cached = _drain_cached(file_id) or {}
        payload: Dict[str, Any] = cached.get("payload") or {}

        phrases = payload.get("phrases") or []

        if not phrases:
            return []

        try:
            phrases = sorted(
                phrases,
                key=lambda p: _ms_to_s(p.get("offsetMilliseconds")),
            )
        except Exception:
            pass

        results: List[SpeakerSeg] = []

        glue = 0.40
        cur_spk: Optional[str] = None
        cur_start: Optional[float] = None
        cur_end: Optional[float] = None

        for p in phrases:
            speaker_raw = p.get("speaker")
            if speaker_raw is None:
                spk = "unknown"
            else:
                spk = f"speaker_{speaker_raw}"

            s = _ms_to_s(p.get("offsetMilliseconds"))
            e = s + _ms_to_s(p.get("durationMilliseconds"))

            if cur_spk is None:
                cur_spk, cur_start, cur_end = spk, s, e
                continue

            if spk == cur_spk and s <= (cur_end or s) + glue:
                cur_end = max(cur_end or e, e)
            else:
                results.append(
                    SpeakerSeg(
                        float(cur_start),
                        float(cur_end),
                        str(cur_spk),
                    )
                )
                cur_spk, cur_start, cur_end = spk, s, e

        if cur_spk is not None:
            results.append(
                SpeakerSeg(
                    float(cur_start),
                    float(cur_end),
                    str(cur_spk),
                )
            )

        return results
