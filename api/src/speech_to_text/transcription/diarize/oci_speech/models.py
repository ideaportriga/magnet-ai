from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..base import BaseDiarization
from ...storage.postgres_storage import PgDataStorage
from ...models import DiarizationCfg
from ...transcribe.oci_whisper.models import drain_oci_cached_payload


@dataclass
class SpeakerSeg:
    start: float
    end: float
    speaker: str


class OciSpeechDiarizer(BaseDiarization):
    def __init__(self, storage: PgDataStorage, cfg: DiarizationCfg):
        super().__init__(storage)

    async def diarize(self, file_id: str) -> List[SpeakerSeg]:
        """
        Retrieves parsed word-level segments from the transcriber's cache
        and merges them into continuous, formatted speaker segments.
        """
        parsed_result = drain_oci_cached_payload(file_id) or {}
        word_level_segments = parsed_result.get("segments", [])

        if not word_level_segments:
            return []

        segs: List[SpeakerSeg] = []

        speaker_label = f"speaker_{word_level_segments[0]['speaker']}"
        current_seg = SpeakerSeg(
            start=word_level_segments[0]["start"],
            end=word_level_segments[0]["end"],
            speaker=speaker_label,
        )

        for word in word_level_segments[1:]:
            current_speaker_str = f"speaker_{word['speaker']}"

            if (
                current_speaker_str == current_seg.speaker
                and (word["start"] - current_seg.end) < 0.8
            ):
                current_seg.end = word["end"]
            else:
                segs.append(current_seg)
                current_seg = SpeakerSeg(
                    start=word["start"], end=word["end"], speaker=current_speaker_str
                )

        segs.append(current_seg)
        return segs
