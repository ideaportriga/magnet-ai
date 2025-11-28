from __future__ import annotations

import asyncio
import logging
import os
import time
import json
from typing import BinaryIO, Dict, List, Any

from .models import FileData
from .utils import merge_words_and_speakers
from .transcribe.base import BaseTranscriber
from .diarize.base import BaseDiarization
from .storage.postgres_storage import PgDataStorage
from ..knowledge.magnet_sync import sync_recording
from stores import get_db_store

store = get_db_store()

log = logging.getLogger(__name__)

WORDS_TIMEOUT = 21_600
MAGNET_SYNC_TIMEOUT = int(os.getenv("MAGNET_SYNC_TIMEOUT", "300"))


async def _sync_to_magnet(file_data: FileData, segments: List[Any]) -> List[str]:
    if os.getenv("MAGNET_SYNC", "0") != "1":
        log.info("MAGNET_SYNC disabled; skipping Magnet sync")
        return []

    # --- Fetch recording ---
    rec_list = await store.list_documents(
        collection_name="recordings",
        filter={"file_id": file_data.file_id},
        projection=["project_id", "id"],
        limit=1,
    )

    if not rec_list:
        raise RuntimeError("No recording row linked to this file_id")

    rec_doc = rec_list[0]
    recording_id = str(rec_doc["id"])
    raw_pid = rec_doc["project_id"]

    # --- Fetch project ---
    proj_list = await store.list_documents(
        collection_name="projects",
        filter={"id": raw_pid},
        projection=["settings"],
        limit=1,
    )

    project = proj_list[0] if proj_list else None

    if not project:
        log.warning("Project %s not found – skipping Magnet sync", raw_pid)
        return []

    sources = project.get("settings", {}).get("knowledge_source", [])
    if not sources:
        log.warning(
            "Project %s has no knowledge sources – skipping Magnet sync", raw_pid
        )
        return []

    # --- Perform sync ---
    log.info(
        "Magnet sync start: file_id=%s recording_id=%s segments=%d",
        file_data.file_id,
        recording_id,
        len(segments),
    )
    t0 = time.perf_counter()

    try:
        count, created_ids = await sync_recording(
            collection_id=sources,
            recording_id=recording_id,
            project_id=str(raw_pid),
            file_name=file_data.file_name,
            merged_segments=segments,
        )
    except Exception as e:
        log.warning(
            "Magnet sync failed for recording %s: %s. Continuing without chunks.",
            recording_id,
            e,
            exc_info=True,
        )
        return []

    dur = time.perf_counter() - t0
    log.info(
        "Magnet sync done: file_id=%s duration=%.2fs returned=%d expected=%d",
        file_data.file_id,
        dur,
        count,
        len(segments),
    )

    if count != len(segments):
        log.warning("Magnet returned %d ids for %d segments", count, len(segments))

    return [
        str(cid[0]) if isinstance(cid, (list, tuple)) else str(cid)
        for cid in created_ids
    ]


