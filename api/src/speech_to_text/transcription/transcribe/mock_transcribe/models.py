from __future__ import annotations
import asyncio
import json
from pathlib import Path
from typing import Dict

from ..base import BaseTranscriber

FIXTURE = Path("data/mock/Short_transcribe_mock.json")


class MockTranscriber(BaseTranscriber):
    async def _transcribe(self, _file_id: str) -> Dict:
        return json.loads(await asyncio.to_thread(FIXTURE.read_text, "utf-8"))
