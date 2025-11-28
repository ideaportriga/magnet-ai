from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(slots=True)
class DiarizationCfg:
    model: str = "mock"
    speakers: Optional[int] = None
    internal_cfg: Optional[Dict] = None


class BaseDiarization(ABC):
    def __init__(self, cfg: DiarizationCfg):
        self._cfg = cfg

    @abstractmethod
    async def diarize(self, file_id: str) -> List[Dict]:
        """
        Return a list of segments:
            [{"start": 0.0, "end": 1.3, "speaker": "SPEAKER_00"}, …]
        """