class TranscriptionPipeline:
    def __init__(
        self,
        stt: BaseTranscriber,
        diarizer: BaseDiarization,
        storage: PgDataStorage,
    ):
        self._stt = stt
        self._dr = diarizer
        self._db = storage

    @staticmethod
    def _validate_words(words: Dict[str, Any] | None) -> Dict[str, Any]:
        if not words or "segments" not in words:
            raise RuntimeError("Transcription step returned no data")
        return words

    @staticmethod
    def _validate_speakers(spk: List[Any] | None) -> List[Any]:
        if spk is None:
            raise RuntimeError("Diarization step returned no data")
        return spk

    async def run(self, file_data: FileData, stream: BinaryIO) -> None:
        delete_raw = True

        stt_class = self._stt.__class__.__name__
        dr_class = self._dr.__class__.__name__
        stt_deploy = getattr(self._stt, "_deployment", None)
        diar_locale = getattr(self._dr, "locale", None)

        log.info(
            "PIPELINE start file_id=%s stt=%s deploy=%s diar=%s locale=%s",
            file_data.file_id,
            stt_class,
            stt_deploy,
            dr_class,
            diar_locale,
        )

        t_all0 = time.perf_counter()
        try:
            t0 = time.perf_counter()
            await self._db.save_audio(file_data, stream)
            await self._db.insert_meta(file_data)
            await self._db.update_status(file_data.file_id, "running")
            t1 = time.perf_counter()
            log.info(
                "TIMING save+meta+status file_id=%s duration=%.2fs",
                file_data.file_id,
                t1 - t0,
            )

            log.info(
                "STT start file_id=%s model=%s deploy=%s",
                file_data.file_id,
                stt_class,
                stt_deploy,
            )
            t_stt0 = time.perf_counter()
            raw_words = await asyncio.wait_for(
                self._stt._transcribe(file_data.file_id), timeout=WORDS_TIMEOUT
            )
            t_stt1 = time.perf_counter()
            words = self._validate_words(raw_words)
            log.info(
                "STT done file_id=%s duration=%.2fs", file_data.file_id, t_stt1 - t_stt0
            )

            log.info(
                "DIAR start file_id=%s model=%s locale=%s",
                file_data.file_id,
                dr_class,
                diar_locale,
            )
            t_diar0 = time.perf_counter()
            raw_speakers = await self._dr.diarize(file_data.file_id)
            t_diar1 = time.perf_counter()
            speakers = self._validate_speakers(raw_speakers)
            log.info(
                "DIAR done file_id=%s duration=%.2fs",
                file_data.file_id,
                t_diar1 - t_diar0,
            )

            t_merge0 = time.perf_counter()
            merged = merge_words_and_speakers(words, speakers)
            unique = {s.speaker for s in speakers}
            participants = sorted(
                [{"name": spk, "key": spk} for spk in unique], key=lambda x: x["key"]
            )
            t_merge1 = time.perf_counter()
            log.info(
                "MERGE done file_id=%s duration=%.2fs speakers=%d",
                file_data.file_id,
                t_merge1 - t_merge0,
                len(unique),
            )

            try:
                segs = (
                    merged["segments"] if isinstance(merged, dict) else merged.segments
                )
            except Exception:
                log.error("Unexpected `merged` type: %r", type(merged))
                segs = []
            log.info("SEGMENTS ready file_id=%s count=%d", file_data.file_id, len(segs))

            log.info(
                "MAGNET start file_id=%s timeout=%ss",
                file_data.file_id,
                MAGNET_SYNC_TIMEOUT,
            )
            t_mag0 = time.perf_counter()
            created_ids = await _sync_to_magnet(file_data, segs)
            t_mag1 = time.perf_counter()
            log.info(
                "MAGNET done file_id=%s duration=%.2fs created=%d",
                file_data.file_id,
                t_mag1 - t_mag0,
                len(created_ids),
            )

            if created_ids and len(created_ids) != len(segs):
                log.warning(
                    "Chunk/segment count mismatch: chunks=%d segments=%d",
                    len(created_ids),
                    len(segs),
                )

            for i, cid in enumerate(created_ids):
                try:
                    if isinstance(merged, dict):
                        merged["segments"][i]["chunk_id"] = cid
                    else:
                        merged.segments[i].chunk_id = cid
                except Exception as e:
                    log.warning("Failed to set chunk_id on segment %d: %s", i, e)

            t_db0 = time.perf_counter()
            await self._db.update_transcription(file_data.file_id, merged)
            await self._db.update_status(
                file_data.file_id, "completed", participants=participants
            )
            t_db1 = time.perf_counter()
            log.info(
                "DB update done file_id=%s duration=%.2fs",
                file_data.file_id,
                t_db1 - t_db0,
            )

            t_all1 = time.perf_counter()
            metrics = {
                "file_id": file_data.file_id,
                "stt_class": stt_class,
                "stt_deploy": stt_deploy,
                "diar_class": dr_class,
                "diar_locale": diar_locale,
                "durations": {
                    "save_meta_status_s": round(t1 - t0, 3),
                    "stt_s": round(t_stt1 - t_stt0, 3),
                    "diar_s": round(t_diar1 - t_diar0, 3),
                    "merge_s": round(t_merge1 - t_merge0, 3),
                    "magnet_s": round(t_mag1 - t_mag0, 3),
                    "db_update_s": round(t_db1 - t_db0, 3),
                    "total_s": round(t_all1 - t_all0, 3),
                },
                "segments": len(segs),
                "participants": [p["name"] for p in participants],
            }
            log.info("METRICS %s", json.dumps(metrics, ensure_ascii=False))

        except Exception as exc:
            await self._db.update_error(file_data.file_id, str(exc))
            await self._db.update_status(file_data.file_id, "failed")
            log.exception("pipeline %s crashed", file_data.file_id)
        finally:
            if delete_raw:
                await self._db.delete_audio(file_data.file_id)
            log.info("PIPELINE end file_id=%s", file_data.file_id)


def _log_magnet_task_result(task: asyncio.Task):
    try:
        res = task.result()
        log.info(
            "MAGNET BG finished: created_ids=%d",
            len(res) if isinstance(res, list) else -1,
        )
    except Exception:
        log.exception("MAGNET BG task crashed")
