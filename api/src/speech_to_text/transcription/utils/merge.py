from __future__ import annotations
from typing import Dict, List, Union
import re

SpeakerType = Union[Dict, object]

_END_SENT_RE = re.compile(r"[.!?][\"')\]]*\s*$")  # text *ends* with a sentence
_SENT_RE = re.compile(r"[.!?][\"')\]]*\s+")  # sentence boundaries


def _ends_sentence(txt: str) -> bool:
    return bool(_END_SENT_RE.search(txt.strip()))


def _sent_count(txt: str) -> int:
    return len(_SENT_RE.findall(txt)) or 1


def _merge_adjacent_segments(
    segs: List[Dict],
    gap_threshold: float = 0.8,
    max_sentences: int = 3,
) -> List[Dict]:
    if not segs:
        return []

    merged: List[Dict] = []
    cur = segs[0].copy()

    for nxt in segs[1:]:
        same_spk = nxt["speaker"] == cur["speaker"]
        gap = nxt["start"] - cur["end"]

        close_now = (
            (not same_spk)  # speaker changed
            or (
                _ends_sentence(cur["text"])  # at a clean stop
                and (
                    gap > gap_threshold  # with a real pause
                    or _sent_count(cur["text"]) >= max_sentences  # or too long already
                )
            )
        )

        if close_now:
            merged.append(cur)
            cur = nxt.copy()
        else:
            cur["text"] = f"{cur['text'].rstrip()} {nxt['text'].lstrip()}"
            cur["end"] = nxt["end"]

    merged.append(cur)
    return merged


def merge_words_and_speakers(words: Dict, speakers: List[SpeakerType]) -> Dict:
    def get_attr(seg: SpeakerType, name: str):
        return getattr(seg, name, None) if hasattr(seg, name) else seg.get(name)

    def speaker_for(ts: float, te: float) -> str:
        mid = (ts + te) / 2
        best, best_dist = "unknown", float("inf")
        for seg in speakers:
            start = get_attr(seg, "start")
            end = get_attr(seg, "end")
            spk = str(get_attr(seg, "speaker") or "unknown").strip('"')
            if start is not None and end is not None:
                if start <= mid < end:
                    return spk
                dist = min(abs(mid - start), abs(mid - end))
                if dist < best_dist:
                    best_dist, best = dist, spk
        return best

    labelled = [
        {
            "start": w.get("start"),
            "end": w.get("end"),
            "speaker": speaker_for(w.get("start"), w.get("end")),
            "text": w.get("text", ""),
        }
        for w in words.get("segments", [])
    ]

    merged = _merge_adjacent_segments(labelled, gap_threshold=0.8, max_sentences=3)

    transcript_text = " ".join(seg["text"] for seg in merged)

    return {"text": transcript_text, "segments": merged}
