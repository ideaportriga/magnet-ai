# api/src/knowledge/magnet_sync.py
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple, Union

from models import DocumentData
from stores import get_db_store

log = logging.getLogger(__name__)
store = get_db_store()


# ────────── helpers (copied / minimal) ──────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _round1(val, default=None):
    if val is None:
        return default
    try:
        d = Decimal(str(val))
        return float(d.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    except Exception:
        return default


def _format_time(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    try:
        total_seconds = int(seconds)
        h, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        if isinstance(seconds, float) and not seconds.is_integer():
            return f"{h:02}:{m:02}:{s:02}.{int((seconds % 1) * 10)}"
        return f"{h:02}:{m:02}:{s:02}"
    except Exception:
        return None


def _normalise_segment(seg: Any) -> Dict[str, Any]:
    if isinstance(seg, dict):
        sd = dict(seg)
        if "content" not in sd:
            sd["content"] = sd.get("text", "")
        sd.setdefault("speaker", "unknown")
        sd.setdefault("start_ms", 0)
        sd.setdefault("end_ms", 0)
        return sd
    if isinstance(seg, str):
        return {
            "text": seg,
            "content": seg,
            "speaker": "unknown",
            "start_ms": 0,
            "end_ms": 0,
        }
    if hasattr(seg, "dict") and callable(seg.dict):
        sd = seg.dict()
        if "content" not in sd:
            sd["content"] = sd.get("text", "")
        return sd
    if hasattr(seg, "__dict__"):
        sd = dict(vars(seg))
        if "content" not in sd:
            sd["content"] = sd.get("text", "")
        return sd
    raise TypeError(f"Unsupported segment type: {type(seg)}")


def _segments_to_docs(
    segs: List[Dict[str, Any]],
    *,
    recording_id: str,
    project_id: str,
    file_name: str,
) -> List[DocumentData]:
    total = max(1, len(segs))
    docs: List[DocumentData] = []
    for idx, seg in enumerate(segs):
        n = idx + 1
        raw_start = seg.get("start") or seg.get("start_sec") or seg.get("startSec")
        raw_end = seg.get("end") or seg.get("end_sec") or seg.get("endSec")
        start_sec = _round1(raw_start, default=0.0)
        end_sec = _round1(raw_end, default=None)
        start_time = _format_time(start_sec)
        end_time = _format_time(end_sec)

        title = f"{file_name} ({start_time})" if start_time is not None else file_name
        content = seg.get("text") or seg.get("content", "")

        docs.append(
            DocumentData(
                content=content,
                metadata={
                    "title": title,
                    "type": "segment",
                    "createdTime": seg.get("createdTime") or _now_iso(),
                    "modifiedTime": seg.get("modifiedTime") or _now_iso(),
                    "recordingId": recording_id,
                    "projectId": project_id,
                    "segmentIndex": idx,
                    "speaker": seg.get("speaker", "unknown"),
                    "startSec": start_sec,
                    "endSec": end_sec,
                    "startTime": start_time,
                    "endTime": end_time,
                    "source": None,  # keep or fill if you have a UI URL
                    "chunkTitle": f"{title} ({n}/{total})",
                    "chunkNumber": n,
                    "chunksTotal": total,
                    "source_id": recording_id,
                },
            )
        )
    return docs


# ────────── public API (same names/signatures as before) ──────────


async def sync_recording(
    *,
    collection_id: str | list[str],
    recording_id: str,
    project_id: str,
    file_name: str,
    merged_segments: List[Any],
    chunk_tokens: int = 500,  # kept for compatibility; not used here
) -> Tuple[int, List[str]]:
    seg_dicts = [_normalise_segment(s) for s in merged_segments]
    docs = _segments_to_docs(
        seg_dicts, recording_id=recording_id, project_id=project_id, file_name=file_name
    )

    collections = (
        [collection_id] if isinstance(collection_id, str) else (collection_id or [])
    )
    if not collections or not docs:
        return 0, []

    created_ids: List[str] = []
    for cid in collections:
        ids = await store.create_documents(docs, cid)
        created_ids.extend(ids)
    log.info("Pushed %d chunks to %s", len(created_ids), collections)
    return len(created_ids), created_ids


async def delete_recording_chunks(
    collection_id: Union[str, List[str]], chunk_ids: List[str]
) -> int:
    if not chunk_ids:
        return 0
    collections = (
        [collection_id] if isinstance(collection_id, str) else (collection_id or [])
    )
    deleted = 0
    for cid in collections:
        for doc_id in chunk_ids:
            try:
                await store.delete_document(document_id=doc_id, collection_id=cid)
                deleted += 1
            except Exception as e:
                log.debug("delete_document failed for %s in %s: %s", doc_id, cid, e)
    return deleted


def _normalize_enhanced(enhanced: Any) -> List[str] | None:
    if isinstance(enhanced, list):
        if all(isinstance(x, str) for x in enhanced):
            return list(enhanced)
        if all(isinstance(x, dict) for x in enhanced):
            return [(d.get("text") or d.get("content") or "") for d in enhanced]
    if isinstance(enhanced, dict):
        if isinstance(enhanced.get("segments"), list):
            return _normalize_enhanced(enhanced["segments"])
        items: List[tuple[int, str]] = []
        for k, v in enhanced.items():
            try:
                i = int(k)
            except (TypeError, ValueError):
                continue
            if isinstance(v, dict):
                txt = v.get("text") or v.get("content") or ""
            else:
                txt = v if isinstance(v, str) else ""
            items.append((i, txt))
        if items:
            return [t for _, t in sorted(items, key=lambda x: x[0])]
    if isinstance(enhanced, str):
        lines = [ln.strip() for ln in enhanced.splitlines() if ln.strip()]
        if len(lines) > 1:
            return lines
        import re

        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", enhanced) if p.strip()]
        return parts if parts else [enhanced.strip()] if enhanced.strip() else []
    return None


async def update_chunks_simple(
    collection_id: str | list[str],
    *,
    recording: dict,
    enhanced: Any,
    allow_partial: bool = True,
) -> tuple[int, list[str]]:
    segs = (recording.get("transcription", {}) or {}).get("segments", []) or []
    seg_count = len(segs)
    if not seg_count:
        return 0, []

    chunk_ids: list[str | None] = [s.get("chunk_id") for s in segs]
    if not any(chunk_ids):
        return 0, []

    texts = _normalize_enhanced(enhanced)
    if texts is None:
        return 0, []

    if allow_partial:
        texts = texts[: min(len(texts), seg_count)]
        if not texts:
            return 0, []
    else:
        if len(texts) != seg_count:
            return 0, []

    # produce updated docs
    new_segs: list[dict] = []
    for i in range(len(texts)):
        base = segs[i] or {}
        sd = _normalise_segment(base)
        sd["content"] = texts[i] or sd.get("content") or sd.get("text") or ""
        new_segs.append(sd)

    file_name = recording.get("source_file") or recording.get("title") or "recording"
    recording_id = str(recording.get("_id"))
    project_id = str(recording.get("project_id"))

    docs = _segments_to_docs(
        new_segs, recording_id=recording_id, project_id=project_id, file_name=file_name
    )

    collections = (
        [collection_id] if isinstance(collection_id, str) else (collection_id or [])
    )
    if not collections:
        return 0, []

    updated: list[str] = []
    to_update = min(len(docs), len(chunk_ids))
    for i in range(to_update):
        doc_id = chunk_ids[i]
        if not doc_id:
            continue
        for cid in collections:
            try:
                await store.update_document(
                    document_id=doc_id, data=docs[i], collection_id=cid
                )
                updated.append(doc_id)
            except Exception as e:
                log.debug("update_document failed for %s in %s: %s", doc_id, cid, e)
    return len(updated), updated
