from __future__ import annotations
import json
from pathlib import Path
from typing import List

from ..base import BaseDiarization  # only BaseDiarization here
from ...models import DiarizationSegment  # ← correct location

FIXTURE = Path("data/mock/Short_diarize_mock.json")


class MockDiarization(BaseDiarization):
    async def diarize(self, _file_id: str) -> List[DiarizationSegment]:
        raw = json.loads(FIXTURE.read_text("utf-8"))
        return [
            DiarizationSegment(
                start=float(seg["start"]),
                end=float(seg["end"]),
                speaker=str(seg["speaker"]),
            )
            for seg in raw
        ]
